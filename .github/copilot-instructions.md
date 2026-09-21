# GSD Team — Copilot CLI

A spec-driven multi-agent development team, organized into four groups. This is the Copilot CLI port of the Claude Code configuration in `.claude/`.

## The groups

**Planning** — decides what to build and how it should be shaped. Never writes application code.

| Agent | Owns |
|---|---|
| `solution-architect` | **Group lead.** `design.md`, `tasks.md` |
| `requirements-analyst` | `spec.md` — requirements and acceptance criteria |
| `ux-designer` | `mockups/` — interactive prototypes |
| `tradeoff-analyst` | `adr/` — decision records |
| `diagram-author` | `diagrams/` — Mermaid C4, sequence, ER |

**Execution** — builds it. Each agent owns a disjoint set of files.

| Agent | Stack |
|---|---|
| `backend-go` | Go services |
| `backend-node` | Node / TypeScript services |
| `web-react` | React web app |
| `ios-swift` | Swift / SwiftUI native |
| `data-engineer` | Schema, migrations, pipelines |

**Deployment** — provisions and reviews infrastructure. Never writes application code.

| Agent | Owns |
|---|---|
| `terraform-engineer` | Terraform modules, state, IAM |
| `aws-architect` | Well-Architected review → `sa-review.md`. **Review-only.** |

**Review** — `review-agent`, as synthesizer (sole author of `review.md`) or analyst (one disjoint slice, no files).

## Invoking agents

```bash
copilot --agent solution-architect --prompt "Design the checkout flow"
```

Interactively: `/agent` to pick one, or name it in a prompt — "Use the tradeoff-analyst agent to compare Postgres and DynamoDB."

## Workflow

The three prompts in `.github/prompts/`:

```
brainstorm.md     an idea       → .claude/specs/<slug>/requirements.md
plan-feature.md   <slug>        → spec, design, diagrams, ADRs, mockups, tasks
run-build.md      <slug>        → /fleet build → review → fix → end-to-end
```

Everything for one feature lives in `.claude/specs/<slug>/`. (The path keeps `.claude/` so both toolchains read and write the same spec directory.)

## Rules that bind every agent

- @.claude/rules/agent-team-protocol.md — lifecycle, task format, **Verification Gate**, review budget
- @.claude/rules/testing-standards.md — T1–T4 tiers and the command per stack
- @.claude/rules/tech-stack-standards.md — Go, TypeScript, React, Swift, Terraform idioms
- @.claude/rules/aws-security-guidelines.md — least privilege, secrets, no unapproved prod writes
- @.claude/rules/execution-hygiene.md — non-interactive execution, dependency isolation

These are shared with the Claude Code configuration — one copy, not two.

## The four things that matter most

**1. Task format is enforced.** A `preToolUse` hook **denies the write** if any task line in `tasks.md` does not match:

```
[role] <verb> <what> | <file paths> | <acceptance>. Run: <command>
```

Roles: `planning` `design` `go` `node` `react` `swift` `data` `terraform` `aws` `review`.

**2. Marking a task `[x]` requires a verification sentinel.** Run the `Run:` command, confirm it passed, then:

```bash
# Get the id and path for your task line
python3 scripts/copilot_hooks/task_id.py --path --slug <spec-slug> '<the full task line>'

mkdir -p ~/.gsd-team/logs/verified/<spec-slug>
echo "<Run command> PASSED" > ~/.gsd-team/logs/verified/<spec-slug>/task-<id>.verified
```

The hook **denies the `[x]` write** without it and consumes it on success so it cannot cover a second task. **Writing a sentinel for a command you did not run defeats the entire system.** If a tier cannot run here, leave the task unchecked and report it blocked — that is the correct outcome.

**3. Groups are wide; barriers are rare.** Tasks in a group run in parallel and **must not share files**. Create a new group only where task B literally needs task A's output on disk.

**4. Ground truth is the disk.** `tasks.md` + sentinels + `git diff`. Copilot subagents have isolated contexts and cannot message each other, so a completion report is not evidence. Run `scripts/verify-spec.sh <slug>` to check.

## Review budget

Each scope — each task group, plus the end-to-end pass — gets **3 review cycles**, non-resetting. A cycle is consumed when the synthesizer is invoked. **Cycle 3 is terminal**: on failure the scope is blocked and surfaced to the user.

No hook can count cycles here. The lead tracks it explicitly.

## What Copilot cannot do that Claude Code can

Stated so nobody wastes time looking for it:

- **No idle nudging** — no `TeammateIdle` event exists, so agents are not prompted to self-claim remaining work.
- **No inter-agent messaging** — subagents have isolated contexts. Coordination happens through the spec directory on disk.
- **No shared task list** — `tasks.md` is the only shared state, read and written as a file.

See `docs/COPILOT-CLI.md` for the full comparison.
