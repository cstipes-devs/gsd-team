---
name: git-workflow
description: Git conventions for this team — conventional commits, branch naming, what never gets committed, and non-interactive git usage for unattended agents. Use when committing, branching, or opening a pull request.
---

# Git Workflow

## Branches

```
feat/<slug>      new capability
fix/<slug>       bug fix
chore/<slug>     tooling, deps, config
docs/<slug>      documentation only
```

Slug matches the spec directory name where there is one, so `.claude/specs/order-submission/` → `feat/order-submission`.

**Never commit directly to the default branch.** If you are on it and need to commit, branch first.

## Commits

Conventional commits:

```
<type>(<scope>): <subject>

<body — why, not what>

<footer — refs, breaking changes>
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`.

- Subject in the imperative, lowercase, no trailing period, under ~72 characters. "add retry to order consumer", not "Added retry."
- The body explains **why**. The diff already shows what.
- Breaking changes get `BREAKING CHANGE:` in the footer.
- Reference the task or spec: `Refs: specs/order-submission/tasks.md#g2-t3`.

**One logical change per commit.** A commit that fixes a bug and reformats a file is two commits.

## Never commit

- Secrets, credentials, tokens, private keys — in any file, including `.tfvars` and `.env`
- Terraform state (`*.tfstate*`) — it contains plaintext secrets
- `node_modules/`, `.terraform/`, build output, `DerivedData/`
- `.claude/settings.local.json`
- Real user data in fixtures or seeds

If you discover a secret already committed: **stop, tell the user, and do not attempt history rewriting on your own.**

## Non-interactive

Per @.claude/rules/execution-hygiene.md, agents run unattended:

- Never `-i` — no `rebase -i`, no `add -i`
- `GIT_TERMINAL_PROMPT=0` so auth failures error instead of hanging
- No command that opens `$EDITOR` — always `-m` for messages
- `git --no-pager` or pipe through `cat`

## Before committing

```bash
git status
git diff --name-only     # only your assigned files should appear
```

An agent committing files outside its task assignment is a protocol violation, not a convenience.

## Pull requests

- Title is the conventional-commit subject for the change as a whole
- Body: what changed and why, the spec path, verification evidence (commands run and their results), and anything a reviewer should look at closely
- Never open or merge a PR unless the user asked for it

## Attribution

End PR descriptions with:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
