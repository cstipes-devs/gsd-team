# GSD Team

**A spec-driven team of 13 AI agents for [Claude Code](https://claude.com/claude-code)** — they plan a feature, build it in parallel, and review their own work, with a verification gate that agents cannot talk their way past.

Point it at a feature request. It produces a specification with testable acceptance criteria, an architecture with real interface contracts, a costed decision record, an interactive UX prototype, and a task breakdown optimized for parallel execution — then builds it and reviews the result.

```
/brainstorm     an idea            →  requirements.md
/plan-feature   <slug>             →  spec, design, diagrams, ADRs, mockups, tasks
/run-build      <slug>             →  build → review → fix → end-to-end → docs
```

Architecturally guided by [`aws-samples/sample-claude-code-agent-team`](https://github.com/aws-samples/sample-claude-code-agent-team). This keeps that sample's machinery — the plan/build/review loop, the rules layer, the enforcement hooks — and replaces its flat four-agent roster with thirteen stack-specific agents in four groups.

---

## Why this exists

Ask a single AI agent to build a feature and you usually get plausible code against imagined requirements, with tests that assert a mock was called.

This splits the work the way a real team does, and enforces the boundaries mechanically:

- **Planning agents never write code.** Design decisions land in documents where you can argue with them, not buried in an implementation.
- **Execution agents own disjoint files.** That is what makes parallel work safe — two agents writing one file is the failure mode the whole structure prevents.
- **Reviewers never fix.** A reviewer who patches the code has stopped reviewing it.
- **No task completes without proof.** An agent must run its verification command and leave an attestation on disk. A hook blocks completion otherwise and consumes the attestation so it cannot be reused.

The interesting constraint is the last one. Agents are good at believing they finished. This makes finishing a thing you have to demonstrate.

---

## Requirements

| | |
|---|---|
| **Claude Code** | 2.1 or newer (agent teams, task hooks) |
| **Python** | 3.8+ on `PATH` — runs the three enforcement hooks |
| **Toolchains** | only the stacks you actually use: `go`, `node`, `swift`/Xcode, `terraform` |

Agent teams are an experimental feature, enabled by `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in the bundled `.claude/settings.json`.

---

## Install

### Into an existing project

```bash
git clone https://github.com/cstipes-devs/gsd-team.git /tmp/gsd-team
cp -r /tmp/gsd-team/.claude /path/to/your-project/
cp /tmp/gsd-team/CLAUDE.md /path/to/your-project/   # merge if you already have one
cd /path/to/your-project && claude
```

Hook paths resolve through `$CLAUDE_PROJECT_DIR`, so they work from any project root with no editing.

### As a standalone workspace

```bash
git clone https://github.com/cstipes-devs/gsd-team.git
cd gsd-team && claude
```

### Verify it took

In Claude Code, run `/agents` — you should see all 13. Then check the hooks are live:

```bash
echo '{"task_id":"t","description":"nonsense"}' | python3 .claude/hooks/task_created_format_check.py; echo "exit=$?"
```

`exit=2` means enforcement is working (it rejected a malformed task). `exit=0` means the hook is not wired up — check `.claude/settings.json`.

---

## The agents

### Planning — decides what to build and how it should be shaped

Writes specs, architecture, diagrams, decision records, and prototypes. **Never writes application code.**

| Agent | Model | Owns | Use it when |
|---|---|---|---|
| **`solution-architect`** | Opus | `design.md`, `tasks.md` | A feature needs an architecture before anyone writes code. Group lead, and the only author of the design. |
| **`requirements-analyst`** | Opus | `spec.md` | Requirements are vague, contested, or exist only in someone's head. Turns a request into numbered requirements and testable acceptance criteria. |
| **`ux-designer`** | Opus | `mockups/` | Screens exist whose layout or flow is contested, or a tap-count budget needs proving. Produces a clickable HTML prototype you can actually tap through. |
| **`tradeoff-analyst`** | Opus | `adr/` | A decision has real alternatives and reversing it later would be expensive. Writes ADRs with option matrices and reversibility analysis. |
| **`diagram-author`** | Sonnet | `diagrams/` | The architecture is stable enough to draw. Mermaid C4, sequence, and ER diagrams. |

### Execution — builds it

Each agent owns a disjoint set of files, which is what lets them run at the same time.

| Agent | Model | Tag | Stack |
|---|---|---|---|
| **`backend-go`** | Sonnet | `[go]` | Go services — handlers, business logic, AWS SDK |
| **`backend-node`** | Sonnet | `[node]` | Node / TypeScript — REST, GraphQL, Lambda, queue consumers |
| **`web-react`** | Sonnet | `[react]` | React — components, hooks, routing, client state |
| **`ios-swift`** | Sonnet | `[swift]` | Swift / SwiftUI — views, view models, networking, XCTest |
| **`data-engineer`** | Sonnet | `[data]` | Schema, migrations, indexes, pipelines |

### Deployment — provisions and reviews the infrastructure

**Never writes application code.**

| Agent | Model | Tag | Owns |
|---|---|---|---|
| **`terraform-engineer`** | Sonnet | `[terraform]` | Terraform modules, environments, remote state, IAM, pipelines |
| **`aws-architect`** | Opus | `[aws]` | Well-Architected review → `sa-review.md`. **Review-only** — never applies infrastructure. |

### Review — validates it

| Agent | Model | Tag | Modes |
|---|---|---|---|
| **`review-agent`** | Opus | `[review]` | **Synthesizer**: sole author of `review.md`, owns the verdict. **Analyst**: reviews one disjoint slice, reports findings, writes nothing. |

**Why Opus for some and Sonnet for others:** if the agent's job is to *decide*, it's Opus. If its job is to *build what was already decided*, it's Sonnet.

---

## How to use it

### The full workflow

```
/brainstorm a game tracking app with playthrough-level logging
```

Asks clarifying questions, then writes `.claude/specs/<slug>/requirements.md`. Where an answer is obvious it takes the default and records it as an assumption rather than spending a question on it.

```
/plan-feature <slug>
```

Runs the planning group in sequence: requirements → architecture → (diagrams, ADRs, UX prototype, Well-Architected review in parallel) → task breakdown. Ends with a **Handoff Package** summarizing what was produced and what is blocked.

```
/run-build <slug>
```

Drives the build: spawns worker pools group by group, runs parallel review after each, applies one scoped fix wave per failure, then a final end-to-end pass.

### Or call an agent directly

You do not have to run the whole loop:

```
Use tradeoff-analyst to compare Postgres and DynamoDB for this access pattern.
Use ux-designer to prototype the checkout flow and prove it fits in 3 taps.
Use aws-architect to review infra/ against the Well-Architected Framework.
Use review-agent to review the current diff for correctness and security.
```

### What lands on disk

Everything for one feature lives in `.claude/specs/<slug>/`:

```
requirements.md   raw ideation from /brainstorm
spec.md           numbered requirements + testable acceptance criteria
design.md         architecture, contracts, data model, security
diagrams/         Mermaid C4, sequence, ER
adr/              decision records
mockups/          interactive HTML prototype
tasks.md          the work, grouped for parallelism
review.md         findings and verdict
sa-review.md      Well-Architected findings
```

---

## What's enforced

Three Python hooks in `.claude/hooks/`. All **fail open** — a bug in enforcement can never wedge the team.

### 1. Task format

Tasks are rejected at creation unless they match:

```
[role] <verb> <what> | <file paths> | <acceptance>. Run: <command>
```

Roles: `planning` `design` `go` `node` `react` `swift` `data` `terraform` `aws` `review`

A real example:

```
[go] Implement POST /orders handler | internal/api/orders.go, internal/api/orders_test.go | returns 201 with order id, 409 on duplicate. Run: go test ./internal/api/...
```

Every task carries explicit file paths (so parallelism stays safe) and a real verification command (so completion means something). Coordination tasks with genuinely no output can bypass with `[skip-format-check]`.

### 2. The verification gate

Before marking a task complete, an agent must run its `Run:` command, confirm it passed, and write an attestation:

```bash
echo "<Run command> PASSED" > ~/.claude/logs/verified/<team>/task-<id>.verified
```

The hook blocks completion without it and **deletes it on use**, so one attestation cannot cover two tasks. If a test tier genuinely cannot run — no AWS account, no simulator — the agent is instructed to mark the task **blocked** rather than fake it.

### 3. Idle work claiming

When an agent goes idle with unclaimed work matching its role, it gets nudged to pick it up instead of waiting to be asked.

Every decision is logged to `~/.claude/logs/team-hooks.jsonl`.

---

## The ideas that make it work

**Groups are wide, barriers are rare.** Tasks in a group run in parallel and must not share files. Create a new group only where task B literally needs task A's output on disk. Four `[go]` tasks in one group finish in the time of the slowest; four groups of one finish in the sum.

**Interface contracts are written before parallel work starts.** That is what lets the Go, React, and Swift agents produce compatible code without talking to each other. A vague contract means incompatible code that surfaces three groups too late.

**Ground truth is the disk** — `tasks.md`, attestations, `git diff`. Not completion messages, which are laggy and lossy. Silence does not mean failure, and a receipt does not mean the work happened.

**Review is bounded.** Three cycles per scope, non-resetting. Cycle 3 is terminal and surfaces to a human, so a stuck scope cannot burn an afternoon in a fix-review loop.

---

## Layout

```
.claude/
├── agents/          13 agents in planning / execution / deployment / review
├── rules/           protocol, testing tiers, security, hygiene, stack standards
├── skills/          spec-workflow, git-workflow, documentation
├── commands/        brainstorm, plan-feature, run-build
├── hooks/           3 enforcement hooks + shared lib
├── specs/           your features land here
└── settings.json
docs/
├── AGENT-ROSTER.md  who does what, and how to add an agent
└── WORKFLOW.md      one feature end to end, with real task lines
CLAUDE.md            loaded every session
```

---

## Customizing

**Per-machine settings** go in `.claude/settings.local.json` (gitignored).

**Adding an agent** — create `.claude/agents/<group>/<name>.md` with `name`, `description`, and `model` frontmatter, then **register its role tag in `ROLE_TAGS` in `.claude/hooks/team_hook_lib.py`** and in the mapping in `teammate_idle_workcheck.py`. A tag the hook does not recognize will have all its tasks rejected at creation — that is the step people forget. Full checklist in [docs/AGENT-ROSTER.md](docs/AGENT-ROSTER.md#adding-an-agent).

**Changing standards** — the files in `.claude/rules/` are referenced by every agent. Edit those rather than editing thirteen agent prompts.

---

## Optional plugins

Not enabled in `settings.json` on purpose: a clone that references unregistered marketplaces errors at startup. Add what you want:

```bash
claude plugin marketplace add anthropics/claude-plugins-official
```

Useful here: `context7`, `feature-dev`, `frontend-design`, `security-guidance`, `pr-review-toolkit`, `aws-core`, `aws-serverless`, `deploy-on-aws`.

---

## Notes and limitations

- **Agent teams are experimental.** The feature flag and hook events may change between Claude Code releases.
- **This is opinionated.** Four test tiers, conventional commits, least-privilege AWS, no production applies without explicit approval. Edit `.claude/rules/` if you disagree — it is all plain markdown.
- **Long builds need a machine that stays awake.** A sleeping laptop kills in-flight agents. `caffeinate -dimsu` on macOS.
- **Verification is only as honest as the agents are.** The gate makes faking deliberate rather than accidental, which is the realistic goal — not a proof.

---

## Compatibility

Built for **Claude Code**, which supplies the task lifecycle events the verification gate binds to.

A **[`copilot-cli`](../../tree/copilot-cli) branch** ports the team to GitHub Copilot CLI. The 13 agents, the rules, and the skills transfer directly; the gate is reconstructed on Copilot's `preToolUse` hook, which can deny a tool call. Three capabilities have no equivalent and are documented rather than faked: idle nudging, inter-agent messaging, and shared task state. See [docs/COPILOT-CLI.md](docs/COPILOT-CLI.md).

Other assistants (Cursor, Codex, Continue) can reuse `.claude/rules/` and `.claude/skills/` as plain markdown standards — four test tiers, per-stack idioms, AWS security guidelines — but not the orchestration, which depends on hook events.


## License

MIT — see [LICENSE](LICENSE).
