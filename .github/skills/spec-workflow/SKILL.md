---
name: spec-workflow
description: The six-phase spec-driven development loop this team runs — plan, build, review, fix, end-to-end, docs. Covers how to structure task groups for maximum parallelism, how to run parallel review with a synthesizer and analysts, and the bounded review-cycle budget. Use when planning a feature, writing tasks.md, or driving a build through the agent team.
---

# Spec-Driven Workflow

How a feature goes from a sentence to shipped code with this team.

## The spec directory

Everything for one feature lives in `.claude/specs/<slug>/`:

```
requirements.md   # optional, from /brainstorm — raw ideation
spec.md           # requirements-analyst — WHAT and acceptance criteria
design.md         # solution-architect — HOW, incl. Security Considerations
diagrams/         # diagram-author — Mermaid
adr/              # tradeoff-analyst — decision records
tasks.md          # solution-architect — the work, grouped
review.md         # review synthesizer — findings and verdict
sa-review.md      # aws-architect — Well-Architected findings
```

## The six phases

**1. Plan** — `requirements-analyst` writes `spec.md`. `solution-architect` writes `design.md` and `tasks.md`, pulling in `tradeoff-analyst` for contested decisions and `diagram-author` once the shape is stable. `aws-architect` reviews the infrastructure design if there is any. Ends with a **Handoff Package** and the lead role passing to the main agent.

**2. Build** — the main agent spawns worker pools. Groups run **sequentially**; tasks inside a group run **in parallel**. Agents self-claim, implement, self-verify, write a sentinel, and mark complete.

**3. Review** — after each group, a synthesizer plus analysts review that group's output. Verdict goes in `review.md`.

**4. Fix** — on FAIL, one scoped fix wave addressing the findings, then re-review. This consumes a cycle.

**5. End-to-end** — once all groups pass, one integrated review over the whole feature: cross-component seams, and every acceptance criterion in `spec.md` checked against reality. This is its own scope with its own 3-cycle budget.

**6. Docs and cleanup** — README and API docs updated, dead code and scaffolding removed, commits conventional per the git-workflow skill.

## Structuring tasks.md — this is where speed comes from

```markdown
## Group 1 — Foundations
- [ ] [terraform] Provision SQS queue and DLQ | infra/modules/queue/*.tf | queue exists with redrive policy. Run: terraform validate && terraform plan -input=false
- [ ] [data] Add orders table migration | db/migrations/003_orders.* | up and down both apply cleanly. Run: migrate up && migrate down && migrate up

## Group 2 — Services
- [ ] [go] Implement POST /orders handler | internal/api/orders.go, internal/api/orders_test.go | returns 201 with order id; 409 on duplicate. Run: go test ./internal/api/...
- [ ] [node] Implement order-confirmation consumer | src/consumers/confirm.ts, src/consumers/confirm.test.ts | ack on success, DLQ after 3 failures. Run: npm test -- confirm
- [ ] [react] Order submission form | src/features/orders/OrderForm.tsx, OrderForm.test.tsx | all four async states; a11y labelled. Run: npx vitest run OrderForm
- [ ] [swift] Order submission screen | Sources/Orders/OrderView.swift, Tests/OrderViewTests.swift | handles offline. Run: swift test --filter OrderView
```

The rules that determine whether the build takes one hour or six:

- **Make groups wide.** As many file-disjoint same-role tasks per group as you have instances of that role. Four `[go]` tasks in one group finish in the time of the slowest one; four groups of one finish in the sum.
- **A new group is a barrier — only create one for a real dependency.** "These feel related" is not a dependency. Ask: does task B literally need task A's output on disk? If no, same group.
- **Front-load shared interfaces.** Put the type definitions, API contracts, and schema in the earliest group so every consumer fans out in parallel behind them.
- **Infrastructure precedes the code that runs on it.**
- **Never let two tasks in the same group write the same file.** This is the invariant the whole model rests on. If you cannot split them cleanly, they belong in different groups.
- **Saturate both pools.** Independent execution and deployment work belongs in the *same* group, not in sequence.

Every task carries a role tag, explicit file paths, acceptance criteria, and a real `Run:` command at the right tier. Format is enforced by hook — see @.claude/rules/agent-team-protocol.md.

## Parallel review

- **One synthesizer** per cycle: sole author of `review.md`, owns the verdict.
- **N analysts**, each assigned a **disjoint slice** of the diff. They message findings to the synthesizer and write no files. Overlapping slices produce duplicate findings and waste the cycle.
- The synthesizer deduplicates, judges severity, and decides.

## The cycle budget

Each scope — each task group, plus the end-to-end pass — gets **3 review cycles**.

- Per scope, **non-resetting**, **non-transferable**. Group A's unused cycle does not help Group B.
- A cycle is consumed **when the synthesizer spawns**, before the verdict exists.
- Cycles 1 and 2 each earn exactly one scoped fix wave on failure.
- **Cycle 3 is terminal.** Fail there and the scope is blocked for a user decision — no automatic retry.

This bound exists so a stuck scope surfaces to a human instead of burning an afternoon in a fix-review loop.

## Definition of done

A feature is complete when **all** hold:

- Every task in `tasks.md` is `[x]`
- Zero CRITICAL or HIGH findings outstanding
- All required test tiers pass, or an unavailable tier is explicitly escalated and accepted
- Every acceptance criterion in `spec.md` is verified against running code
- Docs updated, scaffolding removed

## Ground truth

`tasks.md` + sentinels + `git diff` + files on disk. Not a task list, not completion messages. Messages are laggy and lossy — **silence does not mean failure, and a receipt does not mean the work happened.** When in doubt, look at the disk.
