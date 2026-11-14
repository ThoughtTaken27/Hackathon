---
name: component-craft
description: "Component-level polish standard: layout anatomy, type and spacing scale, state copy, motion choreography, stability, touch adaptation, and a CSS audit. Distilled from measuring every affectUI and AI SDK Agents component. Use when building, restyling or reviewing any UI component, card, list, menu, toast, status line, result panel, approval, or agent-progress surface. Pairs with ui-polish (process and inspiration) and apple-design (spatial principles)."
---

# Component Craft

Polish is not decoration. Measured across 280+ components, it comes from one small, consistent system applied everywhere, plus a defined answer for every state. The reference values are in `references/measured-system.md`. Do not invent new ones.

Hackathon note: the states that matter most for judges are **loading, result, "not in our list" / unknown input, and error**. A result card that handles all four calmly is worth more than any animation (AGENTS.md §0.7, §4).

## The ten laws

1. **One system, few values.** About 4 easings, 6 durations, 6 radii and 8 font sizes, and stop there. A new value needs a reason the existing ones cannot serve. Most polish is consistency.
2. **Tray and card.** The content sits on a white (or raised) card with a 1px hairline and a 1-2px shadow. Status, counts, countdowns and secondary actions go on a quieter tray around or below the card. The card holds the thing itself. The tray holds what is said about it.
3. **Small, dense, calm type.** Body 13-14px, weight 500 for names and 400 for prose. Meta 12-12.5px muted. Headings rarely above 15px inside a component. Tabular numbers for anything that counts; tighten letter-spacing slightly (-0.01em) on medium text. Hierarchy comes from weight and ink level, not size.
4. **Every state is designed, and its copy is written.** Idle, live, waiting on you, failed, finished, empty and narrow. Copy follows `references/state-copy.md`: the title says what happened, one sentence gives the cause, and a real fact goes where reassurance would ("Your list is saved."). A time or count says what happens next. Name the button by its effect.
5. **Nothing moves that you did not move.** Reserve width for the bold or longest label, keep status glyphs in one fixed slot, and use one drawing that morphs (spinner to check or cross) instead of swapping nodes. Fix heights where browsing would otherwise jump. Never remove and re-add a node during live updates. A state change only touches the part that changed.
6. **Things that come and go unfold and fade. Nothing flies.** Enter with opacity, 3-6px of rise and 2-3px of blur over 240-460ms on the out-curve. Exit faster (160-280ms) and upward. Animate height with `grid-template-rows: 0fr → 1fr`. Clip only while the motion runs, so focus rings and shadows survive.
7. **Feedback is instant and physical.** Every pressable gets `:active` scale(0.96-0.98) on a 160ms transition. Hover and colour changes take 150-160ms. Only checks and pops use the overshoot curve. Loading uses a light band sweeping across a copy of the label, not a spinner swap that changes the label's width.
8. **Show the trail, then fold it.** Live work shows its real steps, each with a short present-tense label and real numbers ("Checking 6 of 9 medicines"). When it finishes, the trail folds into one record row ("Checked 9 medicines · 2.1s"). The record stays.
9. **Exceptions first; colour is spent on meaning.** Lead with what needs the person (warnings and failures at the top). Accent colour appears only where it means something: one dot, the live step, the risky item. Status tags are coloured text on a light fill of the same hue, and every tag gets the same width.
10. **Touch and narrow are designed, not shrunk.** On coarse pointers, anything hover-revealed stays visible, and targets grow to 40-44px with bigger invisible hit areas. Inputs use 16px text and keyboard hints are dropped. On narrow containers, shed in a declared order (note first, then counts, then labels down to their icons) using container queries.

## Procedure (run inside ui-polish's loop)

1. **List the states.** For each component, write the state table (state | copy | glyph | actions | what animates) before styling. Start from the closest anatomy in `references/pattern-catalog.md`, then fit it to the product's real meanings. Never copy a pattern one-to-one when the data or tone differs. For forms, live lists or uploads, use `references/verification-cases.md` for lifecycle, keyboard and reduced-motion cases.
2. **Write the copy** for every state using `references/state-copy.md`. Real nouns and numbers, no filler or exclamation marks, status labels of 2-4 words.
3. **Tokens.** Inherit the app's palette and fonts and map them onto the measured scale (`references/measured-system.md`). Adopt the system, not affectUI's colours.
4. **Choreograph.** For each transition, write what moves first, its delay, duration and curve. Build from `references/motion-recipes.md`. Only transform, opacity and filter animate, plus grid-rows for height. Add a reduced-motion branch that leaves the end state standing still.
5. **Verify.**
   - **CSS audit** (replace `<css>` with the stylesheet paths). FIX items must be zero; each WARN is fixed or gets a stated reason. In layered CSS, confirm a hit with computed style first: a later, more specific rule may already override it.
     ```bash
     grep -rnE "transition:\s*all|scale\(0\)|\bease-in\b[^-]" <css>                        # FIX
     grep -rnE "transition[^;]*\b(width|height|top|left|margin|padding)\b" <css>          # WARN: animating layout
     grep -rnE "linear-gradient|border-left:|font-style:\s*italic" <css>                  # WARN: needs a reason from the brief
     grep -rhoE "cubic-bezier\([^)]*\)" <css> | sort | uniq -c                            # aim: <= 4 easings
     grep -rhoE "border-radius:\s*[^;]+" <css> | sort | uniq -c                           # aim: <= 6 radii
     grep -rhoE "font-size:\s*[^;]+" <css> | sort | uniq -c                               # aim: <= 8 sizes
     grep -c "prefers-reduced-motion" <css>                                                # must be >= 1 if anything animates
     ```
   - **State sweep:** capture every state from step 1 at 393px and desktop width, in light (and dark if supported).
   - **Stability check on live updates:** in Playwright, attach a `MutationObserver` that counts removed nodes and record element rects before and after an update. Pass = 0 nodes removed while live, no shift above 1px in unchanged parts.
   - **Prove it in the real app,** not just a dev harness: read computed styles of the changed elements at the address people actually load.
   - **Accessibility:** one polite live region per component announces state changes, controls are named after their object ("Remove ibuprofen"), focus-visible rings show.
6. **Critique against the laws,** one line per law, then fix the weakest two before showing anything.

## References

- `references/measured-system.md`: the numbers (type, spacing, radii, control sizes, durations, easings, keyframes, colour roles).
- `references/state-copy.md`: copy patterns per state, with verbatim examples.
- `references/pattern-catalog.md`: anatomy and non-obvious details of about 40 AI and agent components, plus when not to use each one.
- `references/motion-recipes.md`: CSS recipes for blur crossfade, grid fold, flash-and-fold removal, check pop-and-draw, glyph morph, shimmer label, digit roll, stretching pill.
- `references/verification-cases.md`: lifecycle, geometry, scroll, clipping and flicker acceptance cases.
