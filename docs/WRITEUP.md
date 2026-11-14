# Write-up and video script (living draft)

Owner: Storyteller. Start at kickoff, update as results land (AGENTS.md §2: "pitch in parallel, never last"). Every number here is copied from `results/metrics.json` with its N. Keep names and school out (Round 1 is blind). Final version: one page.

## One-page write-up

**Title + one line:** _what it is, for whom_

**Problem** (one sentence + one cited statistic, opened at the primary source; see `docs/DATA-SOURCES.md`):

**Who it's for** (one specific person, place and moment):

**What it does** (the 60-second flow, in the brief's own words):

**How it works** (pipeline diagram; why this design and what we rejected):

**Results** (from `results/metrics.json`):

| System | Primary metric (N=) | Secondary | Notes |
| --- | --- | --- | --- |
| Trivial baseline | | | |
| Simple baseline | | | |
| Ours | | | |

**Where it does worst** (slice table, worst slice first, with the reason):

**Three real failures** (input → output → cause):
1.
2.
3.

**Limits and safety:** Prototype, not medical advice. _Coverage gaps, what happens off-list, data limits._

**What we'd do with another week:**

**Credits:** datasets, APIs, libraries, pretrained models, and every AI tool used (from `docs/AI-USAGE-LOG.md`, `docs/DATA-SOURCES.md`).

## 2-minute video script

Real voice, real screen, under 2:00, uploaded unlisted. Numbers in the first 30 seconds.

| Time | Says (narration) | Shows (screen) |
| --- | --- | --- |
| 0:00–0:15 | Hook: the person and their moment, plus our headline number | |
| 0:15–1:05 | Live demo of the core flow, including the "why" behind the output | |
| 1:05–1:35 | Results vs baseline, slice/fairness table | |
| 1:35–1:50 | One honest failure and what we learned | |
| 1:50–2:00 | Impact and what's next | |

## The sentence a judge repeats

_One sentence. Protect it._
