# GSD Team

A spec-driven multi-agent development team for [Claude Code](https://claude.com/claude-code), organized into **planning**, **execution**, and **deployment** groups, with machine-enforced verification.

Architecturally guided by [`aws-samples/sample-claude-code-agent-team`](https://github.com/aws-samples/sample-claude-code-agent-team) — this keeps that sample's machinery (the plan→build→review loop, the rules layer, the enforcement hooks, the verification gate) and replaces its flat agent roster with twelve stack-specific agents.

## The team

**Planning** — decides what to build and how it should be shaped.
`solution-architect` · `requirements-analyst` · `diagram-author` · `tradeoff-analyst`

**Execution** — builds it, in parallel, on disjoint files.
`backend-go` · `backend-node` · `web-react` · `ios-swift` · `data-engineer`

**Deployment** — provisions and reviews the infrastructure.
`terraform-engineer` · `aws-architect`

**Review** — validates it.
`review-agent`

Stacks: Go, JavaScript/TypeScript, React, Swift, Terraform, AWS.

See [docs/AGENT-ROSTER.md](docs/AGENT-ROSTER.md) for what each one owns and when to call it.

## Usage

```bash
cd gsd-team
claude
```

```
/brainstorm      an idea → requirements.md
/plan-feature    requirements → spec, design, diagrams, ADRs, tasks
/run-build       tasks → build, review, fix, end-to-end, docs
```

[docs/WORKFLOW.md](docs/WORKFLOW.md) walks one feature through all six phases with real task lines and a real review finding.

## Using it on your own project

This repo is both the team definition and a working Claude Code project. To use the team elsewhere:

```bash
cp -r gsd-team/.claude /path/to/your-project/
cp gsd-team/CLAUDE.md /path/to/your-project/   # merge if you already have one
```

Hook paths resolve through `$CLAUDE_PROJECT_DIR`, so they work from any project root without editing.

## Requirements

| | |
|---|---|
| Claude Code | 2.1+ (agent teams, task hooks) |
| Python | 3.8+ on `PATH` — the hooks |
| Toolchains | whichever stacks you use: `go`, `node`, `swift`, `terraform` |

> **Note:** `terraform` is not currently installed on this machine. Terraform `Run:` commands will fail until `brew install terraform`. Agents are instructed to mark such tasks **blocked** rather than fake a verification.

Agent teams are enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `.claude/settings.json`.

## What is enforced

Three Python hooks in `.claude/hooks/`, all **fail-open** — a hook bug can never wedge the team.

**`task_created_format_check.py`** rejects malformed tasks:

```
[role] <verb> <what> | <file paths> | <acceptance>. Run: <command>
```

Roles: `planning` `go` `node` `react` `swift` `data` `terraform` `aws` `review`. Coordination tasks bypass with `[skip-format-check]`.

**`task_completed_verify_gate.py`** blocks completion without a verification sentinel:

```bash
echo "<Run command> PASSED" > ~/.claude/logs/verified/<team>/task-<id>.verified
```

The sentinel attests that the agent actually ran the `Run:` command and it passed. It is **consumed on use**, so it cannot cover a second task.

**`teammate_idle_workcheck.py`** nudges an idle agent when unclaimed work matching its role remains.

Every decision is logged to `~/.claude/logs/team-hooks.jsonl`.

## The ideas that make it work

- **Groups are wide, barriers are rare.** Tasks in a group run in parallel and must not share files. A new group only where task B literally needs task A's output on disk.
- **Interface contracts are written before parallel work starts.** That is what lets the Go, React, and Swift agents build compatible code without coordinating.
- **Ground truth is the disk** — `tasks.md`, sentinels, `git diff`. Not completion messages, which are laggy and lossy.
- **Review is bounded.** Three cycles per scope, non-resetting. Cycle 3 is terminal and surfaces to a human, so a stuck scope cannot burn an afternoon in a fix-review loop.
- **Reviewers never fix.** A reviewer who patches the code has stopped reviewing it.

## Optional plugins

Not enabled in `settings.json` — a cloned repo referencing unregistered marketplaces errors at startup. Add what you want:

```bash
claude plugin marketplace add anthropics/claude-plugins-official
```

Useful here: `context7`, `feature-dev`, `frontend-design`, `security-guidance`, `pr-review-toolkit`, `aws-core`, `aws-serverless`, `deploy-on-aws`.

## Layout

```
.claude/
├── agents/{planning,execution,deployment,review}/   12 agents
├── rules/          protocol, testing, security, hygiene, stack standards
├── skills/         spec-workflow, git-workflow, documentation
├── commands/       brainstorm, plan-feature, run-build
├── hooks/          3 enforcement hooks + shared lib
├── specs/          <slug>/{spec,design,tasks,review}.md
└── settings.json
docs/               AGENT-ROSTER.md, WORKFLOW.md
CLAUDE.md           loaded every session
```

## Customizing

Personal settings go in `.claude/settings.local.json` (gitignored).

Adding an agent: create the file, then **add its role tag to `ROLE_TAGS` in `.claude/hooks/team_hook_lib.py`** and to the mapping in `teammate_idle_workcheck.py`. A tag the hook does not recognize will have all its tasks rejected at creation. Full checklist in [docs/AGENT-ROSTER.md](docs/AGENT-ROSTER.md#adding-an-agent).
