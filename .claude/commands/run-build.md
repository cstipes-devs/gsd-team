---
description: Drives the build-review loop — spawns execution and deployment pools group by group, runs parallel review with a synthesizer, and enforces the 3-cycle budget.
argument-hint: <slug>
---

Drive the build for the spec at `.claude/specs/$ARGUMENTS/`.

You are the **team lead** for this build. Read `spec.md`, `design.md`, and `tasks.md` before spawning anyone.

## Preflight

Stop and report instead of proceeding if any of these fail:

- `tasks.md` exists and every task matches the enforced format
- `design.md` has its **Security Considerations** section
- No open question in `spec.md` would make the build unstable
- The toolchains the tasks need are actually installed (`go`, `node`, `swift`, `terraform`). **Missing toolchain is a blocker, not something to work around** — a task whose `Run:` command cannot execute cannot be verified, and an agent must never fake a sentinel.

## Per group

Groups run **sequentially**. Tasks within a group run **in parallel**.

**1. Spawn the pool.** One agent per task, matched by role tag:

| Tag | Agent |
|---|---|
| `[go]` | `backend-go` |
| `[node]` | `backend-node` |
| `[react]` | `web-react` |
| `[swift]` | `ios-swift` |
| `[data]` | `data-engineer` |
| `[terraform]` | `terraform-engineer` |
| `[aws]` | `aws-architect` |
| `[review]` | `review-agent` |

Give each agent the spec directory path and its specific task IDs. Agents self-claim, implement, self-verify, write a sentinel, and mark complete. When one finishes, it takes the next unclaimed task for its role rather than idling.

**2. Wait for the group.** Check ground truth, not messages — `tasks.md`, sentinels, and `git diff`. Per @.claude/rules/agent-team-protocol.md, **silence does not mean failure and a receipt does not mean the work happened.**

**3. Review the group.** Spawn one `review-agent` as **synthesizer** (sole author of `review.md`, owns the verdict) plus 2–4 as **analysts**, each assigned a **disjoint slice** of the diff. Analysts message findings and write no files. Overlapping slices waste the cycle on duplicate findings.

**4. On FAIL** — one scoped fix wave addressing only the findings, then re-review. This consumes a cycle.

**5. On PASS** — move to the next group.

## Cycle budget — enforce this strictly

Each scope gets **3 review cycles**: per-scope, non-resetting, non-transferable. A cycle is consumed **when the synthesizer spawns**, before its verdict.

- Cycles 1 and 2 earn one scoped fix wave each on failure.
- **Cycle 3 is terminal.** On failure, mark the scope blocked, stop, and surface it to the user with what is outstanding and what you recommend. Do not start a fourth cycle.

## End-to-end pass

Once every group passes, run one integrated review as its own scope with its own 3-cycle budget: cross-component seams, contract compliance between the pieces that were built in parallel, and **every acceptance criterion in `spec.md` verified against running code** — not against the diff.

## Docs and cleanup

README and API docs updated, scaffolding and dead code removed, commits conventional per @.claude/skills/git-workflow/SKILL.md.

## Report

- Groups completed, tasks done, cycles consumed per scope
- Outstanding findings by severity
- Acceptance criteria met vs. unmet
- Anything blocked, with what it needs
- Test tiers that ran, and any that were escalated as unavailable

Be honest about what did not pass. A build reported green that is not green is worse than a build reported red.
