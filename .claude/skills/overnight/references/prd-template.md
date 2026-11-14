# PRD: <product name>

Status: draft v<n> · written <CT time> · brief received <CT time> · track: <track>
Every claim has a source link or says "assumption". Every number has its N or says "not measured yet".

## 0. The pitch
- **One sentence:** what it is, for whom.
- **The sentence a judge repeats to another judge:**
- **Why this wins (three lines):**

## 1. The brief and track fit
- Verbatim lines from `docs/BRIEF.md` we answer, and how. Use the brief's own words throughout this document.
- Why this track over the other three (the triage table from research, with scores).

## 2. Problem
- One sentence + **one cited statistic** (primary source opened, URL, date).
- Voice of the user: 3–5 paraphrased quotes with links (Reddit, X, reviews, forums).

## 3. Who it's for
- One named persona: age, situation, the exact moment they need this, what they do today instead.

## 4. What already exists (teardown summary)
| Product | Link | Why people use it | Price | Biggest weakness | Evidence |
- The one or two we are rebuilding from, and why those. Link the full teardowns in `docs/research/`.
- Past hackathon projects in this space and what they lacked.

## 5. What we build differently
- **Keep** (the core that delivers the value) · **Cut** · **Add**.
- **Why would anyone use ours instead of the original?** Answer for the persona, in one paragraph, without the word "AI".
- **Why it matters and who will care** (user, caregiver, clinic, judge).
- What is free in ours that is paid elsewhere, and why we can offer it (public data, no proprietary dependency).

## 6. Does this need AI?
- For each step of the flow: lookup, rules, or model? Why.
- The model component judges will see (predicts / classifies / extracts / generates / recommends), which model, why the cheapest one that works.
- **No-AI baseline** and **chatbot baseline** (transcript path). What ours does that they can't, stated as something measurable.
- "LLMs format, rules decide": which decisions are rules, which are model, how model output is validated.

## 7. The core flow (max 5 steps, each visible in the demo)
1. …
- The 60-second test: the script of what the user does on screen.
- The one interactive moment where a judge supplies their own input.
- Three golden-path demo inputs.

## 8. Features
| Feature | Must / Should / Won't | Rubric line it moves | Done-check |
- Out of scope, explicitly.

## 9. Design and UX spec
- Screen list (aim: one screen). For each component: state table (idle, loading, result, "not in our list"/unknown, error, empty, narrow) with the exact copy.
- Token plan: palette, type scale, spacing unit, radii, motion (duration + curve per interaction).
- Which reference patterns we adapt and from where (pattern and measurement only, never copied source).
- Motion plan: the one orchestrated moment; press feedback; reduced-motion behaviour.
- Trust display: how every output shows its reasoning and source.
- "Prototype, not medical/financial advice" placement.

## 10. Architecture
- Stack and why (boring, runnable by a judge in under 5 minutes, no keys needed).
- Module table: module | owner | inputs → outputs (field names and types) | done-check.
- Data flow diagram (text).
- Caching and no-key demo mode (`demo_cache/`). Timeouts, retry, fallback for every external call.

## 11. Data, models, licences
| Source | Use | Licence | Key? | Hit once and cached? |

## 12. Safety and honesty rules
- Unknown ≠ safe. What we never say. Synthetic or public data only.
- Known limits we will state openly.

## 13. Evaluation plan
- Primary metric and why it matters for the persona. Secondary metrics.
- Baselines: trivial, simple, the incumbent/chatbot.
- Dev set (built by the builder) vs **frozen test set (labelled by a teammate who did not write the code)**: recipe, size, label source.
- Slices (lead with the expected worst). Failure gallery plan. One cheap ablation.
- The one command: `python -m eval` → `results/metrics.json`.

## 14. Rubric scorecard
| Line | Pts | What the judge will see from us | Self-score now | Biggest risk | Fix |
(Round 1: technical 30, originality 20, impact + track fit 20, testing + honesty 15, communication 15. Finals: demo 30, depth 30, impact 20, Q&A 20.)

## 15. Risks and premortem
- "It's Sunday 9 PM and we lost. Why?" Top five causes, each with an if-then plan and a cut.
- Plan B (the runner-up idea) and the switch gate (time and condition).

## 16. Build plan
- Milestones against the AGENTS.md clock: skeleton, core flow real, gate, first eval, harden, freeze.
- Cut list, in the order we cut.

## 17. Team plan (two teammates are beginners)
- Three lanes with owners. For each lane: 3–5 tasks, each with a **copy-paste prompt for their Claude Code**, the files they may touch, and the done-check.
- What each person must be able to explain to a judge.

## 18. Demo and video script (2:00)
| Time | Says | Shows |

## 19. Finals Q&A prep
- Ten likely questions from ML researchers with our answers (why this model, baseline, where it fails, leakage, another week).

## 20. Open questions for the humans (ranked; each with our default if nobody answers)

## 21. Credits
Every product that inspired us, dataset, API, library, model and AI tool.
