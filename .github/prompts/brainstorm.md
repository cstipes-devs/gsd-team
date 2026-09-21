# /brainstorm (Copilot CLI)

Run with: `copilot --prompt "$(cat .github/prompts/brainstorm.md)"` or paste into an interactive session.

---


Run a structured brainstorm for: **<your input>**

## How to run this

Ask the user clarifying questions — **up to 10, but stop as soon as you have enough**. Use direct questions to the user, batching related questions rather than asking one at a time. Cover the ground that actually changes the design:

1. **Problem** — what is broken or missing today, and for whom? Push past the proposed solution to the underlying need.
2. **Users** — who uses this, how often, in what context?
3. **Scope** — what is explicitly *not* in this? The out-of-scope answer prevents more rework than any other.
4. **Surfaces** — which of web (React), iOS (Swift), backend (Go / Node), and data are involved?
5. **Data** — what is stored, what is sensitive, what must be retained?
6. **Integrations** — which existing systems or third parties does this touch?
7. **Scale and performance** — how many users, how much data, what latency matters? Get numbers.
8. **Constraints** — deadlines, compliance, existing architecture that cannot change.
9. **Success** — how will we know this worked?

Where an answer is obvious from context or has a clear default, **take the default and state it as an assumption** rather than spending a question on it. The question budget is for the things that genuinely change what gets built.

## Output

Write `.claude/specs/<slug>/requirements.md` — pick a short kebab-case slug from the feature name.

```markdown
# <Feature> — Requirements

## Problem
## Users and context
## Desired outcome
## Scope
### In scope
### Explicitly out of scope
## Surfaces involved
web / iOS / backend / data / infrastructure — and why each
## Data and sensitivity
## Integrations
## Scale and performance
Numbers, not adjectives.
## Constraints
## Success criteria
## Assumptions taken
Defaults you applied without asking.
## Open questions
Still unresolved, with your recommendation for each.
```

This is **raw material, not a specification.** It feeds `requirements-analyst`, who turns it into `spec.md` with testable acceptance criteria.

## Then

Tell the user the file path and offer the next step:

> Next: `/plan-feature <slug>` to have the planning group turn this into spec, design, and tasks.
