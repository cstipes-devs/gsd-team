# GSD Team

A spec-driven multi-agent development team for Claude Code, organized into three groups.

## The groups

**Planning** — decides what to build and how it should be shaped. Writes specs, architecture, diagrams, and decision records. Never writes application code.

| Agent | Owns |
|---|---|
| `solution-architect` | **Group lead.** `design.md`, `tasks.md` |
| `requirements-analyst` | `spec.md` — requirements and acceptance criteria |
| `diagram-author` | `diagrams/` — Mermaid C4, sequence, ER |
| `tradeoff-analyst` | `adr/` — decision records |
| `ux-designer` | `mockups/` — interactive prototypes, wireframes |

**Execution** — builds it. Each agent owns a disjoint set of files, which is what makes parallel work safe.

| Agent | Stack |
|---|---|
| `backend-go` | Go services |
| `backend-node` | Node / TypeScript services |
| `web-react` | React web app |
| `ios-swift` | Swift / SwiftUI native |
| `data-engineer` | Schema, migrations, pipelines |

**Deployment** — provisions and reviews the infrastructure. Never writes application code.

| Agent | Owns |
|---|---|
| `terraform-engineer` | Terraform modules, environments, state, IAM |
| `aws-architect` | Well-Architected review → `sa-review.md`. **Review-only.** |

**Review** — `review-agent` runs as synthesizer (sole author of `review.md`, owns the verdict) or analyst (one disjoint slice, messages findings, writes nothing).

## Workflow

```
/brainstorm <idea>      → .claude/specs/<slug>/requirements.md
/plan-feature <slug>    → spec.md, design.md, diagrams/, adr/, tasks.md
/run-build <slug>       → build → review → fix → end-to-end → docs
```

Everything for one feature lives in `.claude/specs/<slug>/`.

## Rules that bind every agent

- @.claude/rules/agent-team-protocol.md — lifecycle, task format, **Verification Gate**, review budget
- @.claude/rules/testing-standards.md — T1–T4 tiers and the command for each stack
- @.claude/rules/tech-stack-standards.md — Go, TypeScript, React, Swift, Terraform idioms
- @.claude/rules/aws-security-guidelines.md — least privilege, secrets, no unapproved prod writes
- @.claude/rules/execution-hygiene.md — non-interactive execution, dependency isolation

## The four things that matter most

**1. Task format is enforced.** The `TaskCreated` hook rejects anything that does not match:

```
[role] <verb> <what> | <file paths> | <acceptance>. Run: <command>
```

Roles: `planning` `go` `node` `react` `swift` `data` `terraform` `aws` `review`.

**2. Completion requires a verification sentinel.** Before marking a task complete, run the `Run:` command, confirm it passed, then:

```bash
mkdir -p ~/.claude/logs/verified/<team_name>
echo "<Run command> PASSED" > ~/.claude/logs/verified/<team_name>/task-<task_id>.verified
```

The `TaskCompleted` hook blocks without it and consumes it on success. **Writing a sentinel for a command you did not run defeats the entire system.** If a tier cannot run here, mark the task blocked and say so — that is the correct outcome.

**3. Groups are wide; barriers are rare.** Tasks in a group run in parallel and **must not share files**. Create a new group only where task B literally needs task A's output on disk.

**4. Ground truth is the disk.** `tasks.md` + sentinels + `git diff` + files on disk beat `TaskList` output and completion messages. Message delivery is laggy and lossy — silence does not mean failure, and a receipt does not mean the work happened.

## Review budget

Each scope — each task group, plus the end-to-end pass — gets **3 review cycles**, non-resetting and non-transferable. A cycle is consumed when the synthesizer spawns. **Cycle 3 is terminal**: on failure the scope is blocked and surfaced to the user.

## Environment notes

- `terraform` is **not installed** on this machine. Terraform `Run:` commands will fail until `brew install terraform`.
- Present: `git`, `go`, `node`, `swift`, `python3`.
