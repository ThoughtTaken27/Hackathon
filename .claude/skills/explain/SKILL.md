---
description: Explain a module or the latest change so a teammate can repeat it to a judge, and save it to docs/EXPLAIN.md. With "quiz", drill a teammate with judge-style questions instead.
argument-hint: "<module or file> | quiz <module>"
---

Finalists are questioned live on every choice (AGENTS.md §0.2). This makes sure all three teammates can answer.

**Explain mode** (`$ARGUMENTS` = a module, file, or empty for the latest diff):
1. Read the actual code (`git diff main...HEAD` if no target). Never explain from memory.
2. Write, in plain words a high-schooler can say aloud in 30 seconds:
   - **What it does** (input → output, one sentence)
   - **Why this way, and what we rejected**
   - **Known limit / failure case** (a real one, with an example input)
   - **Likely judge question + our answer** (ML-researcher style: baseline, failure, leakage, why this model)
3. Walk through any non-obvious lines one at a time. If something can't be explained simply, say so and propose a simpler version: code a teammate can't explain is a stop-the-line problem.
4. Add or update the entry in `docs/EXPLAIN.md` under the module name, using its template.

**Quiz mode** (`$ARGUMENTS` starts with `quiz`):
1. Read the module's code and its `docs/EXPLAIN.md` entry.
2. Ask the human 5 questions, one at a time, and wait for each answer: what it does, why not just ChatGPT, how ground truth was built, worst slice and why, what happens off-list or with bad input, how they'd validate with real users, and one "walk me through this line" question.
3. After each answer: say what was right, what was missing, and the accurate answer from the code. Don't reveal answers before they try.
4. End with a score out of 5 and the one thing to rehearse.
