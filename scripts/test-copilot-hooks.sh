#!/usr/bin/env bash
# Offline test suite for the Copilot CLI enforcement layer.
# Needs no Copilot, no network. Run from the repo root.

set -uo pipefail
cd "$(dirname "$0")/.."

GATE=scripts/copilot_hooks/pre_tool_use_gate.py
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
SPECS="$TMP/specs"; mkdir -p "$SPECS/demo"
export HOME="$TMP/home"; mkdir -p "$HOME"   # isolate sentinels from the real ones

pass=0; fail=0
ok(){ pass=$((pass+1)); printf '  \033[32mPASS\033[0m  %s\n' "$1"; }
no(){ fail=$((fail+1)); printf '  \033[31mFAIL\033[0m  %s (%s)\n' "$1" "$2"; }

payload(){ python3 -c "
import json,sys
print(json.dumps({'sessionId':'s','timestamp':1,'cwd':'/tmp',
                  'toolName':sys.argv[1],
                  'toolArgs':{'path':sys.argv[2],'content':sys.argv[3]}}))
" "$1" "$2" "$3"; }

# expect <label> <want_exit> <tool> <path> <content>
expect(){ local label="$1" want="$2" tool="$3" path="$4" content="$5"
  payload "$tool" "$path" "$content" | python3 "$GATE" >"$TMP/out" 2>"$TMP/err"
  local got=$?
  [ "$got" = "$want" ] && ok "$label" || no "$label" "exit=$got want=$want"
}

T='- [ ] [go] Add retry logic | internal/retry.go | retries 3x. Run: go test ./internal/...'
TX=${T/- \[ \]/- [x]}
TASKS="$SPECS/demo/tasks.md"

echo "== fail-open (a crashed preToolUse hook DENIES in Copilot) =="
echo 'not json'  | python3 "$GATE" >"$TMP/o" 2>&1; [ $? = 0 ] && [ "$(cat $TMP/o)" = "{}" ] && ok "malformed json allows" || no "malformed json allows" "exit/stdout"
echo ''          | python3 "$GATE" >"$TMP/o" 2>&1; [ $? = 0 ] && ok "empty stdin allows" || no "empty stdin allows" "nonzero"
expect "unrelated file untouched" 0 write "/src/main.go" "package main"

echo
echo "== Rule A: task format =="
expect "valid task line"        0 write "$TASKS" "## G1
$T"
expect "no role tag denied"     2 write "$TASKS" "- [ ] just do the thing"
expect "bad role tag denied"    2 write "$TASKS" "- [ ] [coding] x | a.go | works. Run: go test"
expect "missing Run: denied"    2 write "$TASKS" "- [ ] [go] x | a.go | works."
expect "skip-format-check ok"   0 write "$TASKS" "- [ ] [skip-format-check] coordinate"
expect "realistic file ok"      0 write "$TASKS" "## G1
- [ ] [terraform] Queue | infra/q.tf | exists. Run: terraform validate
- [ ] [data] Migration | db/1.sql | applies. Run: migrate up
## G2
- [ ] [go] Handler | internal/h.go | 201. Run: go test ./...
- [ ] [swift] Screen | Sources/V.swift | offline. Run: swift test"

echo
echo "== Rule B: verification gate =="
printf '## G1\n%s\n' "$T" > "$TASKS"
expect "[x] without sentinel denied" 2 write "$TASKS" "## G1
$TX"

SENT=$(python3 scripts/copilot_hooks/task_id.py --path --slug demo "$T")
mkdir -p "$(dirname "$SENT")"; echo "go test PASSED" > "$SENT"
expect "[x] with sentinel allowed"   0 write "$TASKS" "## G1
$TX"
[ -f "$SENT" ] && no "sentinel consumed" "still present" || ok "sentinel consumed"

printf '## G1\n%s\n' "$T" > "$TASKS"
expect "sentinel cannot be reused"   2 write "$TASKS" "## G1
$TX"

echo
echo "== matcher compiles the way Copilot compiles it =="
python3 - <<'PY'
import json,re,sys
pat=json.load(open('.github/hooks/gsd-team.json'))['hooks']['preToolUse'][0]['matcher']
try: rx=re.compile('^(?:'+pat+')$')
except re.error as e: print(f'  \033[31mFAIL\033[0m  matcher compiles ({e})'); sys.exit(1)
hit=['write','Write','edit','create_file','str_replace_editor','apply_patch','multi_edit','write_file']
miss=['bash','read','shell','search','grep','fetch']
bad=[t for t in hit if not rx.match(t)]+[t for t in miss if rx.match(t)]
print('  \033[32mPASS\033[0m  matcher: 8 write tools match, 6 read tools skip' if not bad
      else f'  \033[31mFAIL\033[0m  matcher wrong for {bad}')
sys.exit(1 if bad else 0)
PY
[ $? = 0 ] && pass=$((pass+1)) || fail=$((fail+1))

echo
echo "== agents converted cleanly =="
python3 - <<'PY'
import glob,re,os,sys
bad=[]
files=sorted(glob.glob('.github/agents/*.agent.md'))
for p in files:
    t=open(p,encoding='utf-8').read()
    m=re.match(r'^---\n(.*?)\n---\n(.*)$',t,re.S)
    if not m: bad.append((p,'no frontmatter')); continue
    f=dict(re.findall(r'^([\w-]+):\s*(.+)$',m.group(1),re.M)); body=m.group(2)
    stem=os.path.basename(p).replace('.agent.md','')
    if f.get('name')!=stem: bad.append((p,'name mismatch'))
    if 'description' not in f: bad.append((p,'no description'))
    if f.get('include-custom-instructions')!='true': bad.append((p,'no include flag'))
    if f.get('model') in ('opus','sonnet'): bad.append((p,'Claude model id'))
    for tok in ('TaskUpdate','TaskList','TaskGet','SendMessage'):
        if tok in body: bad.append((p,f'leftover {tok}'))
    if '~/.claude/logs' in body: bad.append((p,'old sentinel path'))
for p,why in bad: print(f'  \033[31mFAIL\033[0m  {os.path.basename(p)}: {why}')
if not bad: print(f'  \033[32mPASS\033[0m  {len(files)} agents valid, no Claude-only references')
sys.exit(1 if bad else 0)
PY
[ $? = 0 ] && pass=$((pass+1)) || fail=$((fail+1))

echo
echo "== verify-spec.sh =="
V="$TMP/v/specs/demo"; mkdir -p "$V"
cat > "$V/tasks.md" <<EOF
- [x] [go] Honest | internal/a.go | works. Run: go test ./...
- [x] [go] Forged | internal/b.go | works. Run: go test ./...
EOF
H='[go] Honest | internal/a.go | works. Run: go test ./...'
HS=$(python3 scripts/copilot_hooks/task_id.py --path --slug demo "$H")
mkdir -p "$(dirname "$HS")"; echo PASSED > "$HS"
./scripts/verify-spec.sh demo --specs-dir "$TMP/v/specs" >"$TMP/v.out" 2>&1
[ $? = 1 ] && grep -q Forged "$TMP/v.out" && ok "catches forged completion" || no "catches forged completion" "see $TMP/v.out"

C="$TMP/c/specs/clean"; mkdir -p "$C"
echo "- [ ] [go] Todo | internal/a.go | works. Run: go test ./..." > "$C/tasks.md"
./scripts/verify-spec.sh clean --specs-dir "$TMP/c/specs" >/dev/null 2>&1
[ $? = 0 ] && ok "clean spec exits 0" || no "clean spec exits 0" "nonzero"

echo
printf '\033[1m%d passed, %d failed\033[0m\n' "$pass" "$fail"
exit $((fail > 0))
