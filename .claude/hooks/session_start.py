"""SessionStart hook: tell Claude the time, phase, next deadline and git state.

Team tooling, not project code. Its stdout is added to Claude's context, so every
session starts knowing where the team is on the clock. It never fails a session.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clock  # noqa: E402

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def git(*args: str, timeout: int = 5) -> str:
    """Run a git command in the repo; return stdout, or '' on any failure."""
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def git_lines() -> list:
    """Short description of branch, local changes and distance from origin/main."""
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    lines = [f"Branch: {branch}"]
    dirty = git("status", "--porcelain")
    if dirty:
        lines.append(f"Uncommitted files: {len(dirty.splitlines())}")
    git("fetch", "--quiet", "origin", "main", timeout=8)
    counts = git("rev-list", "--left-right", "--count", "HEAD...origin/main")
    if counts:
        ahead, behind = counts.split()
        if behind != "0":
            lines.append(f"origin/main has {behind} commit(s) you don't have: run `git pull --rebase origin main` before working.")
        if ahead != "0" and branch != "main":
            lines.append(f"This branch is {ahead} commit(s) ahead of main: merge soon (small PRs, often).")
    elif branch != "unknown":
        lines.append("Could not compare with origin/main (offline, or main not pushed yet).")
    return lines


def decisions_locked() -> bool:
    """True once the Idea row of docs/DECISIONS.md has been filled in."""
    try:
        with open(os.path.join(ROOT, "docs", "DECISIONS.md"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("| Idea |"):
                    return line.strip().strip("|").replace("Idea", "", 1).strip() != ""
    except OSError:
        pass
    return False


def main() -> None:
    """Print the session briefing."""
    now = clock.now_ct()
    name, todo = clock.phase(now)
    out = [
        "== Veritas hackathon briefing (from .claude/hooks/session_start.py) ==",
        f"Now: {now:%a %b %d, %I:%M %p} CT | Phase: {name}",
        f"Do now: {todo}",
    ]
    nxt = clock.next_deadline(now)
    if nxt:
        out.append(f"Next deadline: {nxt[0]} in {nxt[1]}")
    if not clock.before_kickoff(now) and not decisions_locked():
        out.append("WARNING: docs/DECISIONS.md has no locked idea yet. Lock it (/kickoff) before building.")
    out += git_lines()
    out.append("Before working: read docs/DECISIONS.md and docs/BRIEF.md, then state task, rubric line and model tier (AGENTS.md).")
    print("\n".join(out))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a briefing failure must never block a session
        print(f"(session briefing unavailable: {exc})")
    sys.exit(0)
