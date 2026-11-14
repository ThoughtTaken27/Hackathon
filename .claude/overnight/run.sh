#!/usr/bin/env bash
# Overnight kickoff runner (team tooling, not project code).
# Runs on the repo owner's own computer. Waits for kickoff (Fri Nov 13, 11:00 PM CT),
# then runs Phase A (brief -> research -> PRD) and Phase B (build, with /goal),
# both unattended in Claude Code. Everything stays local: nothing is pushed.
#
#   bash .claude/overnight/run.sh check    # preflight only: is this machine ready?
#   bash .claude/overnight/run.sh          # the real run (start it before 11 PM, leave it open)
#   bash .claude/overnight/run.sh status   # where is it now?
#
# Settings (environment variables):
#   RESEARCH_MODEL=opus  BUILD_MODEL=opus  EFFORT=high   models and effort level
#   STOP_AT=1794666600   epoch seconds to stop retrying (default Sat 8:30 AM CT)
#   SKIP_WAIT=1          start now instead of waiting for 11 PM (testing only)
set -u

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "Run this inside the Hackathon repo."; exit 1; }
cd "$ROOT" || exit 1

KICKOFF=${KICKOFF:-1794632400}      # 2026-11-13 23:00 CT
STOP_AT=${STOP_AT:-1794666600}      # 2026-11-14 08:30 CT
RESEARCH_MODEL=${RESEARCH_MODEL:-opus}
BUILD_MODEL=${BUILD_MODEL:-opus}
EFFORT=${EFFORT:-high}
STATE=.overnight
LOGS=$STATE/logs
BRANCH=overnight/build
mkdir -p "$LOGS"

say()  { printf '[%s] %s\n' "$(TZ=America/Chicago date '+%a %I:%M %p CT')" "$*" | tee -a "$LOGS/run.log"; }
now()  { date +%s; }
have() { command -v "$1" >/dev/null 2>&1; }

check() {
  local ok=0
  echo "Preflight for the overnight run"
  if have claude; then echo "  ok   Claude Code $(claude --version 2>/dev/null | head -1)"; else echo "  FAIL Claude Code not found (install it first)"; ok=1; fi
  if have python3 || have python; then echo "  ok   Python found"; else echo "  FAIL Python not found"; ok=1; fi
  if have node; then echo "  ok   Node $(node --version) (needed for REA)"; else echo "  warn Node not found: REA tools unavailable"; fi
  if have caffeinate; then echo "  ok   caffeinate found: the Mac will be kept awake"; else echo "  warn caffeinate not found: make sure this computer cannot sleep tonight"; fi
  if [ -d "$HOME/.claude/skills/reverse-engineer-anything" ]; then echo "  ok   REA skill installed"; else echo "  warn REA not set up. Run:  npx -y rea-agents@latest setup --client claude_code"; fi
  if have aside || [ -d "$HOME/.aside/cli" ]; then echo "  ok   Aside CLI found (used for X/Reddit research)"; else echo "  warn Aside CLI not found: X/Reddit research falls back to web search"; fi
  if [ -f .env ]; then echo "  ok   .env exists (Claude cannot read it; the app can)"; else echo "  warn no .env: the build will use a no-key fallback for any LLM step. Copy .env.example to .env and add a key to avoid that"; fi
  if have claude; then
    echo "  ...  testing an unattended Claude call (auto permission mode)"
    if out=$(claude -p "Reply with exactly: READY" --model haiku --permission-mode auto 2>&1) && printf '%s' "$out" | grep -q READY; then
      echo "  ok   unattended Claude call works"
    else
      echo "  FAIL unattended Claude call failed:"; printf '%s\n' "$out" | tail -3 | sed 's/^/       /'; ok=1
    fi
  fi
  echo "  note branch: $(git rev-parse --abbrev-ref HEAD), uncommitted files: $(git status --porcelain | wc -l | tr -d ' ')"
  [ "$ok" = 0 ] && echo "Ready." || echo "Fix the FAIL lines before tonight."
  return "$ok"
}

status() {
  echo "Now: $(TZ=America/Chicago date '+%a %I:%M %p CT')"
  [ -f $STATE/PRD_DONE ] && echo "Phase A: done -> $(head -c 300 $STATE/PRD_DONE)" || echo "Phase A: not done"
  [ -f $STATE/BUILD_DONE ] && echo "Phase B: done" || echo "Phase B: not done"
  [ -f $STATE/STATE.md ] && { echo "--- STATE.md"; tail -25 $STATE/STATE.md; }
  echo "--- last log lines"; tail -5 "$LOGS/run.log" 2>/dev/null
  git log --oneline 2>/dev/null | head -8
}

# One unattended Claude run. $1 = log name, $2 = model, $3 = prompt.
run_claude() {
  local name=$1 model=$2 prompt=$3 fallback=""
  [ "$model" != "sonnet" ] && fallback="--fallback-model sonnet"
  # shellcheck disable=SC2086  (fallback is two words on purpose; works on macOS bash 3.2)
  claude -p "$prompt" \
    --model "$model" --effort "$EFFORT" $fallback \
    --permission-mode auto \
    --output-format stream-json --verbose \
    --disallowedTools "Bash(git push)" "Bash(git push *)" "Bash(gh pr create *)" \
    >> "$LOGS/$name.jsonl" 2>> "$LOGS/$name.err"
}

# Repeat a phase until its done-file exists. Handles usage limits by waiting and retrying.
phase() {
  local name=$1 model=$2 prompt=$3 done_file=$4 max=$5 attempt=1
  while [ ! -f "$done_file" ] && [ "$(now)" -lt "$STOP_AT" ] && [ "$attempt" -le "$max" ]; do
    say "$name: attempt $attempt on $model ($EFFORT)"
    run_claude "$name-$attempt" "$model" "$prompt"; rc=$?
    [ -f "$done_file" ] && break
    say "$name: session ended (exit $rc) before finishing; last error: $(tail -1 "$LOGS/$name-$attempt.err" 2>/dev/null | cut -c1-160)"
    attempt=$((attempt + 1))
    say "$name: waiting 10 minutes before retrying (a usage limit may need to reset)"
    sleep 600
  done
  [ -f "$done_file" ]
}

main() {
  # Keep the Mac awake for the whole run.
  if have caffeinate && [ -z "${CAFFEINATED:-}" ]; then CAFFEINATED=1 exec caffeinate -dimsu bash "$0" "$@"; fi

  check || { say "Preflight failed. Not starting."; exit 1; }
  say "Overnight run starting. Research: $RESEARCH_MODEL, build: $BUILD_MODEL, effort: $EFFORT. Nothing will be pushed."

  # Work on a local branch so main stays untouched until a human reviews it.
  git pull --rebase origin main >> "$LOGS/run.log" 2>&1 || say "Could not pull main (continuing with the local copy)."
  git switch "$BRANCH" >> "$LOGS/run.log" 2>&1 || git switch -c "$BRANCH" >> "$LOGS/run.log" 2>&1
  say "On local branch $(git rev-parse --abbrev-ref HEAD)."

  if [ -z "${SKIP_WAIT:-}" ]; then
    while [ "$(now)" -lt "$KICKOFF" ]; do
      left=$(( (KICKOFF - $(now)) / 60 )); say "Waiting for kickoff: $left min left. Leave this window open."
      sleep $(( left > 5 ? 300 : 30 ))
    done
  fi

  # Brief intake: paste it if you're here; otherwise Claude looks in Gmail.
  if [ ! -s $STATE/brief.txt ] && [ -t 0 ]; then
    echo; echo ">>> Kickoff. Copy the full brief email (all four tracks) to the clipboard, then press Enter."
    echo ">>> Or wait 10 minutes and Claude will look for it in Gmail on its own."
    if read -r -t 600 _; then
      if have pbpaste; then pbpaste > $STATE/brief.txt; else echo "Paste the brief, then press Ctrl-D:"; cat > $STATE/brief.txt; fi
      say "Brief saved from the clipboard ($(wc -c < $STATE/brief.txt | tr -d ' ') bytes)."
    else
      say "No paste. Claude will look for the brief itself."
    fi
  fi

  phase "phase-a" "$RESEARCH_MODEL" "Read .claude/overnight/phase-a.md in full and carry it out exactly. You are unattended; never wait for a human." $STATE/PRD_DONE 4 \
    || { say "Phase A did not finish. See $LOGS and $STATE/STATE.md. Stopping."; exit 1; }
  say "Phase A done: $(head -c 200 $STATE/PRD_DONE)"

  phase "phase-b" "$BUILD_MODEL" "/goal $(cat .claude/overnight/goal.txt)" $STATE/BUILD_DONE 40 \
    && say "Phase B done. Read docs/MORNING-BRIEF.md." \
    || say "Phase B stopped before finishing. Read $STATE/STATE.md and docs/MORNING-BRIEF.md (if present)."
  status
}

case "${1:-run}" in
  check)  check ;;
  status) status ;;
  run)    main "$@" ;;
  *)      echo "Usage: bash .claude/overnight/run.sh [check|run|status]"; exit 2 ;;
esac
