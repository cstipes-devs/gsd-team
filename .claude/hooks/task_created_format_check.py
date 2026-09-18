#!/usr/bin/env python3
"""TaskCreated hook — enforce the task line format.

Required shape (see .claude/rules/agent-team-protocol.md):

    [role] <verb> <what> | <file paths> | <acceptance>. Run: <command>

Tasks containing [skip-format-check] bypass this check. Fails open on any
unexpected error.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


EVENT = "TaskCreated"

EXPECTED = """Task format rejected by task_created_format_check.

Required shape:
  [role] <verb> <what> | <file paths> | <acceptance>. Run: <command>

Example:
  [go] Implement POST /orders handler | internal/api/orders.go, internal/api/orders_test.go | returns 201 with order id, 409 on duplicate. Run: go test ./internal/api/...

Valid roles: planning, go, node, react, swift, data, terraform, aws, review

Every task needs all four parts: a role tag, explicit file paths, acceptance
criteria, and a real Run: command at the right test tier.

Coordination or research tasks with no verifiable output may include
[skip-format-check] to bypass this check."""


def main():
    try:
        import team_hook_lib as lib
    except Exception:
        sys.exit(0)  # fail open

    try:
        payload = lib.read_payload()
        text = lib.task_text(payload)
        tid = lib.task_id(payload)

        if not text:
            lib.allow(EVENT, "no task text in payload", task_id=tid)

        if lib.SKIP_MARKER in text.lower():
            lib.allow(EVENT, "skip-format-check marker present", task_id=tid)

        match = lib.TASK_RE.match(text)
        if not match:
            lib.deny(EVENT, EXPECTED, task_id=tid, task=text[:300])

        # The Run: command must be more than a placeholder.
        command = match.group("command").strip()
        if len(command) < 3 or command.lower() in ("none", "n/a", "tbd", "todo"):
            lib.deny(
                EVENT,
                "Task rejected: the Run: command is a placeholder ({!r}).\n"
                "Provide a real command that verifies this task at the tier its "
                "acceptance criteria imply. See .claude/rules/testing-standards.md."
                .format(command),
                task_id=tid,
                task=text[:300],
            )

        # File paths must look like paths, not prose.
        files = match.group("files").strip()
        if "/" not in files and "." not in files:
            lib.deny(
                EVENT,
                "Task rejected: the file section ({!r}) does not look like file "
                "paths.\nList the explicit files this task will modify — file "
                "disjointness is what makes parallel execution safe."
                .format(files),
                task_id=tid,
                task=text[:300],
            )

        lib.allow(EVENT, "format ok", task_id=tid, role=match.group("role"))

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
