# Motion recipes

Generic recipes written from measured behaviour (not vendor source). Variables: `--ease: cubic-bezier(.22,1,.36,1)`, `--ease-pop: cubic-bezier(.34,1.56,.64,1)`, `--ease-spring: cubic-bezier(.34,1.3,.64,1)`.

## Text in / out (labels, status lines, titles)
```css
@keyframes text-in  { from { opacity: 0; transform: translateY(4px);  filter: blur(3px); } }
@keyframes text-out { to   { opacity: 0; transform: translateY(-4px); filter: blur(3px); } }
.label-enter { animation: text-in 320ms var(--ease) both; }
.label-exit  { animation: text-out 220ms ease-in both; position: absolute; } /* old text fades on top */
```
Keep both layers in one grid cell (`display:grid; > * { grid-area: 1/1 }`) so the swap never changes layout. If the width changes, glide the box width over 260ms and clip only while it glides.

## Fold / unfold height without measuring
```css
.fold { display: grid; grid-template-rows: 0fr; opacity: 0;
        transition: grid-template-rows 260ms var(--ease), opacity 200ms ease; }
.fold[data-open] { grid-template-rows: 1fr; opacity: 1; }
.fold > * { min-height: 0; overflow: hidden; }
```
A closed body must be `inert`. Clip only the inner element, so outer focus rings survive.

## Row enters, row leaves (flash, then fold)
```css
.row { display: grid; grid-template-rows: 1fr; animation: grow 420ms var(--ease) both;
       transition: grid-template-rows 260ms var(--ease), opacity 200ms ease; }
@keyframes grow { from { grid-template-rows: 0fr; opacity: 0; } }
.row[data-leaving] { grid-template-rows: 0fr; opacity: 0; pointer-events: none;
       transition: grid-template-rows 260ms var(--ease) 200ms, opacity 220ms ease 180ms; }
.row[data-leaving] .row-inner::before { animation: flash 280ms ease-out both; } /* inset tinted fill */
@keyframes flash { 35% { opacity: 1; } }
```
JS removes the node after about 480ms. A leaving row loses its hover fill and stops taking input immediately.

## Check: pop, then draw
```css
.check { animation: pop 440ms var(--ease-pop) both; }
@keyframes pop { 0% { transform: scale(.5); } 60% { transform: scale(1.12); } 100% { transform: scale(1); } }
.check path { stroke-dasharray: 14; stroke-dashoffset: 14; animation: draw 340ms var(--ease) 120ms forwards; }
@keyframes draw { to { stroke-dashoffset: 0; } }
```
Use it once, at completion. Never loop it.

## One glyph that morphs (spinner to check or cross)
Keep the spinner, check and cross in one fixed square (`display:grid; place-items:center; width:16px; height:16px`). When the state changes, the spinner freezes where it is (`animation-play-state: paused`), fades to 0 and scales to .8 over 200ms. The result glyph pops in at the same spot. The slot never changes size, so the label beside it never moves.

## Shimmer label (working)
```css
.shimmer { position: relative; color: color-mix(in srgb, currentColor 55%, transparent); }
.shimmer::after { content: attr(data-text); position: absolute; inset: 0; color: transparent;
  background: linear-gradient(90deg, transparent 38%, var(--shine) 50%, transparent 62%) 100% 0 / 300% 100% no-repeat;
  -webkit-background-clip: text; background-clip: text; animation: sweep 1.6s linear infinite; }
@keyframes sweep { to { background-position: 0 0; } }
```
`--shine` is rgba(255,255,255,.82) on light and .95 on ink. On a coloured label, mix the shine from the label colour. Stop the animation when the work stops.

## Skeleton sweep (all blocks in phase)
Use `background-attachment: fixed`, a size of 150vw, and position animated from -50vw to 100vw over 2.2s linear, so every skeleton on screen shares one sweep. Never animate each block on its own phase.

## Digit roll
Each digit is a column of 0-9 inside a 1.15em window with `mask-image: linear-gradient(transparent, #000 14%, #000 86%, transparent)`. Only the changed column moves (translateY to the new digit over 460ms on --ease). A new column enters from -35% with opacity. Use tabular numbers, and put the real number in the aria label.

## Stretching pill (segmented control, tabs)
Animate `left` and `right` (or two custom properties) separately. The edge facing the target moves at 260ms and the trailing edge at 360ms, so the pill stretches toward the target and settles. Press: scale .97 while held. Keep regular and semibold copies of each label stacked and crossfade them so the width never shifts.

## Toast stack
Position by transform and size by height, so both glide. Cards behind show only their edge (scale .94-.96, translateY -8 to -10px). Enter at 440ms on --ease; settle a swipe at 460ms on --ease-spring. The swipe layer is separate from the stack transform, so the finger never fights the stack. Pause the timer on hover, on focus, and while the tab is hidden.

## Press and hover
```css
.pressable { transition: transform 160ms var(--ease), background-color 160ms ease, color 160ms ease; }
.pressable:active:not(:disabled) { transform: scale(.97); }
@media (hover: hover) { .pressable:hover { background: var(--hover-fill); } }
```

## Reduced motion
```css
@media (prefers-reduced-motion: reduce) {
  .component *, .component *::before, .component *::after { animation: none !important; transition-duration: 1ms !important; }
}
```
The end state must be complete without the animation. Apply this to checks, shimmer text and reveals too.
