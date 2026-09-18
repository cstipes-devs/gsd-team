# Execution Hygiene

Agents run unattended. A command that stops for input stops the whole team.

## Non-interactive, always

Every command must terminate without a human. Known offenders and their fixes:

| Tool | Use |
|---|---|
| `terraform` | `TF_INPUT=0`, `-input=false`, `-auto-approve` (dev only, per security rules) |
| `npm` / `npx` | `npm ci` over `npm install`; `--yes` on `npx` |
| `git` | never `-i`; `GIT_TERMINAL_PROMPT=0`; no commands that open `$EDITOR` |
| `apt` / `brew` | `-y`; prefer not installing system packages at all |
| `aws` | `--no-cli-pager`, `--output json` |
| `gh` | `--yes` where offered |
| pagers | `PAGER=cat`, or pipe through `| cat` |

If a command might prompt and you cannot suppress it, do not run it — report the need to the lead instead.

## Timeouts and long-running work

- Anything that could exceed ~2 minutes gets an explicit timeout or runs in the background.
- **Never start a foreground server and wait on it.** Background it, poll for readiness, then proceed.
- Poll with a bounded loop and a failure exit. No unbounded `while true`.

## Dependency isolation

- Install into the project, never globally. No `npm i -g`, no `pip install` outside a venv, no `go install` into a shared GOPATH for project deps.
- Respect the lockfile. `npm ci`, `go mod download`, `swift package resolve` — do not silently upgrade versions to make an error go away.
- Adding a dependency is a design decision. If the task did not call for it, ask before adding it.

## Filesystem discipline

- **Write only to the files your task assigned.** Verify with `git diff --name-only` before completing.
- Temporary files go in the session scratchpad, never in the repo and never in `/tmp` directly.
- Never `rm -rf` a path you built by string interpolation without printing it first.

## Output discipline

- Pipe verbose commands through `tail` or `grep` rather than dumping thousands of lines.
- When reporting a failure, include the actual error text — not "the tests failed."
- Check exit codes. A command that printed something reassuring and exited non-zero still failed.
