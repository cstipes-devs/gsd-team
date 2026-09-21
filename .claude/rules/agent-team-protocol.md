# Agent Team Protocol

How teammates claim work, verify it, and report back. This file is binding on every agent in this repo.

## Teammate lifecycle

1. **Receive delegation.** The lead sends you a spec path and a set of task IDs via `SendMessage`.
2. **Read the specs before touching anything.** At minimum `spec.md` and `design.md` in the spec directory. Do not infer requirements you could have read.
3. **Claim your task.** `TaskUpdate` → `in_progress`. Dependencies unblock automatically when their blockers complete.
4. **Implement exactly what the task describes.** Not more. Scope creep inside a task breaks the file-disjointness that makes parallel work safe.
5. **Self-verify against the Verification Gate below**, then `TaskUpdate` → `completed`.
6. **Report.** Mark the line in `tasks.md` `[x]` with a `> Done.` note, then `SendMessage` the lead a one-paragraph summary.
7. **Then self-claim.** If unclaimed, unblocked tasks remain for your role, take one. Do not idle waiting to be asked.

## Task format

Every task line must match:

```
[role] <verb> <what> | <file paths> | <acceptance>. Run: <command>
```

Valid role tags:

| Group | Tags |
|---|---|
| Planning | `[planning]` `[design]` |
| Execution | `[go]` `[node]` `[react]` `[swift]` `[data]` |
| Deployment | `[terraform]` `[aws]` |
| Review | `[review]` |

`task_created_format_check.py` enforces this shape. Coordination, research, and spike tasks that genuinely have no verification command include `[skip-format-check]` to bypass it — use this sparingly and never for work that produces code.

The `Run:` command is not decoration. It is the command a human could execute to confirm the task is actually done, and it must exercise the correct test tier per @.claude/rules/testing-standards.md.

## Verification Gate

Before any `TaskUpdate` → `completed`, all five must hold:

1. You executed the `Run:` command and it passed. Not "should pass" — you ran it.
2. The command exercises the right tier for the work. A T3 task is not satisfied by a unit test.
3. Interfaces and output contracts match the spec exactly — field names, types, status codes, error shapes.
4. You modified only the files your task assigned you. Check with `git diff --name-only`.
5. You read real success signals. A `200` with an error body in it is a failure. Check payload contents and exit codes, not just that something responded.

Then write the sentinel, immediately before marking the task complete:

```bash
mkdir -p ~/.claude/logs/verified/<team_name>
echo "<Run command> PASSED" > ~/.claude/logs/verified/<team_name>/task-<task_id>.verified
```

The sentinel is your attestation that verification actually ran. `task_completed_verify_gate.py` blocks completion without it, and consumes the file on success so it cannot be reused for a second task.

Writing the sentinel without running the command is the one thing in this protocol that makes the whole system worthless. Don't.

## Communication

- **Teammate → teammate:** `SendMessage` for interface clarifications, dependency questions, shared output locations.
- **Teammate → lead:** blockers needing a decision, completion summaries, scope questions.
- **Status:** `TaskUpdate` to claim and complete, `TaskList` / `TaskGet` to check state.

Do not broadcast. Message the specific agent who owns the thing you need.

## Review cycle budget

Each scope — a task group, or the end-to-end pass — gets exactly **3 review cycles**.

- The budget is **per scope**, **non-resetting**, and **non-fungible**. An unused cycle in group A does not help group B.
- A cycle is consumed when the review synthesizer spawns, *before* its verdict is known.
- Cycles 1 and 2, on failure, earn exactly one scoped fix wave each.
- **Cycle 3 is terminal.** If it fails, the scope is marked blocked and surfaced to the user for a decision. No automatic retry.

## Ground truth

Authoritative state lives on disk, not in messages:

```
tasks.md  +  verification sentinels  +  git diff  +  files actually on disk
```

Those beat `TaskList` output and message receipts every time. Message delivery is laggy and lossy — **silence does not mean failure**, and a receipt does not mean the work happened. When in doubt, look at the disk.
