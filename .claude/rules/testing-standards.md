# Testing Standards

Four verification tiers. Every task's `Run:` command must exercise the tier its acceptance criteria imply.

## The tiers

| Tier | What it proves | Mocks allowed |
|---|---|---|
| **T1 — Unit** | Isolated logic is correct | Yes |
| **T2 — Integration / contract** | Components agree on schemas and interfaces | At process boundaries only |
| **T3 — Deployed resource** | A real, provisioned resource works with the application's own identity | **No** |
| **T4 — End-to-end** | A user journey satisfies the spec's acceptance criteria | **No** |

A task is not complete because a lower tier passed. If acceptance says "the endpoint returns the user's orders," a unit test on the handler is not sufficient — that is T2 at minimum.

## Commands by stack

| Tier | Go | Node / TS | React | Swift | Terraform |
|---|---|---|---|---|---|
| **T1** | `go test ./...` | `npm test` | `npx vitest run` | `swift test` | `terraform validate` |
| **T2** | `go test -tags=integration ./...` | contract tests against a running dep | `npx vitest run --dir src/components` (RTL) | `xcodebuild test -scheme <S>` | `terraform plan -input=false -detailed-exitcode` |
| **T3** | curl/client hitting the deployed endpoint with app credentials | same | — | — | post-apply resource assertion (`aws <svc> describe-*`) |
| **T4** | journey script asserting spec acceptance criteria | Playwright / equivalent | Playwright | XCUITest | — |

## Rules

- **Every stack runs T1 and T2 minimum** before a task completes.
- **T3 uses the application's identity**, not your admin credentials. Passing as admin and failing in production is the exact bug T3 exists to catch.
- **T4 asserts the spec's acceptance criteria verbatim**, not a paraphrase of them.
- **No skipped or focused tests** left in a completed task — no `t.Skip`, `it.only`, `describe.skip`, `XCTSkip` without an inline comment explaining why and a linked task.
- **A flaky test is a failing test.** Do not retry until green. Fix it or escalate it.
- Tests assert behavior and contracts, not implementation details. Renaming a private function should not break a test.

## Escalation

If a tier genuinely cannot run — no AWS account for T3, no device for a Swift T4 — do not silently drop it. Mark the task blocked, state which tier is unavailable and why, and let the lead decide. Never write the verification sentinel for a tier you did not actually execute.
