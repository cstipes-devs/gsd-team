# /plan-feature (Copilot CLI)

Run with: `copilot --prompt "$(cat .github/prompts/plan-feature.md)"` or paste into an interactive session.

---


Run the planning group for: **<your input>**

Resolve the spec directory to `.claude/specs/<slug>/`, creating it if needed. If `requirements.md` already exists there from `/brainstorm`, use it as input.

## Sequence

Run these in order — each depends on the one before.

**1. `requirements-analyst` → `spec.md`**  
`copilot --agent requirements-analyst --prompt "..."`, or "Use the requirements-analyst agent to ..."
Numbered requirements and **testable acceptance criteria**. These become T4 assertions later, so they must be written as assertions, not aspirations. If the request is too vague to specify, the analyst asks the user rather than guessing.

**2. `solution-architect` → `design.md`**
Architecture, component decomposition, interface contracts precise enough for parallel agents to build compatible code, data model, technology choices across Go / Node / React / Swift / Terraform, and a **mandatory Security Considerations section**.

**3. In parallel, once the design is stable:**
- `tradeoff-analyst` → `adr/` — only for decisions that are genuinely contested and consequential. Skip it if there are none; a directory of ceremonial ADRs hides the real ones.
- `diagram-author` → `diagrams/` — Mermaid. Only the diagrams that carry real information.
- `aws-architect` → `sa-review.md` — Well-Architected review, if the feature involves infrastructure.

**4. `solution-architect` → `tasks.md`**
The task breakdown. This determines how fast the build runs.

## tasks.md requirements

Per @.github/skills/spec-workflow/SKILL.md:

- **Groups wide, barriers few.** As many file-disjoint same-role tasks per group as possible. Create a new group *only* where task B literally needs task A's output on disk.
- **Front-load shared interfaces** so consumers fan out in parallel behind them.
- **Infrastructure before the code that runs on it.**
- **No two tasks in one group may write the same file.** This is the invariant everything else rests on.
- **Saturate both pools** — independent execution and deployment work goes in the *same* group.

Every task must match the enforced format (the `TaskCreated` hook rejects anything else):

```
[role] <verb> <what> | <file paths> | <acceptance>. Run: <command>
```

Roles: `planning` `go` `node` `react` `swift` `data` `terraform` `aws` `review`. The `Run:` command must be real and at the tier the acceptance criteria imply — see @.claude/rules/testing-standards.md.

## Output — the Handoff Package

Report back:

- Spec directory path
- One-paragraph architecture summary
- Group structure with task counts per role
- Confirmation that `design.md` contains its Security Considerations section
- Any open question that would block the build
- The `sa-review.md` verdict, if infrastructure was reviewed

Then stop. **Do not start building.** Offer:

> Next: run `.github/prompts/run-build.md` to execute the build-review loop.
