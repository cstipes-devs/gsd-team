# Tech Stack Standards

Idioms each execution and deployment agent follows. When existing code in a repo disagrees with this file, **match the existing code** and note the divergence — consistency inside a codebase beats consistency with this document.

## Go

- Standard library first. Reach for a framework only when the task calls for one.
- `context.Context` is the first parameter of anything that does I/O, and it is threaded through — never `context.TODO()` in shipped code.
- Errors wrap with `fmt.Errorf("...: %w", err)`; callers branch with `errors.Is` / `errors.As`, never on string matching.
- Table-driven tests with subtests (`t.Run`). Parallel where safe.
- Accept interfaces, return structs. Define the interface at the consumer.
- No panics in library code. `panic` is for genuinely unrecoverable initialization failure.
- `gofmt` clean; `go vet ./...` passes before completion.

## Node / TypeScript

- `strict: true`. **No `any`** — use `unknown` and narrow.
- Validate at boundaries (HTTP handlers, queue consumers, config load) with zod or equivalent. Data from outside the process is untyped until proven otherwise.
- ESM, `async`/`await`. No floating promises — every promise is awaited or explicitly `void`ed.
- Errors are `Error` subclasses with discriminating fields, not thrown strings or bare objects.
- Structured logging (pino or equivalent). No `console.log` in shipped code paths.
- Lockfile committed; `npm ci` in CI.

## React

- Function components and hooks only. Follow the rules of hooks — no conditional hook calls.
- Server state belongs in a query library (TanStack Query or equivalent), not in `useEffect` + `useState`.
- Derive during render rather than syncing with `useEffect`. Most `useEffect`s that set state are bugs.
- Tests use React Testing Library, querying **by role and accessible name**. No test IDs unless there is genuinely no accessible handle.
- Accessibility is not optional: semantic elements, labelled inputs, keyboard-reachable interactions, visible focus.
- Colocate a component with its test and its styles.

## Swift / iOS

- SwiftUI for new views; UIKit only where the task requires it or the codebase already is.
- `async`/`await` and structured concurrency. No completion-handler pyramids in new code.
- Concurrency correctness: types crossing isolation boundaries are `Sendable`; UI state is `@MainActor`.
- **No force-unwrap and no force-try outside tests.** `guard let` with a meaningful early return.
- `struct` by default; `class` when identity or reference semantics are actually needed.
- Value types for models, `Codable` for wire formats, and decode errors are handled — not `try!`.
- XCTest for unit, XCUITest for journeys.

## Terraform

- Everything is a module. Root configs compose modules; they do not declare dozens of raw resources.
- **Pin provider versions** with `required_providers` and a version constraint. Commit `.terraform.lock.hcl`.
- **Remote state**, encrypted, with locking. Never local state for anything shared, never state in git.
- No hardcoded ARNs, account IDs, or region strings — use variables, data sources, and `aws_caller_identity`.
- Variables have `type` and `description`; anything non-obvious has a `validation` block. Outputs have descriptions.
- One workspace or directory per environment. Environments differ by `tfvars`, not by edited resource blocks.
- `terraform fmt -check -recursive` and `terraform validate` pass before completion.

## Cross-cutting

- **Name things for what they mean in the domain**, not for their type. `orderTotal`, not `numVal2`.
- Comments explain *why*, never *what*. Code that needs a *what* comment should be rewritten.
- No dead code, no commented-out blocks, no `TODO` without a linked task.
- Public interfaces get doc comments; internal helpers usually do not need them.
- Match the surrounding file's conventions over your own preferences.
