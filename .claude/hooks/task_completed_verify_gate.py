#!/usr/bin/env python3
"""TaskCompleted hook — require a verification sentinel.

A task may not be marked complete unless the agent wrote:

    ~/.claude/logs/verified/<team>/task-<task_id>.verified

The sentinel is the agent's attestation that it actually ran the task's Run:
command and the command passed. On success the sentinel is consumed (deleted)
so it cannot be reused for a second task.

Fails open on any unexpected error.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


EVENT = "TaskCompleted"


def message(team, tid, path):
    return """Completion blocked: no verification sentinel for task {tid}.

Before marking a task complete you must actually run its Run: command and
confirm it passed, then write the sentinel:

  mkdir -p ~/.claude/logs/verified/{team}
  echo "<Run command> PASSED" > {path}

The Verification Gate (.claude/rules/agent-team-protocol.md) requires all of:
  1. You executed the Run: command and it passed
  2. The command exercises the correct test tier
  3. Interfaces and output contracts match design.md exactly
  4. You modified only your assigned files (git diff --name-only)
  5. You read real success signals, not just a 200 status

If a required test tier genuinely cannot run in this environment, mark the task
blocked and report it. Do not write a sentinel for a command you did not run.
""".format(tid=tid, team=team, path=path)


def main():
    try:
        import team_hook_lib as lib
    except Exception:
        sys.exit(0)  # fail open

    try:
        payload = lib.read_payload()
        tid = lib.task_id(payload)
        team = lib.team_name(payload)

        if not tid:
            lib.allow(EVENT, "no task id in payload")

        text = lib.task_text(payload)
        if text and lib.SKIP_MARKER in text.lower():
            lib.allow(EVENT, "skip-format-check task, no Run: to verify",
                      task_id=tid)

        path = lib.sentinel_path(team, tid)

        if not os.path.isfile(path):
            lib.deny(EVENT, message(team, tid, path), task_id=tid, team=team,
                     sentinel=path)

        # Consume the sentinel so it cannot attest to a second task.
        contents = ""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                contents = fh.read().strip()[:300]
        except Exception:
            pass

        try:
            os.remove(path)
        except Exception:
            pass

        lib.allow(EVENT, "sentinel present and consumed", task_id=tid,
                  team=team, attestation=contents)

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
