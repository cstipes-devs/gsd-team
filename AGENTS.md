# GSD Team

A spec-driven multi-agent development team. This repo supports two toolchains from one checkout:

- **GitHub Copilot CLI** — agents in `.github/agents/`, enforcement in `scripts/copilot_hooks/`
- **Claude Code** — agents in `.claude/agents/`, enforcement in `.claude/hooks/`

Both share the same standards in `.claude/rules/` and write specs to `.claude/specs/<slug>/`.

@.github/copilot-instructions.md
