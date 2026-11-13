# Submission kit

Deadline: **11:59 PM ET / 10:59 PM CT Sun Nov 15**. Our target: **9:00 PM CT**. No late entries.

The write-up and video are all a blind reviewer sees first. Put our numbers in the first 30 seconds of the video and the top half of the write-up.

## One-page write-up template

1. **Problem:** one sentence + one cited statistic.
2. **Who it's for:** a specific person (e.g. "a 72-year-old on a diuretic in Phoenix").
3. **Approach:** pipeline diagram; why our design (e.g. rules + LLM instead of end-to-end LLM).
4. **Results:** metrics table, baseline vs. ours, fairness table.
5. **Where it fails:** 3 concrete examples.
6. **Limitations and safety:** prototype, not medical advice; data/rule gaps.
7. **Credits:** every dataset, API, library, pretrained model, and every AI tool used (from `AI-USAGE-LOG.md`).

## 2-minute video structure

| Time | Content |
| --- | --- |
| 0:00–0:15 | Hook: a real person's scenario |
| 0:15–1:05 | Live demo of the core flow |
| 1:05–1:35 | Results + fairness table |
| 1:35–1:50 | One honest failure |
| 1:50–2:00 | Impact and what's next |

Upload as **unlisted** YouTube (or direct upload). Check the link in a private/incognito window.

## Questions to rehearse (finals Q&A = 20%)

- Why not just ask ChatGPT?
- How did you build the ground truth, and who labeled it?
- Which group did your model do worst on, and why?
- What happens if the input isn't in your table/model's coverage?
- How would you validate this with real patients/clinicians?
- Which parts did AI tools write? Walk us through that code.

## Final checklist (Sun 5–9 PM CT)

- [ ] Fresh clone / fresh Colab runtime runs end to end from the README instructions.
- [ ] No API keys in the repo or notebook outputs (search for `key`, `sk-`, `AIza`).
- [ ] Repo/Colab is viewable by judges (public or shared link tested in incognito).
- [ ] README: what it is, how to run, sample inputs, results summary, credits, "not medical advice".
- [ ] Write-up is one page; video is under 2:00 and unlisted.
- [ ] `AI-USAGE-LOG.md` complete; AI tools credited in the write-up.
- [ ] Every teammate can explain every module.
- [ ] Submitted, and confirmation email received by every teammate.
