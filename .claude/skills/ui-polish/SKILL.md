---
name: ui-polish
description: "Workflow for anything visual (the demo screen, web app, Streamlit/Gradio UI, HTML page, results chart). Research reference sites, build from sourced values, capture real screenshots, measure, critique, and iterate before showing anyone. Use when you design, restyle, polish or review UI, or when someone says \"polish\", \"make it look premium\", \"looks like AI slop\", \"clean it up\" or \"aesthetic\"."
---

# UI Polish

The first draft is never the deliverable. Judge composition, hierarchy, spacing, type, material and motion together, from a real screenshot. "It builds and the tests pass" is not acceptance.

## Hackathon scope (read first)

- Polish only what judges see: the one demo screen and the first 15 seconds of the video (AGENTS.md §4). Nothing else.
- Polish comes **after the Sat 6 PM gate**, in P4/P5. Before that, a plain working screen beats a pretty broken one.
- Timebox each loop round to about 45 minutes. Two rounds, then stop.
- Never change logic, labels or numbers while polishing. If polish needs a code change beyond styling, it's a separate task.
- Streamlit: custom CSS goes in one `st.markdown("<style>…</style>", unsafe_allow_html=True)` block plus `.streamlit/config.toml` theme. Gradio: `gr.Blocks(css=…, theme=…)`. Keep all styling in one file so it's easy to explain.

Pair this with the other bundled skills:
- `component-craft`: **the component standard** (ten laws, measured scale, state copy, motion recipes, CSS audit). It owns per-component decisions; this skill owns the loop.
- `frontend-design`: aesthetic direction, AI-tell list, copy rules.
- `emil-design-eng`: motion and component feel (easing, durations, press states, reduced motion).
- `apple-design`: Apple's design principles for the web. Apply it when building (spacing, type size and tracking, radius, colour budget, materials, springs) and again as the review pass in step 7.

## The loop (do every step)

1. **Brief.** One line each: what the screen is for, the one thing it must say first, where it lives, and the existing tokens to reuse. In an existing app, inherit its tokens and classes before inventing any.
2. **Research (before styling).** Pull concrete values for the exact components involved. Reuse `references/extracted-values.md` first. Only research what's missing, with a `scout` subagent asked for "exact values + URL"; append new findings.
3. **Token plan.** Write a compact plan: palette (named values), type scale (sizes, weights, tracking, leading), spacing rhythm (one base unit), radii by hierarchy, motion (duration + curve per interaction). Check it against the AI-tell list; revise anything that is a default rather than a choice.
4. **Build.** Write each component's state table and copy first (component-craft procedure steps 1-2). Only transform/opacity animate. Every pressable gets `:active` feedback. Respect `prefers-reduced-motion`. No hover-only affordances on touch surfaces.
5. **Capture.** Real screenshots with Playwright (Python: `page.set_viewport_size`, `page.screenshot`): desktop at 1440x900 (how judges see it) and phone at 393x852, plus empty, error and dark states if they exist. Then open the PNGs with the Read tool and look at them.
6. **Measure.** Run the component-craft CSS audit (0 FIX; justify each WARN). From the screenshots check: one shared left edge, spacing on the base unit, text contrast >= 4.5:1 (3:1 for large text and graphics), the accent appearing only where intended, nothing clipped or duplicated.
7. **Critique.** Ask a fresh subagent (with the screenshots and CSS paths) for a verdict (ship / needs-fix) and the four highest-leverage fixes at selector level (hierarchy, composition, material, motion). Also self-critique: remove one accessory.
8. **Iterate.** Apply, re-capture, re-measure. Two rounds in hackathon mode. Stop when the critique says ship and the measurements pass, or the timebox runs out.
9. **Deliver.** Show the final screenshots. List what changed and which source each value came from. Commit screenshots the README or write-up will use.

## Reference sites

| Site | Use it for |
|---|---|
| Zeron (github.com/zeronsh/zeron) | Whole-product material: layered surfaces, hairlines, frosted overlays, 20-26px panels, 44px touch controls, 50px primary buttons, grouped cards with inset separators |
| coss.com/ui | Structural components on Base UI: radius scale, buttons, focus rings, dialogs, checkboxes, collapsibles |
| transitions.dev | Motion values for toasts, tabs, list exits, content swaps (values live in `:root` custom properties) |
| kinetics.colorion.co | Micro-interactions with code (check, hold-to-confirm, countdown, toast overshoot) |
| devouringdetails.com | Detail craft |
| beui.dev | Motion constants (ease, springs, toast stack) |
| useplanes.com/components/heroes, /sections | Hero and section composition for web pages |
| ui.spectrumhq.in, 21st.dev, shadcnblocks.com, reactbits.dev | Component ideas; filter hard for taste |
| evilcharts.com | Chart styling (bars, grids, tooltips) for the results chart |
| useplanes.com/components | Animated text, headlines, heroes, reasoning traces, command palette: the one "wow" moment |
| uiarc.dev/components | Dense data blocks, charts, tabular numbers, foundation tokens |
| aisdkagents.com/ai-components | AI and agent surfaces: answers with citations, tool/step trails, attachments, questions panels |
| affectui.com/components | Thinking states, text reveals, number tickers, shimmer loaders, toasts, message actions |

These libraries are for patterns and measured values. Rebuild the idea in our own code; never paste their source, and never use paid (Pro) source at all.

Reject purple glows, hover-only tricks, tilt cards on touch, and black halos on light surfaces.

## House taste

- Default canvas: the platform's neutral (near-white, or a true dark gray in dark mode). Not cream, paper or parchment, and not near-black with a single bright accent, unless the brief asks.
- Graphite text, one accent spent on meaning (the result, a risk level, the primary action).
- System sans for everything. A serif or italic headline only when the brief asks; never a large italic serif hero.
- Restraint reads as expensive. If a choice exists only to look premium, cut it. Premium comes from spacing, type size and tracking, radius by hierarchy, and instant feedback, not from a palette.
- Frosted glass only on functional chrome (nav, controls, sheets); content surfaces mostly opaque.
- No nested pills, badge circles, decorative gradients, breathing animations or full-screen colour washes.
- Composition and hierarchy first; decoration last.

## Hard rejects

Reject on sight, in the plan and again in the screenshot, unless the brief names it:
- Purple gradients, glowing buttons, glow halos.
- Coloured stripes down the side of cards (`border-left` accent bars).
- Massive italic serif headlines.
- Black or cream "old money" backgrounds trying too hard to look expensive.

Before showing anyone, grep the CSS for `font-style: italic`, `serif`, `linear-gradient`, `border-left`, inset side-stripe shadows (`box-shadow: inset 3px 0`), and glow-style `box-shadow` on `h1`/`.hero`/`button`/`.card`. Each hit needs a stated reason from the brief.

## AI-tell checklist (reject unless the brief asks)

- Tracked ALL-CAPS eyebrow over every section; labels above content that add nothing.
- Meta strings chained with middle dots on every row.
- Monospace for small data labels.
- Identical rounded cards with the same soft grey shadow; one radius everywhere.
- Fade-and-slide-up on every section; hover effects on every card.
- One word accented in a headline; `→` appended to buttons.
- Viewport-clamped font sizes on a fixed-width phone surface.
- Reassurance filler copy ("Nothing to worry about!"). In a health app this is also a safety problem: never imply "safe" (AGENTS.md §0.7).

## Tooling notes

- Serve local files with `python -m http.server <port> --bind 127.0.0.1` (or the app's own server) rather than opening `file://` URLs.
- Streamlit/Gradio take a few seconds to render: wait for a known element (`page.wait_for_selector`) before the screenshot.
- If you can't view images, rely on DOM measurements (`getBoundingClientRect`, `getComputedStyle`) and a subagent critique, and say so.
- Fixtures and screenshots use generic or synthetic data only, never real people (AGENTS.md §0.6).

## References

- `references/extracted-values.md`: exact values already pulled from the sites above, with URLs. Append new findings; don't re-research what is there.
