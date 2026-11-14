"""Hackathon clock: current Central time, phase, and next deadline.

Team tooling, not project code. Shared by the hooks in this folder.
Uses a fixed UTC-6 offset (CST) because daylight saving ended Nov 1, 2026 and
Windows Python often lacks the tz database that zoneinfo needs.
"""
from datetime import datetime, timedelta, timezone

CT = timezone(timedelta(hours=-6), "CT")


def ct(day: int, hour: int, minute: int = 0) -> datetime:
    """A Central-time moment in November 2026."""
    return datetime(2026, 11, day, hour, minute, tzinfo=CT)


KICKOFF = ct(13, 23)
GATE = ct(14, 18)
FREEZE = ct(15, 13)
SUBMIT_TARGET = ct(15, 21)
HARD_CLOSE = ct(15, 22, 59)

# (start, name, what to do). Each phase runs until the next one starts.
PHASES = [
    (ct(1, 0), "Pre-kickoff", "Docs, accounts and setup only. NO project code (AGENTS.md §0.1)."),
    (KICKOFF, "P0 Lock", "Paste the brief into docs/BRIEF.md, run /kickoff, lock docs/DECISIONS.md by 12 AM."),
    (ct(14, 0), "P1 Skeleton", "Walking skeleton end to end with stubs; call each real API once and cache it."),
    (ct(14, 2), "Sleep", "Sleep. Q&A is 20% of finals and needs rested brains."),
    (ct(14, 9), "P2 Build", "Replace stubs one at a time, smoke test after each. Evaluator builds the test set."),
    (GATE, "P3 Measure", "GATE passed: full flow must work. First eval run: baseline vs ours, failure list."),
    (ct(14, 22), "Sleep", "Sleep."),
    (ct(15, 9), "P4 Harden", "Fix the top failure modes, rerun eval. Stretch only if everything is green."),
    (FREEZE, "P5 Story", "FREEZE: no new features or dependencies. Write-up, video, README."),
    (ct(15, 17), "P6 Ship", "Run /ship-check, fresh-clone test, rehearse Q&A. Submit by 9 PM CT."),
    (SUBMIT_TARGET, "SUBMIT NOW", "Past the 9 PM target. Submit immediately; hard close 10:59 PM CT."),
    (HARD_CLOSE, "Closed", "Submissions closed. Prep the 5-minute finals demo (Nov 21) and Q&A."),
]

DEADLINES = [
    (KICKOFF, "Kickoff (code allowed from here)"),
    (ct(14, 0), "Idea + roles locked"),
    (GATE, "GATE: full demo flow works"),
    (FREEZE, "FREEZE: no new features"),
    (SUBMIT_TARGET, "Our submit target"),
    (HARD_CLOSE, "Hard close (late = zero)"),
]


def now_ct() -> datetime:
    """Current time in Central time."""
    return datetime.now(CT)


def phase(now: datetime) -> tuple:
    """Return (name, what to do) for the phase containing `now`."""
    current = PHASES[0]
    for entry in PHASES:
        if now >= entry[0]:
            current = entry
    return current[1], current[2]


def next_deadline(now: datetime):
    """Return (label, time left as text) for the next deadline, or None."""
    for when, label in DEADLINES:
        if when > now:
            mins = int((when - now).total_seconds() // 60)
            return label, f"{mins // 60}h {mins % 60:02d}m"
    return None


def before_kickoff(now: datetime) -> bool:
    """True while project code is still forbidden."""
    return now < KICKOFF


def after_freeze(now: datetime) -> bool:
    """True once the feature freeze is in effect."""
    return now >= FREEZE
