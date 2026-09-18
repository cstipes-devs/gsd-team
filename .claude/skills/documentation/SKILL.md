---
name: documentation
description: Technical writing standards for specs, designs, ADRs, READMEs, and API docs — structure, tone, and what makes a document useful to the agent or engineer who reads it next. Use when writing or revising any documentation in this repo.
---

# Documentation Standards

Everything here is written for **the agent or engineer who arrives with no context**. That reader cannot ask you a follow-up question. Write accordingly.

## Universal rules

- **Lead with the conclusion.** The first paragraph says what this is and why it exists. Background comes after, if at all.
- **Be specific.** "Fast" and "scalable" and "robust" carry no information. Numbers, thresholds, and named conditions do.
- **Write why, not what.** The code already shows what. Documentation earns its keep by capturing the reasoning that the code cannot express.
- **Cut every sentence that survives deletion.** Padding makes the important parts harder to find.
- **Say what is *not* true too** — non-goals, out of scope, known limitations. These prevent more wasted work than the positive statements do.
- Prefer a table to a list of parallel prose paragraphs. Prefer a short example to a long abstract description.
- Second person and active voice. "Run the migration," not "the migration should be run."
- Use fenced code blocks with a language tag. Every command must be copy-pasteable and correct.

## Per-document contracts

**`spec.md`** — problem, users, numbered requirements, testable acceptance criteria, non-functional requirements with numbers, explicit out-of-scope, open questions. Acceptance criteria must be assertions a test can make. No architecture.

**`design.md`** — architecture overview, component responsibilities, interface contracts precise enough for two parallel agents to build compatible code, data model, technology choices with reasons, **Security Considerations (mandatory)**, open questions. No implementation code.

**ADRs** — context, options at their strongest, comparison against *this system's* needs, decision with the decisive criterion, consequences including second-order effects and reversibility. Numbered, immutable once accepted; supersede rather than edit.

**`README.md`** — what this is, how to run it, how to test it, how it is laid out. A new engineer should get it running from the README alone without asking anyone. Keep it current; a stale README is worse than none.

**API docs** — every endpoint: method, path, auth, request schema, response schema, **every error case with its status code and body shape**. Error cases are what consumers actually need and are almost always what is missing.

## Code comments

- Comments explain **why**. Code that needs a *what* comment should be rewritten instead.
- Document public interfaces; internal helpers usually need nothing.
- **No commented-out code.** Git remembers it.
- No `TODO` without a linked task. An unlinked TODO is a lie about future work.
- A comment that contradicts the code is worse than no comment. If you change the code, change the comment.

## Diagrams

Per the `diagram-author` agent: Mermaid, one message per diagram, every edge labelled with what crosses it, node names identical to those in `design.md`. Each diagram file opens with one sentence saying what the reader should take away.

## Keeping docs true

Documentation is part of the change, not a follow-up. A task that alters behavior and leaves the docs describing the old behavior is incomplete — the stale doc will mislead someone with more confidence than no doc would have.
