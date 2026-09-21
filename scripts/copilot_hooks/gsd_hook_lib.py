"""Shared helpers for the gsd-team GitHub Copilot CLI hooks.

Ported from `.claude/hooks/team_hook_lib.py`. The task grammar (TASK_RE,
ROLE_TAGS, SKIP_MARKER) is deliberately identical so a tasks.md written under
one toolchain validates under the other.

IMPORTANT — the fail-open inversion:

Claude Code treats a crashed hook as "allow". Copilot CLI does the opposite:
a preToolUse hook that crashes, times out, or exits non-zero FAILS CLOSED and
denies the tool call. Exit code 2 always denies, even when stdout says allow.

So every code path here must end in an explicit `allow()` — printing `{}` and
exiting 0. A bare `raise` would block the user's file write, which is exactly
the outcome a bug in our enforcement must never cause.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

# Not under ~/.claude or ~/.copilot — one location serves both toolchains.
STATE_ROOT = os.path.expanduser("~/.gsd-team")
LOG_PATH = os.path.join(STATE_ROOT, "logs", "team-hooks.jsonl")
VERIFIED_ROOT = os.path.join(STATE_ROOT, "logs", "verified")

# Keep in sync with .claude/hooks/team_hook_lib.py and
# .claude/rules/agent-team-protocol.md.
ROLE_TAGS = (
    "planning",
    "design",
    "go",
    "node",
    "react",
    "swift",
    "data",
    "terraform",
    "aws",
    "review",
)

SKIP_MARKER = "[skip-format-check]"

# [role] <verb> <what> | <files> | <acceptance>. Run: <command>
TASK_RE = re.compile(
    r"^\s*\[(?P<role>" + "|".join(ROLE_TAGS) + r")\]\s+"
    r"(?P<desc>[^|]+?)\s*\|\s*"
    r"(?P<files>[^|]+?)\s*\|\s*"
    r"(?P<acceptance>.+?)\.?\s*"
    r"Run:\s*(?P<command>\S.*)$",
    re.IGNORECASE | re.DOTALL,
)

# A markdown checkbox line, checked or unchecked.
#
# The body is deliberately NOT required to start with "[" — a line that is
# missing its role tag entirely is the most common malformation, and it must
# be caught by the format rule rather than slipping past as "not a task".
TASK_LINE_RE = re.compile(r"^\s*[-*]\s*\[(?P<mark>[ xX])\]\s*(?P<body>\S.*)$")


def read_payload():
    """Read Copilot's preToolUse JSON from stdin.

    Documented shape: {sessionId, timestamp, cwd, toolName, toolArgs}.
    Returns {} on anything unreadable so callers fall through to allow().
    """
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def tool_name(payload):
    return str(payload.get("toolName") or "")


def tool_args(payload):
    args = payload.get("toolArgs")
    return args if isinstance(args, dict) else {}


def target_path(payload):
    """Best-effort extraction of the file a write tool is targeting.

    Tool argument names are not standardized across Copilot's write tools, so
    check the plausible keys rather than assuming one shape.
    """
    args = tool_args(payload)
    for key in ("path", "file_path", "filePath", "filename", "file", "target"):
        value = args.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def written_content(payload):
    """Best-effort extraction of the content a write tool would write."""
    args = tool_args(payload)
    for key in ("content", "contents", "text", "new_string", "newString", "body"):
        value = args.get(key)
        if isinstance(value, str):
            return value
    return None


def spec_slug(path):
    """Derive the spec directory name from a path to its tasks.md."""
    parts = os.path.normpath(path).split(os.sep)
    if "specs" in parts:
        i = parts.index("specs")
        if i + 1 < len(parts):
            return re.sub(r"[^A-Za-z0-9._-]", "-", parts[i + 1])
    parent = os.path.basename(os.path.dirname(path))
    return re.sub(r"[^A-Za-z0-9._-]", "-", parent) or "default"


def task_id(task_body):
    """Derive a stable id from a task line.

    Copilot supplies no task id, so identity is derived from the line itself:
    the SHA-256 of the normalized `[role] description | files` prefix, which is
    the part that names the work. The acceptance clause, the Run: command, the
    checkbox state and any trailing `> Done.` note are excluded so that marking
    a task complete does not change its id.

    Consequence worth knowing: editing a task's role, description, or file list
    changes its id and orphans any sentinel already written for it. Rewrite the
    sentinel, or re-run verification, after editing those fields.
    """
    body = task_body.strip()
    parts = body.split("|")
    prefix = "|".join(parts[:2]) if len(parts) >= 2 else body
    normalized = re.sub(r"\s+", " ", prefix).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def sentinel_path(slug, tid):
    return os.path.join(VERIFIED_ROOT, slug, "task-{}.verified".format(tid))


def iter_task_lines(content):
    """Yield (line_number, is_checked, body) for every markdown task line."""
    for n, line in enumerate(content.splitlines(), 1):
        m = TASK_LINE_RE.match(line)
        if m:
            yield n, m.group("mark").lower() == "x", m.group("body").strip()


def log(event, decision, **fields):
    """Append one decision to the audit log. Never raises."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "decision": decision,
        }
        record.update(fields)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:
        pass


def allow(event="preToolUse", reason="", **fields):
    """Let the tool call through.

    `{}` on stdout plus exit 0 is Copilot's "no opinion" response. This is the
    only safe terminal state for an unexpected condition, because any other
    exit denies the call.
    """
    if reason:
        log(event, "allow", reason=reason, **fields)
    sys.stdout.write("{}\n")
    sys.exit(0)


def deny(event, reason, **fields):
    """Block the tool call and tell the agent why.

    Both signals are sent: the JSON decision on stdout and exit code 2. Exit 2
    denies unconditionally, so a malformed stdout cannot turn a deny into an
    allow.
    """
    log(event, "deny", reason=reason, **fields)
    sys.stdout.write(json.dumps({
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }) + "\n")
    sys.exit(2)
