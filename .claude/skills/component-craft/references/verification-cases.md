# Craft verification cases

Use these when a component owns forms, uploads, live lists, or more than one surface. These are acceptance cases, not another aesthetic checklist.

## The governing distinction
A source shows a pattern; a screenshot shows one presentation; a build shows compilation; a behaviour test shows only its exercised path. None proves the others. Never copy gated (paid) implementation source; measurements and patterns only.

## Meaning before presentation
- Remove/cancel/approve changes the logical source of truth immediately. A fading row is only a presentation snapshot: inert, hidden from accessibility, and excluded from submits, counts, retries and late async updates.
- Keep a row through its exit; cancel a stale removal if its key returns. Clean up timers and object URLs.
- Animate a check only when completion happens while mounted, not when loading history. An unknown progress fraction stays indeterminate. Never invent a percent, time remaining, count or outcome to fill a design (AGENTS.md §0.4).
- Exercise rapid open-close-open, repeated remove/retry, unmount during a transition, and delayed completion after removal. Reduced motion uses a settled end state without extending the action's lifetime.

## Geometry at the boundary
- Test the real wrappers (the actual Streamlit/Gradio/page container), not only an isolated harness.
- A shrinking flex child needs a shrinkable chain up to the field, not just min-height on its leaf. Padding creates a minimum box: large bottom padding can push a footer below the visible viewport.
- For a long input, check the root doesn't scroll unexpectedly (scrollHeight <= clientHeight), the input and primary button stay visible, and `elementFromPoint` at the button returns the button. A screenshot and rectangles alone can miss an overlay.
- Use the screenshot's real pixel size when cropping. Don't assume devicePixelRatio.

## One owner per interaction
- A reading gesture (scrolling up) cancels auto-follow. A disclosure may reveal its own content, not jump elsewhere. The virtualizer and the follower never both correct the same movement.
- Keep status glyphs and action slots dimensionally stable. Check unchanged neighbours while live updates happen.
- Enter/exit is reversible from the current presentation. Prefer a small arrival over a whole-card slide. Initial history is settled; idle elements don't replay entrances.

## Clips, corners, and flicker
- **Every clip box owns its bleed.** A row that sits outside its column on purpose (negative margin for icon alignment or a press fill) needs that same horizontal room on every ancestor that clips. Probe: walk from the glyph up and fail if any `overflow != visible` ancestor's left edge is right of the glyph's left edge.
- **A scroll container is a clip with its own corners.** When a rounded card is taller than its scrolling parent, give the scroll container the card's radius. Verify with a capture at a mid-scroll position, not only top and bottom.
- **Flicker is usually a state flipping and flipping back, not a paint bug.** Instrument the page before guessing: log `animationstart`/`transitionstart` and attribute mutations with timestamps, then look for pairs that undo each other within about a second. Common causes:
  1. A scroll flag (`at-end`) turning false while auto-follow glides to new content, then true again: the jump button blinks on every update. Treat a pinned follow as already at the target.
  2. A brief network blip shown as "Reconnecting" then "Reconnected" within a second. Give connection loss a short grace window (about 2.5s) and announce recovery only after an outage people saw.
  3. Entrance animations replaying when a rerun hands an existing list new keys (common in Streamlit reruns). Key items by stable identity, and treat many arrivals in one update as a resync, not live work.
- Regression-test each fix with the old code: the new test should fail before the fix and pass after.

## Minimal evidence bundle
A component/state matrix, source URLs plus measured properties, a before/after or reproducible fixture, two capture/critique rounds for changed UI, functional and lifecycle checks, and real production styles/hit targets. A finished slice is never a substitute for the whole requested scope.
