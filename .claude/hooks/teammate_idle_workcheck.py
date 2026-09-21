#!/usr/bin/env python3
"""TeammateIdle hook — nudge an idle agent toward claimable work.

When a teammate goes idle, scan the active spec's tasks.md for unclaimed,
unblocked tasks matching that teammate's role. If any exist, remind the agent
to self-claim rather than waiting to be asked.

This hook never blocks — it only informs. Fails open on any unexpected error.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import glob
import re

EVENT = "TeammateIdle"

# - [ ] [role] description ...   (unchecked tasks only)
OPEN_TASK_RE = re.compile(r"^\s*[-*]\s*\[\s*\]\s*\[(?P<role>[a-z]+)\]\s*(?P<rest>.+)$",
                          re.IGNORECASE)


def find_task_files(root):
    """Locate tasks.md under .claude/specs, newest first."""
    pattern = os.path.join(root, ".claude", "specs", "*", "tasks.md")
    files = glob.glob(pattern)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files


def agent_roles(name):
    """Map an agent name to the role tags it can claim."""
    mapping = {
        "backend-go": ["go"],
        "backend-node": ["node"],
        "web-react": ["react"],
        "ios-swift": ["swift"],
        "data-engineer": ["data"],
        "terraform-engineer": ["terraform"],
        "aws-architect": ["aws"],
        "review-agent": ["review"],
        "solution-architect": ["planning"],
        "requirements-analyst": ["planning"],
        "diagram-author": ["planning"],
        "tradeoff-analyst": ["planning"],
        "ux-designer": ["design", "planning"],
    }
    return mapping.get((name or "").strip().lower(), [])


def main():
    try:
        import team_hook_lib as lib
    except Exception:
        sys.exit(0)  # fail open

    try:
        payload = lib.read_payload()
        name = str(lib.dig(payload, "agent_name", "agentName", "name",
                           "subagent_type", "type") or "").strip()
        roles = agent_roles(name)

        root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        task_files = find_task_files(root)

        if not task_files:
            lib.allow(EVENT, "no tasks.md found", agent=name)

        claimable = []
        for path in task_files:
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        match = OPEN_TASK_RE.match(line)
                        if not match:
                            continue
                        role = match.group("role").lower()
                        if roles and role not in roles:
                            continue
                        claimable.append((role, match.group("rest").strip()[:120]))
            except Exception:
                continue
            if claimable:
                break  # only report on the most recent spec with open work

        if not claimable:
            lib.allow(EVENT, "no claimable work", agent=name, roles=",".join(roles))

        listing = "\n".join(
            "  [{}] {}".format(role, rest) for role, rest in claimable[:8]
        )
        more = ""
        if len(claimable) > 8:
            more = "\n  ... and {} more".format(len(claimable) - 8)

        notice = (
            "{} unclaimed task(s) remain that you can pick up:\n{}{}\n\n"
            "Per .claude/rules/agent-team-protocol.md, after finishing a task you "
            "self-claim the next unclaimed, unblocked task for your role rather "
            "than idling. Claim one with TaskUpdate -> in_progress."
        ).format(len(claimable), listing, more)

        sys.stderr.write(notice + "\n")
        lib.log(EVENT, "nudge", agent=name, roles=",".join(roles),
                claimable=len(claimable))
        sys.exit(0)

    except SystemExit:
        raise
    except Exception as exc:  # fail open
        try:
            lib.log(EVENT, "error", reason=repr(exc))
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
