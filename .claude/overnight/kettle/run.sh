#!/usr/bin/env bash
# Kettle runner (team tooling): stage 1 teardown -> stage 2 PRD -> stage 3 build. Local only, never pushes.
#   bash .claude/overnight/kettle/run.sh          # run all stages (skips finished ones)
#   bash .claude/overnight/kettle/run.sh status   # where is it?
set -u
ROOT=$(git rev-parse --show-toplevel) || exit 1
cd "$ROOT" || exit 1
STOP_AT=${STOP_AT:-1794754802}   # Sun Nov 15 2026 9:00 AM CT
MODEL=${MODEL:-opus}; EFFORT=${EFFORT:-high}
ST=.overnight/kettle; LOGS=$ST/logs; K=.claude/overnight/kettle
mkdir -p "$LOGS" "$ST/jobs"
say() { printf '[%s] %s\n' "$(TZ=America/Chicago date '+%a %I:%M %p CT')" "$*" | tee -a "$LOGS/run.log"; }
now() { date +%s; }

status() {
  for f in TEARDOWN_DONE PRD_DONE BUILD_DONE; do [ -f $ST/$f ] && echo "$f: yes" || echo "$f: not yet"; done
  [ -f $ST/STATE.md ] && { echo "--- STATE.md (tail)"; tail -20 $ST/STATE.md; }
  echo "--- run.log"; tail -6 "$LOGS/run.log" 2>/dev/null
  git log --oneline | head -6
}

run_claude() {  # $1 log name, $2 prompt
  claude -p "$2" --model "$MODEL" --effort "$EFFORT" --fallback-model sonnet \
    --permission-mode auto --output-format stream-json --verbose \
    --disallowedTools "Bash(git push)" "Bash(git push *)" "Bash(gh pr create *)" \
    >> "$LOGS/$1.jsonl" 2>> "$LOGS/$1.err"
}

stage() {  # $1 name, $2 prompt, $3 done file, $4 max attempts
  local a=1
  while [ ! -f "$3" ] && [ "$(now)" -lt "$STOP_AT" ] && [ "$a" -le "$4" ]; do
    say "$1: attempt $a on $MODEL ($EFFORT)"
    run_claude "$1-$a" "$2"; rc=$?
    [ -f "$3" ] && break
    say "$1: ended (exit $rc) before finishing; last error: $(tail -1 "$LOGS/$1-$a.err" 2>/dev/null | cut -c1-160)"
    a=$((a + 1)); say "$1: waiting 10 min before retry (usage limit may need to reset)"; sleep 600
  done
  [ -f "$3" ]
}

main() {
  if command -v caffeinate >/dev/null && [ -z "${CAFFEINATED:-}" ]; then CAFFEINATED=1 exec caffeinate -dimsu bash "$0" "$@"; fi
  [ "$(git rev-parse --abbrev-ref HEAD)" = kettle ] || git switch kettle >> "$LOGS/run.log" 2>&1 || { say "Not on branch kettle; stopping."; exit 1; }
  say "Kettle run starting on branch kettle. Model $MODEL, effort $EFFORT. Nothing will be pushed."
  stage k1-teardown "Read .claude/overnight/kettle/k1-teardown.md in full and carry it out exactly. You are unattended; never wait for a human." $ST/TEARDOWN_DONE 4 \
    || { say "Stage 1 did not finish. Stopping."; exit 1; }
  say "Stage 1 done: $(head -c 300 $ST/TEARDOWN_DONE | tr '\n' ' ')"
  stage k2-prd "Read .claude/overnight/kettle/k2-prd.md in full and carry it out exactly. You are unattended; never wait for a human." $ST/PRD_DONE 4 \
    || { say "Stage 2 did not finish. Stopping."; exit 1; }
  say "Stage 2 done: $(head -c 300 $ST/PRD_DONE | tr '\n' ' ')"
  stage k3-build "/goal $(cat $K/goal.txt)" $ST/BUILD_DONE 40 \
    && say "Stage 3 done. Read docs/MORNING-BRIEF.md." \
    || say "Stage 3 stopped before finishing. Read $ST/STATE.md."
  status
}

case "${1:-run}" in status) status ;; run) main "$@" ;; *) echo "usage: run.sh [run|status]"; exit 2 ;; esac
