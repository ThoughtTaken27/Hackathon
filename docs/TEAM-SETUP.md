# Team setup (do this before kickoff)

Setting up accounts and tools before kickoff is allowed. Writing project code is not.

## 1. GitHub access (repo: `thoughttaken27/hackathon`)

- [ ] Every teammate has a GitHub account.
- [ ] Repo owner adds each teammate: GitHub → repo **Settings → Collaborators → Add people** (Write access). Teammates accept the email invite.
- [ ] Decide repo visibility for submission: judges must be able to open it. Make it public (or share access) before submitting.

## 2. Claude Code for each teammate (Claude Pro)

- [ ] Sign in at [claude.ai/code](https://claude.ai/code) and connect GitHub when asked.
- [ ] Install the Claude GitHub App on the repo if prompted (the repo owner may need to approve it).
- [ ] Start a session on `thoughttaken27/hackathon`. Claude reads `CLAUDE.md` automatically, so it knows the rules.
- [ ] Each cloud session works on its own branch. Merge into `main` through small pull requests, often. Pull `main` before starting new work.
- Pro has usage limits. Don't burn them on tasks a quick search answers. Start a fresh session per task rather than one huge session.

**Claude Pro is not an API key.** A Pro subscription covers chatting and Claude Code; it does not let our app call an LLM. If the project needs an LLM/vision call inside the app, we need a separate API key (see 4).

## 3. Google Colab + Drive

- [ ] Everyone can open Colab with a Google account.
- [ ] One shared Drive folder for videos, screenshots and large files (not git).
- [ ] Learn Colab **Secrets** (key icon in the left sidebar) for API keys: never paste keys into cells.

## 4. LLM / vision API (open question: decide before kickoff)

The app may need one LLM call (rewrite rule outputs into plain language) and possibly a vision call (read a med-list photo). Options:

| Provider | Notes |
| --- | --- |
| Google Gemini (Google AI Studio key) | Has historically offered a free tier; check current limits tonight |
| Anthropic API (console.anthropic.com) | Pay-as-you-go credits; separate from Claude Pro |
| OpenAI API | Pay-as-you-go |
| No LLM / local OCR (e.g. Tesseract) | Fallback; rules-based output still works |

- [ ] Pick one, get a key tonight, test it once in the provider's web console (not in our repo).
- [ ] Store it as `LLM_API_KEY`-style env var / Colab secret. `.env` is git-ignored.
- [ ] Design so the core pipeline still works with the LLM step turned off (also a nice baseline for evaluation).

## 5. Communication

- [ ] Group chat for quick messages; one call link for kickoff and check-ins.
- [ ] Shared decisions go into `docs/DECISIONS.md` in the repo, not only chat.

## 6. Git rules of the road

- Branch per person/feature: `<name>/<feature>` (cloud Claude sessions name their own branches; that's fine).
- Pull before you start, pull before you push. Small commits with clear messages.
- Never force-push `main`. Never rewrite another person's branch.
- Notebooks cause merge conflicts: one owner per notebook, or keep logic in `.py` files and import them.
