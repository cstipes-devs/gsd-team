# GSD Team on GitHub Copilot CLI

This branch (`copilot-cli`) runs the same 13-agent team under [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/overview) instead of Claude Code.

It is **additive**. Nothing under `.claude/` is modified, so one checkout serves both toolchains and the standards in `.claude/rules/` exist in exactly one copy.

> **Status: the enforcement layer is tested offline; the live integration is not.**
> Every hook rule, the task-id derivation, and the audit CLI are covered by tests
> that run without Copilot installed. Nobody has yet run this against a real
> Copilot CLI session. See *Unverified* at the bottom.

---

## Install

```bash
git clone -b copilot-cli https://github.com/cstipes-devs/gsd-team.git
cd gsd-team
copilot
```

Into an existing project:

```bash
cp -r gsd-team/.github/agents  .github/
cp -r gsd-team/.github/skills  .github/
cp -r gsd-team/.github/hooks   .github/
cp -r gsd-team/.github/prompts .github/
cp -r gsd-team/.claude/rules   .claude/     # the shared standards
cp -r gsd-team/scripts         .
cp gsd-team/.github/copilot-instructions.md .github/
```

Verify:

```bash
# Enforcement is live (should print a deny and exit 2)
printf '%s' '{"toolName":"write","toolArgs":{"path":"specs/x/tasks.md","content":"- [ ] nope"}}' \
  | python3 scripts/copilot_hooks/pre_tool_use_gate.py; echo "exit=$?"
```

In an interactive session, `/agent` should list all 13.

---

## What maps to what

| Claude Code | Copilot CLI | Status |
|---|---|---|
| `.claude/agents/<group>/<n>.md` | `.github/agents/<n>.agent.md` | **Ported** — flat, group kept in `description` |
| Frontmatter `model: opus\|sonnet` | *(dropped)* | Claude model ids don't resolve; a comment records the intended tier |
| `.claude/skills/<n>/SKILL.md` | `.github/skills/<n>/SKILL.md` | **Ported** — same convention |
| `.claude/rules/*.md` | *(referenced, not copied)* | **Shared** — one copy for both toolchains |
| `@.claude/...` includes | `@` relative includes | **Works** — Copilot supports nested `@` includes |
| Slash commands | `.github/prompts/*.md` | **Ported** — run via `--prompt` or paste |
| Hook `TaskCreated` | `preToolUse` on a `tasks.md` write | **Reconstructed** |
| Hook `TaskCompleted` | `preToolUse` denying an unattested `[x]` | **Reconstructed** |
| Hook `TeammateIdle` | — | **Lost** — no idle event exists |
| `TaskUpdate` / `TaskList` / `TaskGet` | — | **Lost** — no shared task state |
| `SendMessage` between agents | — | **Lost** — subagents have isolated contexts |
| Worker pools self-claiming | `/fleet` orchestration | **Rewritten** |

---

## How enforcement works here

Claude Code fires hooks on task lifecycle *events*. Copilot has no task lifecycle, so both rules bind to the **file write that touches `tasks.md`**:

```
preToolUse  →  matcher filters to write-like tools
            →  is the target a specs/*/tasks.md?  no → allow
            →  Rule A: every task line matches the format?  no → DENY
            →  Rule B: any line newly [x] without a sentinel?  yes → DENY
            →  consume the sentinels, allow
```

A denial is both `{"permissionDecision":"deny","permissionDecisionReason":"..."}` on stdout **and** exit code 2. Exit 2 denies unconditionally in Copilot, so a malformed stdout cannot turn a deny into an allow.

### The fail-open inversion — important if you modify the hooks

Claude Code treats a crashed hook as *allow*. **Copilot does the opposite: a `preToolUse` hook that crashes, times out, or exits non-zero denies the tool call.**

So every path in `pre_tool_use_gate.py` ends in an explicit `allow()` — printing `{}` and exiting 0. If you edit these hooks, preserve that. A bug that blocks every file write is far worse than one that lets a task through.

### Task identity — the fragile part

Claude Code supplies a `task_id`. Copilot does not, so identity is **derived from the task line**: the first 12 hex of SHA-256 over the normalized `[role] description | files` prefix.

The acceptance clause, the `Run:` command, the checkbox state, and any trailing `> Done.` note are excluded — so marking a task complete does not change its id.

**The consequence:** editing a task's role, description, or file list **changes its id and orphans any sentinel already written for it.** Re-derive and rewrite the sentinel after editing those fields. This is the weakest joint in the port.

Compute an id:

```bash
python3 scripts/copilot_hooks/task_id.py '<the full task line>'
python3 scripts/copilot_hooks/task_id.py --path --slug my-feature '<the full task line>'
```

### Sentinels live outside both config dirs

`~/.gsd-team/logs/verified/<spec-slug>/task-<id>.verified`, with the audit log at `~/.gsd-team/logs/team-hooks.jsonl`. Neither toolchain owns the other's directory.

---

## `scripts/verify-spec.sh`

A standalone audit — no Copilot, no Claude, no network:

```bash
scripts/verify-spec.sh <slug>
scripts/verify-spec.sh <slug> --specs-dir path/to/specs
```

It reports, and exits non-zero on, any task that is `[x]` without an attestation, and any malformed task line. Use it:

- **In CI**, to catch a forged completion in a PR
- **As the backstop** when a patch-style edit slips past the hook (the hook can only diff whole-file writes reliably)
- **Before believing a build is green**

A sentinel that the hook already consumed still counts — the audit log records the consumption.

---

## What you give up

Three real losses, not worked around:

**No idle nudging.** Claude Code's `TeammateIdle` hook prompts an agent to self-claim remaining work. No equivalent event exists, so the lead must delegate explicitly.

**No inter-agent messaging.** Claude Code agents use `SendMessage` to clarify interfaces and report blockers to each other. Copilot subagents have isolated contexts. Coordination happens through files in the spec directory — which is why `design.md`'s interface contracts matter more here, not less.

**No shared task list.** Pools cannot self-claim from a queue. `/run-build` maps each task group to a `/fleet` invocation and re-reads `tasks.md` between groups. The 3-cycle review budget is tracked by the lead in prose, since no hook can count it.

None of these breaks the verification gate, which is the mechanism worth preserving.

---

## Unverified

Run these before treating the branch as production-ready:

1. `/agent` lists all 13 agents in an interactive session
2. `.github/hooks/gsd-team.json` actually registers — confirm the `matcher` matches Copilot's real write-tool names (it is validated against 12 plausible names offline, but not against the real ones)
3. `/plan-feature` produces spec, design, and tasks end to end
4. Marking a task `[x]` without a sentinel is **refused by Copilot**, with the reason surfaced to the user
5. `/fleet` parallelism behaves as `run-build.md` assumes

Item 2 is the most likely thing to be wrong. If the hook never fires, check the tool name Copilot reports in `~/.gsd-team/logs/team-hooks.jsonl` and widen the matcher.
