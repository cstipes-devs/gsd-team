#!/usr/bin/env python3
"""preToolUse hook — the gsd-team verification gate for GitHub Copilot CLI.

Claude Code binds this enforcement to TaskCreated and TaskCompleted events.
Copilot has no task lifecycle, so both rules bind instead to the file write
that touches a spec's tasks.md:

  Rule A — task format. Every task line must match the required shape.
  Rule B — verification gate. Flipping a task from [ ] to [x] requires a
           verification sentinel on disk, which is consumed on use.

Anything that is not a write to a tasks.md under a specs/ directory is allowed
without inspection.

Fails OPEN by explicit allow() — see gsd_hook_lib for why that matters here.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EVENT = "preToolUse"

FORMAT_HELP = """Task format rejected by the gsd-team verification gate.

Required shape:
  - [ ] [role] <verb> <what> | <file paths> | <acceptance>. Run: <command>

Example:
  - [ ] [go] Implement POST /orders handler | internal/api/orders.go, internal/api/orders_test.go | returns 201 with order id, 409 on duplicate. Run: go test ./internal/api/...

Valid roles: planning, design, go, node, react, swift, data, terraform, aws, review

Every task needs all four parts: a role tag, explicit file paths, acceptance
criteria, and a real Run: command at the right test tier.

Coordination or research tasks with no verifiable output may include
[skip-format-check] to bypass this check.

Offending line {lineno}:
  {line}"""

GATE_HELP = """Completion blocked: no verification sentinel for this task.

  {desc}

Before marking a task [x] you must actually run its Run: command, confirm it
passed, and write the sentinel:

  mkdir -p {sentinel_dir}
  echo "<Run command> PASSED" > {sentinel}

Derive the task id with:
  python3 scripts/copilot_hooks/task_id.py '<the task line>'

The Verification Gate requires all of:
  1. You executed the Run: command and it passed
  2. The command exercises the correct test tier
  3. Interfaces and output contracts match design.md exactly
  4. You modified only your assigned files (git diff --name-only)
  5. You read real success signals, not just a 200 status

If a required tier genuinely cannot run in this environment, leave the task
unchecked and report it as blocked. Do not write a sentinel for a command you
did not run."""


def is_tasks_file(path):
    if not path:
        return False
    norm = path.replace("\\", "/")
    return norm.endswith("/tasks.md") or norm == "tasks.md"


def main():
    try:
        import gsd_hook_lib as lib
    except Exception:
        # Cannot even load the library: allow, never block on our own bug.
        sys.stdout.write("{}\n")
        sys.exit(0)

    try:
        payload = lib.read_payload()
        path = lib.target_path(payload)

        if not is_tasks_file(path):
            lib.allow(EVENT)

        content = lib.written_content(payload)
        if content is None:
            # A patch-style edit we cannot reconstruct. verify-spec.sh is the
            # backstop for this case.
            lib.allow(EVENT, "tasks.md write with no readable content",
                      path=path)

        slug = lib.spec_slug(path)

        # Prior state, so we only gate transitions rather than re-gating every
        # already-checked task on each write.
        previously_checked = set()
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    for _, checked, body in lib.iter_task_lines(fh.read()):
                        if checked:
                            previously_checked.add(lib.task_id(body))
            except Exception:
                pass

        # Rule A — format.
        for lineno, _checked, body in lib.iter_task_lines(content):
            if lib.SKIP_MARKER in body.lower():
                continue
            if not lib.TASK_RE.match(body):
                lib.deny(
                    EVENT,
                    FORMAT_HELP.format(lineno=lineno, line=body[:200]),
                    path=path, rule="format",
                )

        # Rule B — verification gate on newly-checked tasks.
        newly_checked = []
        for _lineno, checked, body in lib.iter_task_lines(content):
            if not checked:
                continue
            if lib.SKIP_MARKER in body.lower():
                continue
            tid = lib.task_id(body)
            if tid not in previously_checked:
                newly_checked.append((tid, body))

        for tid, body in newly_checked:
            sentinel = lib.sentinel_path(slug, tid)
            if not os.path.isfile(sentinel):
                lib.deny(
                    EVENT,
                    GATE_HELP.format(
                        desc=body.split("|")[0].strip()[:120],
                        sentinel_dir=os.path.dirname(sentinel),
                        sentinel=sentinel,
                    ),
                    path=path, rule="verification-gate",
                    task_id=tid, slug=slug,
                )

        # All newly-checked tasks are attested: consume their sentinels so none
        # can vouch for a second task.
        for tid, body in newly_checked:
            sentinel = lib.sentinel_path(slug, tid)
            attestation = ""
            try:
                with open(sentinel, "r", encoding="utf-8") as fh:
                    attestation = fh.read().strip()[:300]
            except Exception:
                pass
            try:
                os.remove(sentinel)
            except Exception:
                pass
            lib.log(EVENT, "consumed", task_id=tid, slug=slug,
                    attestation=attestation)

        lib.allow(EVENT, "tasks.md write accepted", path=path,
                  completed=len(newly_checked))

    except SystemExit:
        raise
    except Exception as exc:
        # Fail open, loudly in the log but silently to the user.
        try:
            lib.log(EVENT, "error", reason=repr(exc))
        except Exception:
            pass
        sys.stdout.write("{}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
