---
description: P0 lock at kickoff (Fri 11 PM CT). Paste the brief, pick idea + track, fill docs/DECISIONS.md, split work into GitHub issues. Run once, with the whole team on the call.
argument-hint: "[paste the brief text, or leave empty and paste when asked]"
disable-model-invocation: true
---

You are running the team's kickoff (AGENTS.md §3 P0, `docs/KICKOFF.md`). Goal: idea, track, roles and data contracts locked by 12:00 AM CT. This is a Lead-tier decision (AGENTS.md §9); keep it to one pass.

1. **Time check.** Run `TZ=America/Chicago date`. Before Fri Nov 13 11:00 PM CT: say "brief not out yet", offer to rehearse with `docs/IDEAS.md`, write nothing.
2. **Brief.** Use `$ARGUMENTS` if given; otherwise ask the human to paste the brief **verbatim**, with attachment names and links. Write it into `docs/BRIEF.md` with the time received. Then list, quoting the brief's exact words: problem statement, target user, named datasets/resources, required deliverables or constraints, judging hints.
3. **Shortlist.** Score the top 2–3 options (from `docs/IDEAS.md` plus anything the brief suggests) in one table against the Round 1 rubric (tech 30, originality 20, impact/fit 20, testing 15, comms 15) and the idea filter in `docs/IDEAS.md`. If the brief names a dataset, an option that uses it wins ties. Give one recommendation with the single sentence a judge would repeat, and the riskiest assumption.
4. **Chatbot test.** Give the human one representative input to paste into ChatGPT/Gemini/Claude. If a chatbot already does it well, our edge must be something we can measure against that chatbot as a baseline; say what.
5. **Humans decide.** Stop and wait for the team's pick. Disagree once with evidence, then commit.
6. **Lock.** Fill every row of `docs/DECISIONS.md`: track, idea, one-sentence problem, named persona, MVP flow (max 5 steps, each visible in the demo), out of scope, primary metric, test-set recipe, labeler (not the code author), code home, UI, LLM provider (cheapest that works, no-key cached mode). Fill **Module owners** with an input → output contract per module (plain dicts/JSON, field names and types) so three people can build in parallel. Add decision-log rows for what we rejected and why.
7. **Story first.** Draft the 60-second demo script into `docs/WRITEUP.md` (video section): exactly what the user does on screen, step by step. If it can't be said in 60 seconds, cut scope now.
8. **Issues.** If `gh` works (`gh auth status`), create one issue per module and one for the eval set, using `.github/ISSUE_TEMPLATE/task.md` fields (rubric line, owner, contract, done-check). Otherwise list them in `docs/DECISIONS.md` under Module owners.
9. **Commit** only the docs (`docs/BRIEF.md`, `docs/DECISIONS.md`, `docs/WRITEUP.md`) in one small commit, pull --rebase, push to main, and tell everyone to pull.

Finish with: the locked one-sentence pitch, who owns what, and the next deadline (P1 skeleton by 2 AM CT, then sleep).
