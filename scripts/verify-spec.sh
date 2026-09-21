#!/usr/bin/env bash
# Audit a spec directory's tasks.md against the verification gate.
#
# Standalone: needs no Copilot, no Claude, no network. Use it as a CI check,
# as the backstop when a patch-style edit slips past the preToolUse hook, and
# as the thing you run before believing a build is green.
#
#   scripts/verify-spec.sh <slug> [--specs-dir DIR]
#
# Exit 0 when every completed task is attested and every task line is
# well-formed. Exit 1 otherwise, naming each problem.

set -uo pipefail

SLUG=""
SPECS_DIR=".claude/specs"

while [ $# -gt 0 ]; do
  case "$1" in
    --specs-dir) SPECS_DIR="$2"; shift 2 ;;
    -h|--help)   sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           SLUG="$1"; shift ;;
  esac
done

if [ -z "$SLUG" ]; then
  echo "usage: $0 <slug> [--specs-dir DIR]" >&2
  exit 2
fi

TASKS="$SPECS_DIR/$SLUG/tasks.md"
if [ ! -f "$TASKS" ]; then
  echo "error: no tasks.md at $TASKS" >&2
  exit 2
fi

HOOKS_DIR="$(cd "$(dirname "$0")/copilot_hooks" && pwd)"

python3 - "$TASKS" "$SLUG" "$HOOKS_DIR" <<'PY'
import os, sys

tasks_path, slug, hooks_dir = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, hooks_dir)
import gsd_hook_lib as lib

content = open(tasks_path, encoding="utf-8").read()

malformed, unattested, ok, skipped = [], [], 0, 0

for lineno, checked, body in lib.iter_task_lines(content):
    if lib.SKIP_MARKER in body.lower():
        skipped += 1
        continue

    if not lib.TASK_RE.match(body):
        malformed.append((lineno, body))
        continue

    if not checked:
        continue

    tid = lib.task_id(body)
    sentinel = lib.sentinel_path(slug, tid)
    consumed = False

    # A consumed sentinel is still proof: the gate logs it on the way through.
    try:
        with open(lib.LOG_PATH, encoding="utf-8") as fh:
            for line in fh:
                if '"consumed"' in line and tid in line and slug in line:
                    consumed = True
                    break
    except Exception:
        pass

    if os.path.isfile(sentinel) or consumed:
        ok += 1
    else:
        unattested.append((lineno, tid, body))

print(f"spec: {slug}   tasks.md: {tasks_path}")
print(f"  verified complete : {ok}")
print(f"  skip-format-check : {skipped}")
print(f"  malformed         : {len(malformed)}")
print(f"  unattested [x]    : {len(unattested)}")

if malformed:
    print("\nMALFORMED TASK LINES")
    for lineno, body in malformed:
        print(f"  line {lineno}: {body[:110]}")

if unattested:
    print("\nCOMPLETED WITHOUT A VERIFICATION SENTINEL")
    print("  These are marked [x] but nothing attests their Run: command passed.")
    for lineno, tid, body in unattested:
        print(f"  line {lineno} [{tid}]: {body.split('|')[0].strip()[:90]}")

sys.exit(1 if (malformed or unattested) else 0)
PY
