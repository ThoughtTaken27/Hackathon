"""PreToolUse hook: enforce the AGENTS.md stop-the-line rules that a machine can check.

Team tooling, not project code. Blocks (exit 2, reason on stderr):
  - API keys / tokens / private keys written into files or about to be committed (§0.8)
  - project code written before kickoff, Fri Nov 13 11 PM CT (§0.1)
  - force-pushes that rewrite history, and `git add` of a .env file
Asks the human (after the Sun 1 PM freeze): new code files, dependency changes.
Anything unexpected fails open (exit 0) so a hook bug never stops the team.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clock  # noqa: E402

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

SECRET_PATTERNS = [
    ("Anthropic key", r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    ("OpenAI-style key", r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_\-]{20,}"),
    ("Google API key", r"AIza[0-9A-Za-z_\-]{35}"),
    ("GitHub token", r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|github_pat_[A-Za-z0-9_]{40,}"),
    ("Hugging Face token", r"\bhf_[A-Za-z0-9]{30,}"),
    ("AWS access key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("Slack token", r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    ("Private key", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ("Hard-coded credential", r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"]([^'\"\s]{20,})['\"]"),
]
PLACEHOLDER_HINTS = ("your", "xxx", "<", "example", "placeholder", "changeme", "...", "dummy", "fake")

CODE_EXTS = {".py", ".ipynb", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".html", ".css",
             ".r", ".java", ".go", ".rs", ".c", ".cpp", ".swift", ".kt", ".sh"}
DEPENDENCY_FILES = {"requirements.txt", "pyproject.toml", "package.json", "environment.yml", "setup.py"}


def find_secrets(text: str) -> list:
    """Return 'kind (abcd…)' labels for likely secrets in text, skipping obvious placeholders."""
    hits = []
    for kind, pattern in SECRET_PATTERNS:
        for m in re.finditer(pattern, text):
            value = m.group(m.lastindex or 0)
            if any(h in value.lower() for h in PLACEHOLDER_HINTS):
                continue
            hits.append(f"{kind} ({value[:4]}…)")
    return hits


def block(reason: str) -> None:
    """Stop the tool call; Claude sees the reason."""
    print(reason, file=sys.stderr)
    sys.exit(2)


def ask(reason: str) -> None:
    """Hand the decision to the human with a reason."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def rel_path(path: str) -> str:
    """Path relative to the repo root, with forward slashes."""
    try:
        return os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
    except ValueError:  # different drive on Windows
        return path.replace("\\", "/")


def written_text(tool_input: dict) -> str:
    """All text a Write/Edit/MultiEdit/NotebookEdit call would put into a file."""
    parts = [tool_input.get(k) or "" for k in ("content", "new_string", "new_source")]
    parts += [e.get("new_string") or "" for e in tool_input.get("edits") or []]
    return "\n".join(parts)


def check_file_write(tool_name: str, tool_input: dict) -> None:
    """Rules for tools that change files."""
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    rel = rel_path(path)
    name = os.path.basename(rel)
    ext = os.path.splitext(name)[1].lower()
    secrets = find_secrets(written_text(tool_input))
    if secrets and not name.startswith(".env"):
        block(f"Blocked: {', '.join(secrets)} in {rel}. Keys live in env vars / .env / Colab Secrets, "
              "never in files git can see (AGENTS.md §0.8). Read the key with os.environ instead.")
    if rel.startswith(".claude/") or rel.startswith("../"):
        return
    is_code = ext in CODE_EXTS or name in DEPENDENCY_FILES
    now = clock.now_ct()
    if is_code and clock.before_kickoff(now):
        block(f"Blocked: {rel} is project code and kickoff is Fri Nov 13, 11:00 PM CT. Rules: all project "
              "code is written during the 48 hours (AGENTS.md §0.1). Do docs/planning now, or wait for kickoff.")
    if clock.after_freeze(now):
        if name in DEPENDENCY_FILES:
            ask(f"FREEZE is in effect (since Sun 1 PM CT): changing {name} adds risk. Approve only for a bug fix.")
        if is_code and tool_name == "Write" and not os.path.exists(path):
            ask(f"FREEZE is in effect (since Sun 1 PM CT): {rel} is a new code file. Approve only for a bug fix.")


def changed_text_for_commit() -> str:
    """Text a commit could include: diff vs HEAD plus untracked, non-ignored files."""
    def run(*args):
        try:
            r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
            return r.stdout if r.returncode == 0 else ""
        except Exception:
            return ""
    diff = run("diff", "HEAD", "-U0") or run("diff", "--cached", "-U0")
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    for f in run("ls-files", "--others", "--exclude-standard").splitlines():
        try:
            if os.path.getsize(os.path.join(ROOT, f)) < 1_000_000:
                with open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore") as fh:
                    added.append(fh.read())
        except OSError:
            pass
    return "\n".join(added)


def check_bash(command: str) -> None:
    """Rules for shell commands."""
    for part in re.split(r"&&|\|\||;|\n", command):
        part = part.strip()
        if re.search(r"\bgit\s+push\b", part):
            if re.search(r"(?:^|\s)(?:-f|--force)(?:\s|$)|\s\+\S", part):
                block("Blocked: force-push rewrites history others may have pulled (AGENTS.md §8). "
                      "Pull --rebase and push normally, or ask the human.")
            if "--force-with-lease" in part and re.search(r"\bmain\b", part):
                block("Blocked: never force-push main (AGENTS.md §8).")
        if re.search(r"\bgit\s+add\b", part) and re.search(r"(?:^|[\s/])\.env(?!\.example)\b", part):
            block("Blocked: .env holds secrets and must never be committed (AGENTS.md §0.8).")
    if re.search(r"\bgit\s+commit\b", command):
        secrets = find_secrets(changed_text_for_commit())
        if secrets:
            block(f"Blocked commit: possible secret(s) in your changes: {', '.join(secrets)}. "
                  "Move keys to .env / env vars, then commit (AGENTS.md §0.8).")


def main() -> None:
    """Read the hook payload and apply the matching rules."""
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if tool_name == "Bash":
        check_bash(tool_input.get("command") or "")
    elif tool_name in {"Write", "Edit", "MultiEdit", "NotebookEdit"}:
        check_file_write(tool_name, tool_input)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail open: a hook bug must never block the team
    sys.exit(0)
