# Measured system

Sources: rendered CSS of all 51 affectUI components, 8 motion pieces, 12 screens and 11 blocks (Classic style), plus computed styles of all 201 AI SDK Agents (aisdkagents.com) demos. Measured Oct 17, 2026. Counts are occurrences across the corpus. These are measurements, not copied source.

## Type

| Role | affectUI | AI SDK Agents | Use |
|---|---|---|---|
| Body / names | 13px w500, lh 20px (207×) | 13px w500, ls -0.13px, lh 16-20px | primary text in rows, buttons |
| Prose | 13.5-14px w400, lh 1.45 | 13-14px w400, lh 20-22px | answers, descriptions |
| Meta | 12.5px w400 muted, lh 18px (164×) | 12px w400 muted, lh 16px (1041×) | status lines, times, counts |
| Micro | 11-11.5px w500 | 10-11px (mono for ids) | tags, kbd hints, axis labels |
| Component title | 14-15px w500-600 | 14px w500 | card header, at most one per card |
| Hero number | 24-28px w500, ls -0.02em | 24px w500, ls -0.6px | meters, receipts, the headline metric |

- Weights: 500 dominates (304×), 600 for emphasis (46×), 400 for prose. 700 is basically never used.
- Letter-spacing: -0.006em to -0.02em on medium text. Never positive tracking except on tiny caps, which are rare.
- `font-variant-numeric: tabular-nums` on every timer, count, size and price (88× affect, 1101× AI SDK).
- Family: Inter (affect) and Geist (AI SDK). Mono only for code, ids and tool names.
- The muted ink does most of the work: `text-muted-foreground` is the single most used class (2906×).

## Spacing

- Gaps: 10, 8 and 6px dominate (affect); 8, 4 and 6px (AI SDK). 2px between stacked name and meta lines.
- Paddings: `0 10px` and `0 14px` on controls, 14px on cards, 4-6px on trays that wrap a card. Rows use `10px 6px 10px 10px`.
- Card inner padding plus inner radius should about equal the outer radius (concentric corners), e.g. card 16 / inner 6 / area 12.

## Radii (by hierarchy)

| Element | Radius |
|---|---|
| Tray / outer shell | 16-22px |
| Card | 14-16px |
| Row, menu item, area | 10-12px |
| Button md / sm / lg | 12 / 10 / 14px |
| Chip, icon button | 8px |
| Tag, kbd, favicon | 4-6px |
| Pill, avatar, dot | 999px / 50% |

## Control sizes

- Buttons: sm 32px (13px text, 16px icon), md 40px (14px text, 18px icon), lg 48px (15px text, 20px icon). Inline actions are 24px pills at 12px.
- Icon buttons 28-30px on mouse, 40px on touch. Rows 36-44px (a data table uses 44px rows and a 44px selection column, so the cells are square).
- Touch: at least 40px for options and 44px for rows. Inputs use 16px text.
- Icons 14-16px inline, 18px in buttons, 1.6-1.8 stroke, round caps and joins.

## Surfaces and lines

- Light: tray `#f0f0f0`, card `#fff`, line `#ececec`, area `#fafafa`, ink `#171717`, text `#404040`, muted `#8f8f8f`, faint `#b5b5b5`.
- Dark: tray `#111113`, card `#19191b`, line `#2a2a2e`, ink `#ededed`, muted `#8b8b92`. Floating layers one step lighter than the card (`#26262a`).
- Card edge: `box-shadow: 0 0 0 1px var(--line), 0 1px 2px rgba(0,0,0,.04)`. Slightly stronger: `0 0 0 1px line, 0 1px 3px rgba(0,0,0,.08)`. Avoid big drop shadows.
- Primary button: dark fill with a 1px ring and a light top edge. It inverts to light in dark mode.
- Tags: coloured text on an 8-12% fill of the same hue. Danger is `#e5484d` light and `#ff6369` dark.
- Focus ring: `outline: 2px solid rgba(ink, .22); outline-offset: 2px`.

## Durations (ms, by job)

| Job | ms |
|---|---|
| Colour and hover feedback, press scale | 150-160 |
| Small exit (toast, chip, label out) | 200-280 |
| Fold or unfold (grid rows), content swap | 260-380 |
| Enter (text in, row grow, card settle) | 300-460 |
| Check pop | 420-460 |
| Hero reveals (text reveal, wipe) | 560-760 |
| Spinner revolution | 800-1000, linear |
| Shimmer sweep | 1600-2200, linear |

Corpus frequency: 160 (467×), 260 (365×), 380, 300, 200, 220, 320, 460. AI SDK defaults to 150ms ease-out for colours, 300ms for enter, 200-240ms for grid folds.

## Easings

| Name | Curve | Use |
|---|---|---|
| out (default) | `cubic-bezier(0.22, 1, 0.36, 1)` | enters, folds, glides |
| out-soft | `cubic-bezier(0.25, 1, 0.5, 1)` | grid-row folds, label in |
| spring | `cubic-bezier(0.34, 1.3, 0.64, 1)` | toast settle, swipe return |
| pop | `cubic-bezier(0.34, 1.56, 0.64, 1)` | checks and votes only |
| drawer | `cubic-bezier(0.32, 0.72, 0.24, 1)` | sheets |
| ease / ease-out | built-in | colour, opacity |
| linear | | spinners, shimmer, timers |

Use ease-in only for exits under 300ms.

## Keyframe vocabulary (values)

- text-in: from `opacity 0, translateY(4px), blur(3px)`. text-out: to `translateY(-4px), blur(3px)`.
- label in (button morph): from `opacity 0, blur(3px), translateY(25%)` over 480ms. Icon in: from `blur(2px), scale(.7)` over 520ms.
- pop: `scale(.4 or .5) → 1.12-1.15 at 60% → 1`.
- draw: stroke-dasharray equal to the path length, dashoffset to 0 over 340-360ms after a 60-180ms delay.
- flash (row removal): inset fill opacity `0 → 1 at 35% → 0` over 280ms, then the row folds after a 200ms delay.
- shake (error): ±3px on X at 20/40/60/80%, 380ms, once.
- roll (digits, phase labels): in from `translateY(70%)` plus blur over 460ms, out to `-70%` over 320ms.
- Blur values: 3px (128×), 2px (33×), 8px only for hero text.
- Scale values: 0.8-0.82 for things appearing, 0.96-0.98 for press, 1.06-1.08 for a raised or dragging state.

## Media and container branches present in nearly every component

- `@media (prefers-reduced-motion: reduce)` (122×): animations removed, the end state stays.
- `@media (hover: none) and (pointer: coarse)` (69×): hidden controls become visible, targets get bigger, kbd hints are dropped.
- `@container (max-width: 420-600px)`: shed secondary content in a declared order.
