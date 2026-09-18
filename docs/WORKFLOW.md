# Workflow — A Feature End to End

One feature through all six phases. The example: **order submission** — a React form and an iOS screen both posting to a Go API, which writes to Postgres and emits to SQS for an async confirmation consumer in Node.

## Phase 1 — Plan

```
/brainstorm users need to submit orders from web and mobile
```

Clarifying questions, then `.claude/specs/order-submission/requirements.md`.

```
/plan-feature order-submission
```

`requirements-analyst` writes `spec.md`:

```markdown
## Requirements
R1. An authenticated user can submit an order from web or iOS.
R2. Duplicate submission of the same idempotency key must not create two orders.
R3. Order confirmation is delivered asynchronously.

## Acceptance criteria
AC1. POST /orders with a valid body returns 201 and a body containing `orderId`.
AC2. POST /orders with an idempotency key already used returns 409 with
     `{"code":"DUPLICATE_ORDER"}` and creates no second row.
AC3. A confirmation message appears on the orders-confirm queue within 5s of a 201.
AC4. Submitting while offline on iOS shows a retry affordance and does not lose input.
```

Note the shape: each criterion names the status code, the payload, and the observable effect. A T4 test can assert these verbatim. "Handles duplicates gracefully" could not be tested.

`solution-architect` writes `design.md` — components, the `POST /orders` contract with exact field names and error shapes, the data model, and the mandatory **Security Considerations** section. `tradeoff-analyst` writes an ADR on sync vs. async confirmation. `diagram-author` draws the container view and the submission sequence. `aws-architect` reviews the infrastructure design.

Then `tasks.md`:

```markdown
## Group 1 — Foundations
- [ ] [terraform] Provision orders SQS queue and DLQ | infra/modules/orders-queue/*.tf | queue and DLQ exist with redrive maxReceiveCount 3. Run: terraform validate && terraform plan -input=false
- [ ] [data] Add orders table and idempotency index | db/migrations/004_orders.up.sql, db/migrations/004_orders.down.sql | unique index on idempotency_key; up and down both apply. Run: migrate up && migrate down && migrate up

## Group 2 — Services and clients
- [ ] [go] Implement POST /orders handler | internal/api/orders.go, internal/api/orders_test.go | 201 with orderId; 409 DUPLICATE_ORDER on repeat key. Run: go test ./internal/api/...
- [ ] [node] Implement confirmation consumer | src/consumers/confirm.ts, src/consumers/confirm.test.ts | acks on success, DLQ after 3 failures. Run: npm test -- confirm
- [ ] [react] Order submission form | src/features/orders/OrderForm.tsx, src/features/orders/OrderForm.test.tsx | loading/empty/error/success states, labelled inputs. Run: npx vitest run OrderForm
- [ ] [swift] Order submission screen | Sources/Orders/OrderView.swift, Tests/OrdersTests/OrderViewTests.swift | offline shows retry, input preserved. Run: swift test --filter OrderView
```

**Why this shape.** Group 1 is the barrier: the queue and the table must exist before anything uses them. Group 2 is four tasks across four different agents running simultaneously on disjoint files — it finishes in the time of the slowest one. Splitting it into four groups would have taken four times as long for no benefit, because none of those tasks needs another's output.

The API contract lives in `design.md` *before* Group 2 starts, which is what lets the Go, React, and Swift agents build compatible code without talking to each other.

## Phase 2 — Build

```
/run-build order-submission
```

The lead checks preflight, then spawns Group 1: `terraform-engineer` and `data-engineer` in parallel. Each reads the specs, claims its task, implements, and runs its `Run:` command.

`data-engineer` runs up, down, and up again — proving the migration is reversible — then:

```bash
mkdir -p ~/.claude/logs/verified/order-submission
echo "migrate up && migrate down && migrate up PASSED" \
  > ~/.claude/logs/verified/order-submission/task-g1-t2.verified
```

Without that sentinel the `TaskCompleted` hook blocks the completion. With it, the hook allows it and **deletes the file** so it cannot attest to a second task.

Group 1 passes review; the lead spawns Group 2's four agents.

## Phase 3 — Review

One `review-agent` as **synthesizer**, three as **analysts** on disjoint slices: the Go handler, the Node consumer, the two clients. Analysts message findings; the synthesizer deduplicates, judges severity, and writes `review.md`.

A real finding:

```markdown
### [HIGH] Idempotency check races under concurrent submission
**Where:** internal/api/orders.go:84
**Issue:** The handler SELECTs for an existing idempotency_key, then INSERTs.
Two concurrent requests with the same key both pass the SELECT.
**Failure scenario:** User double-taps submit. Both requests read no existing
key, both insert, and AC2 fails — two orders created.
**Fix:** Rely on the unique index from migration 004 and handle the constraint
violation as the 409 path, rather than checking first. Owner: backend-go.
```

Verdict: `FAIL`, 1 HIGH, cycle 1 of 3.

## Phase 4 — Fix

One scoped fix wave: `backend-go` addresses only that finding. Re-review as cycle 2 → `PASS`.

If cycle 3 had also failed, the scope would be **blocked** and handed to you with what is outstanding. No fourth cycle — that bound is what keeps a stuck scope from burning an afternoon.

## Phase 5 — End to end

Its own scope, its own 3-cycle budget. Checks the seams that parallel work tends to break — does the Swift client decode exactly what the Go handler emits? — and verifies **every acceptance criterion against running code**, not against the diff. AC3's five-second window is a real T4 assertion against a real queue.

## Phase 6 — Docs and cleanup

API docs updated with the 409 case, README current, scaffolding removed, commits conventional.

## What to watch for

| Symptom | Cause | Fix |
|---|---|---|
| Tasks rejected at creation | Format does not match, or an unrecognized role tag | Check the four parts and the tag list in `team_hook_lib.py` |
| Completion blocked | No sentinel, or it was already consumed | Run the `Run:` command, then write the sentinel with the exact task id |
| Build is slow | Too many groups | Ask of each barrier: does B actually need A's output on disk? |
| Parallel agents produce incompatible code | Interface contract underspecified in `design.md` | Contracts need exact field names, types, status codes, and error shapes |
| A green build that is not green | A sentinel was written for a command that did not run | This is the failure that makes the system worthless — never do it |

## Audit

Every hook decision lands in `~/.claude/logs/team-hooks.jsonl`:

```bash
tail -20 ~/.claude/logs/team-hooks.jsonl | python3 -m json.tool --json-lines
```
