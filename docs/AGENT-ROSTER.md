# Agent Roster

Twelve agents in four groups. Who to call, and when.

## Planning

| Agent | Model | Owns | Call it when |
|---|---|---|---|
| `solution-architect` | Opus | `design.md`, `tasks.md` | A feature needs an architecture before anyone writes code. Group lead. |
| `requirements-analyst` | Opus | `spec.md` | Requirements are vague, contested, or exist only in someone's head. |
| `diagram-author` | Sonnet | `diagrams/` | The architecture is stable enough to draw, or a diagram has drifted. |
| `tradeoff-analyst` | Opus | `adr/` | A decision has real alternatives and reversing it later would be expensive. |
| `ux-designer` | Opus | `mockups/`, `wireframes/` | A feature has screens whose layout or flow is contested, or a tap-count/friction budget needs proving before code commits to it. Role tag `[design]`. |

**Never** write application code, tests, or Terraform.

## Execution

| Agent | Model | Tag | Stack |
|---|---|---|---|
| `backend-go` | Sonnet | `[go]` | Go — handlers, services, AWS SDK |
| `backend-node` | Sonnet | `[node]` | Node / TypeScript — APIs, Lambda, consumers |
| `web-react` | Sonnet | `[react]` | React — components, hooks, routing, client state |
| `ios-swift` | Sonnet | `[swift]` | Swift — SwiftUI, view models, networking |
| `data-engineer` | Sonnet | `[data]` | Schema, migrations, indexes, pipelines |

**Never** write Terraform, and never touch files outside their assigned task set.

## Deployment

| Agent | Model | Tag | Owns |
|---|---|---|---|
| `terraform-engineer` | Sonnet | `[terraform]` | `.tf` modules, environments, state, IAM, pipelines |
| `aws-architect` | Opus | `[aws]` | `sa-review.md` — Well-Architected review. **Review-only.** |

**Never** write application code. `aws-architect` never applies infrastructure — it finds problems and hands them to `terraform-engineer`.

## Review

| Agent | Model | Tag | Mode |
|---|---|---|---|
| `review-agent` | Opus | `[review]` | **Synthesizer**: sole author of `review.md`, owns the verdict. **Analyst**: one disjoint slice, messages findings, writes nothing. |

**Never** writes or fixes application code. A reviewer who patches the code has stopped reviewing it.

## Boundaries, and why they exist

| Boundary | Reason |
|---|---|
| Planning writes no code | Design decisions stay visible in documents instead of being buried in an implementation. |
| Execution agents own disjoint files | Two agents writing one file in parallel is the failure mode the whole model prevents. |
| Execution writes no Terraform | Infrastructure changes need the security review path in @.claude/rules/aws-security-guidelines.md. |
| `aws-architect` never applies | A reviewer who also authors the fix has stopped being a reviewer. |
| `review-agent` never fixes | Same reason — plus it would silently take ownership of another agent's file. |

## Choosing a model

Opus for judgment — architecture, trade-offs, requirements, review. Sonnet for execution against a written spec. If an agent's job is to *decide*, it is Opus; if its job is to *build what was decided*, it is Sonnet.

## Adding an agent

1. Create `.claude/agents/<group>/<name>.md` with frontmatter: `name` (matching the filename), `description` (say when to use it — this is how it gets selected), `model`, `color`.
2. Body sections: **Role** (owns / never), **Inputs**, **Standards** (`@`-reference the rules, do not restate them), **Implementation**, **Verification** (the exact `Run:` command), **Handoff**.
3. Add its role tag to `ROLE_TAGS` in `.claude/hooks/team_hook_lib.py` and to the mapping in `teammate_idle_workcheck.py`.
4. Add it to this roster, to `CLAUDE.md`, and to the table in `.claude/commands/run-build.md`.

Step 3 is the one people forget — a new role tag that the hook does not recognize will have all its tasks rejected at creation.
