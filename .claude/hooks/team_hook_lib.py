"""Shared helpers for the gsd-team enforcement hooks.

Every hook in this directory MUST fail open: if this library or the hook that
imports it raises, the hook exits 0 and the teammate proceeds. A bug in our
enforcement must never be able to wedge the team.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/logs/team-hooks.jsonl")
VERIFIED_ROOT = os.path.expanduser("~/.claude/logs/verified")

# Role tags recognised by this team. Keep in sync with
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
    r"^\s*\[(?P<role>" + "|".join(ROLE_TAGS) + r")\]\s+"  # role tag
    r"(?P<desc>[^|]+?)\s*\|\s*"                            # description
    r"(?P<files>[^|]+?)\s*\|\s*"                           # file paths
    r"(?P<acceptance>.+?)\.?\s*"                           # acceptance
    r"Run:\s*(?P<command>\S.*)$",                          # run command
    re.IGNORECASE | re.DOTALL,
)


def read_payload():
    """Read the hook JSON from stdin. Returns {} on anything unreadable."""
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


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


def dig(payload, *names, default=""):
    """Fetch the first present key from the payload or its nested containers.

    Hook payload shapes vary across Claude Code versions, so look in the
    top level and in the usual nested spots rather than assuming one shape.
    """
    containers = [payload]
    for key in ("task", "tool_input", "input", "data", "teammate", "agent"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            containers.append(nested)
    for container in containers:
        for name in names:
            value = container.get(name)
            if value not in (None, ""):
                return value
    return default


def task_text(payload):
    """Best-effort extraction of the task's one-line description."""
    value = dig(
        payload,
        "description", "content", "prompt", "text", "task", "title", "subject",
    )
    if isinstance(value, dict):
        value = value.get("description") or value.get("content") or ""
    return str(value or "").strip()


def task_id(payload):
    return str(dig(payload, "task_id", "taskId", "id") or "").strip()


def team_name(payload):
    name = str(
        dig(payload, "team_name", "teamName", "team", "session_id", "sessionId")
        or ""
    ).strip()
    return re.sub(r"[^A-Za-z0-9._-]", "-", name) or "default"


def sentinel_path(team, tid):
    return os.path.join(VERIFIED_ROOT, team, "task-{}.verified".format(tid))


def allow(event, reason="", **fields):
    """Let the action through."""
    log(event, "allow", reason=reason, **fields)
    sys.exit(0)


def deny(event, message, **fields):
    """Block the action and tell the agent why.

    Exit code 2 signals a blocking hook decision; the message on stderr is
    surfaced back to the agent so it can correct course.
    """
    log(event, "deny", reason=message, **fields)
    sys.stderr.write(message + "\n")
    sys.exit(2)
