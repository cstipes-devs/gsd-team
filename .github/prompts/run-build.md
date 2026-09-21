# /run-build — drive the build-review loop (Copilot CLI)

Drive the build for the spec at `.claude/specs/<slug>/`.

You are the **team lead**. Read `spec.md`, `design.md`, and `tasks.md` before delegating anything.

> **How this differs from the Claude Code version.** Copilot has no shared task
> list and no messaging between subagents. Worker pools cannot self-claim from a
> queue. Instead: groups map to `/fleet` invocations, and **`tasks.md` on disk is
> the only coordination state**. Re-read it between groups rather than querying
> anything. That is a constraint, but it matches what the protocol already says —
> ground truth is the disk.

## Preflight

Stop and report instead of proceeding if any of these fail:

- `tasks.md` exists and every task matches the enforced format
- `design.md` has its **Security Considerations** section
- No open question in `spec.md` would destabilize the build
- The toolchains the tasks need are installed (`go`, `node`, `swift`, `terraform`). **A missing toolchain is a blocker, not something to work around** — a task whose `Run:` command cannot execute cannot be verified, and no agent may write a sentinel for a command it did not run.

## Per group

Groups run **sequentially**. Tasks within a group run **in parallel**.

**1. Delegate the group with `/fleet`.** Give it the group's tasks as the objective and name the agent for each role tag:

| Tag | Agent |
|---|---|
| `[go]` | `backend-go` |
| `[node]` | `backend-node` |
| `[react]` | `web-react` |
| `[swift]` | `ios-swift` |
| `[data]` | `data-engineer` |
| `[terraform]` | `terraform-engineer` |
| `[aws]` | `aws-architect` |
| `[design]` | `ux-designer` |
| `[review]` | `review-agent` |

Each subagent gets: the spec directory path, its specific task lines, and the instruction to run its `Run:` command, write its sentinel, and mark its task `[x]`.

Tasks in a group are file-disjoint by construction, so parallel execution is safe. **Do not hand two tasks that touch the same file to one fleet.**

**2. Verify the group on disk, not from reports.**

```bash
scripts/verify-spec.sh <slug>
```

Exit 0 means every `[x]` task is attested. **Non-zero means stop** — a task was marked complete without proof, which is a protocol violation, not a passing build. Report it and do not proceed to the next group.

Also check `git diff --name-only` against the group's assigned files. Silence from a subagent does not mean failure, and a completion report does not mean the work happened.

**3. Review the group.** Invoke `review-agent` as **synthesizer** (sole author of `review.md`, owns the verdict), plus 2–4 more as **analysts**, each on a **disjoint slice** of the diff. Analysts report findings; they write no files. Overlapping slices waste the cycle on duplicates.

**4. On FAIL** — one scoped fix wave addressing only the findings, then re-review. This consumes a cycle.

**5. On PASS** — next group.

## Cycle budget — you enforce this, no hook can

Each scope gets **3 review cycles**: per-scope, non-resetting, non-transferable. A cycle is consumed when the synthesizer is invoked, before its verdict.

- Cycles 1 and 2 each earn one scoped fix wave on failure.
- **Cycle 3 is terminal.** On failure, mark the scope blocked, stop, and surface it to the user with what is outstanding and what you recommend. Do not start a fourth cycle.

Track the count explicitly in your working notes — there is no task state to hold it for you.

## End-to-end pass

Once every group passes, run one integrated review as its own scope with its own 3-cycle budget: cross-component seams, contract compliance between pieces built in parallel, and **every acceptance criterion in `spec.md` verified against running code** — not against the diff.

## Docs and cleanup

README and API docs updated, scaffolding and dead code removed, commits conventional per `.github/skills/git-workflow/SKILL.md`.

## Report

- Groups completed, tasks done, cycles consumed per scope
- `scripts/verify-spec.sh` output for the final state
- Outstanding findings by severity
- Acceptance criteria met vs. unmet
- Anything blocked, and what it needs
- Test tiers that ran, and any escalated as unavailable

Be honest about what did not pass. A build reported green that is not green is worse than one reported red.
