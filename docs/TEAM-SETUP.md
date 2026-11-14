# Team setup (do this before kickoff)

Setting up accounts and tools before kickoff is allowed. Writing project code is not. Budget: about 15 minutes per laptop.

## 1. GitHub access (repo: `thoughttaken27/hackathon`)

- [ ] Every teammate has a GitHub account.
- [ ] Repo owner adds each teammate: repo **Settings → Collaborators → Add people** (needs the owner's 2FA). Teammates accept the email invite (it expires in 7 days).
- [ ] The repo has a `main` branch and it's the default branch (Settings → General → Default branch).
- [ ] Before submitting: make the repo public (or share access) so judges can open it. Check in an incognito window.

## 2. Your laptop (each teammate)

| Step | macOS | Windows |
| --- | --- | --- |
| Git | `xcode-select --install` (or `brew install git`) | Install **Git for Windows** (includes Git Bash, which Claude Code's hooks need) |
| Python 3.11+ (Colab runs 3.12) | `brew install python@3.12` or python.org | python.org installer, tick "Add to PATH" |
| Claude Code | `curl -fsSL https://claude.ai/install.sh \| bash` | PowerShell: `irm https://claude.ai/install.ps1 \| iex` |
| GitHub CLI (recommended) | `brew install gh` | `winget install GitHub.cli` |

You can also use Claude Code inside the Claude desktop app, or on the web at claude.ai/code. The repo works the same in all three.

Then, in a terminal:

```bash
gh auth login
```

```bash
git clone https://github.com/ThoughtTaken27/Hackathon.git && cd Hackathon
```

```bash
git config user.name "yourfirstname" && git config pull.rebase true
```

```bash
claude
```

- [ ] Log in with your own Claude Pro account when asked.
- [ ] **Accept the "trust this folder" prompt.** The team hooks only run after you trust the folder.
- [ ] Check it works: the first reply should mention the **hackathon briefing** (time in CT, phase, next deadline). If not, run `/hooks` and check Python is on your PATH (`python3 --version` or `python --version`).
- [ ] Type `/start` to run your first session.

## 3. What the repo sets up for you

Everything under `.claude/` is shared through git, so all three Claude Code sessions follow the same rules.

| File | What it does |
| --- | --- |
| `CLAUDE.md` → `AGENTS.md` | The rules, rubric, clock and practices every agent loads |
| `.claude/settings.json` | Default model (Sonnet; switch with `/model`), common safe commands pre-approved, `.env` unreadable, force-push denied, hooks |
| `.claude/hooks/session_start.py` | Every session starts knowing the CT time, phase, next deadline, and whether you're behind `main` |
| `.claude/hooks/guard.py` | Blocks API keys in files and commits, project code before kickoff, force-pushes, committing `.env`. After the Sun 1 PM freeze, asks before new code files or dependency changes |
| `.claude/skills/` | Team slash commands (below) |
| `.claude/agents/` | Cheap Haiku workers: `scout` (research), `builder` (routine code), `runner` (run + report) |
| `.github/` | Issue and PR templates with the done-check and explain-back built in |

**Personal settings stay personal:** put your own overrides in `.claude/settings.local.json` and notes in `CLAUDE.local.md`. Both are git-ignored. Don't edit the shared files for personal taste. If you change them, tell the team.

## 4. Slash commands

| Command | When |
| --- | --- |
| `/kickoff` | Fri 11 PM CT, once, whole team: brief → idea → `DECISIONS.md` → issues |
| `/start [issue#]` | Start of every session: sync, claim one task, branch, plan |
| `/done [issue#]` | End of every task: verify, explain-back, AI log, commit, push, PR |
| `/explain <module>` · `/explain quiz <module>` | After a change; Q&A drills before finals |
| `/checkin` | At each team check-in: done / next / blocked, time left, the cut to make |
| `/ship-check` | Sun 5 PM CT: fresh-clone run, secret scan, numbers vs `results/` |

**Design skills** (third-party, credited in each folder's `SOURCE.md`). Claude also picks them up on its own when you do UI work:

| Command | Use it for |
| --- | --- |
| `/frontend-design` | Visual direction for the demo screen: palette, type, layout that doesn't look AI-templated (Anthropic, Apache-2.0) |
| `/emil-design-eng` | Interaction polish and UI code review: press states, transitions, easing, timing (Emil Kowalski, MIT) |
| `/apple-design` | Motion, gestures, materials, typography, reduced motion, Apple's design principles (Emil Kowalski, MIT) |

Polish is worth points only on the one demo screen and the first 15 seconds of the video. Use these in P4/P5 (Sunday), after the GATE passes. Never let them hold up the core flow or the metrics table.

## 5. How we work together

- **GitHub Issues are the task board.** One issue per task, with an owner, a contract and a done-check. Agents claim issues with `gh issue edit <n> --add-assignee @me`. No `gh`? Tell your Claude the issue number.
- **`docs/DECISIONS.md` is the source of truth** for the idea, owners and data contracts. Want to change a contract? Tell the team first.
- **One branch per task:** `<name>/<task>`. Pull `main` before you start and before you push. Merge to `main` through small PRs, often. `main` must always run.
- **Review = understanding.** A teammate reviews each PR and must be able to explain it. If nobody can within ~15 minutes and the smoke test passes, merge it yourself and say so in chat.
- `docs/AI-USAGE-LOG.md` and `docs/EXPLAIN.md` merge with `union` (see `.gitattributes`): everyone's new rows are kept, so don't hand-resolve those.
- Notebooks conflict badly. One owner per notebook. Keep logic in `.py` files that notebooks import.
- Never force-push `main`. Never rewrite another person's branch. The hooks block the common accidents.

## 6. Claude Pro budget

- Each teammate has their own Pro limits (a 5-hour window plus a weekly cap, shared with chat). Default to Sonnet. Hand searches and routine code to the Haiku workers. Use Opus/Fable only for the calls AGENTS.md §9 lists.
- Start a fresh session per task (`/clear`) instead of one huge session.
- **Claude Pro is not an API key.** If the app itself calls an LLM, it needs a separate key (section 8).

## 7. Google Colab + Drive

- [ ] Everyone can open Colab with a Google account.
- [ ] One shared Drive folder for videos, screenshots and large files (not git). Check it has free space.
- [ ] Learn Colab **Secrets** (key icon in the left sidebar) for API keys. Never paste keys into cells.
- Colab is optional. Use it only if it's the easiest way for judges to run the project with one click. Gradio share links die with the runtime, so a judge-facing app needs Hugging Face Spaces or a rerunnable notebook.

## 8. LLM / vision API (decide before kickoff)

| Provider | Notes |
| --- | --- |
| Google Gemini (AI Studio key) | Free tier; check current limits tonight |
| Anthropic API (console.anthropic.com) | Pay-as-you-go credits; separate from Claude Pro |
| OpenAI API | Pay-as-you-go |
| No LLM / local OCR | Fallback; the rules-based output still works |

- [ ] Pick one, get a key tonight, test it once in the provider's web console (not in our repo).
- [ ] Copy `.env.example` to `.env` and fill it in (git-ignored; Claude is configured not to read it). In Colab use Secrets.
- [ ] Design so the core pipeline works with the LLM turned off and from `demo_cache/` with no keys. That's also our baseline.

## 9. Communication

- Group chat for quick messages; one call link for kickoff and check-ins.
- Anything decided goes into `docs/DECISIONS.md` or an issue, not only chat.
- Check the official email inbox for organizer updates at each check-in.
