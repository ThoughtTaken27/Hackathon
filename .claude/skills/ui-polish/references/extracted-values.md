# Extracted design values

Exact values pulled from reference sites (Sep–Oct 2026). Append new findings with date and URL. These are references to translate into the app's own tokens, not code to copy.

## coss.com/ui
- Radius scale 6 / 8 / 10 / 14 / 16px. Buttons 10px; cards and dialogs 16px.
- Buttons transition only `box-shadow`, 150ms `cubic-bezier(.4,0,.2,1)`.
- Focus: 1px white inner ring + 3px coloured outer ring, not the browser outline.
- Dialog backdrop `rgba(0,0,0,.32)` + `backdrop-filter: blur(8px)`.

## rareui.com
- Display tracking ramps with size: -1.8px at 72px, -0.9px at 36px, -0.4px at 16px.
- Dark cards `#121212` at 32px radius (showcase-oversized; scale down).

## beui.dev
- `EASE_OUT = [0.16, 1, 0.3, 1]`; `EASE_DRAWER = [0.32, 0.72, 0, 1]` (sheet open 0.5s tween, no overshoot).
- Button press scale .93, hover 1.02, spring `{ stiffness: 500, damping: 30, mass: .6 }` (use .97 on dense utility UI).
- Springs: swap `{460, 30, 0.55}`, panel `{420, 40, 0.5}`, layout `{360, 32, 0.6}`.
- Tabs: pill list rounded-full p-1 gap-1, trigger px-3.5 py-1.5 text-sm/500, indicator spring `{245, 36, 1.2}` (no overshoot), content enter opacity + y4 0.18s.
- Toast: rounded-2xl border bg-card/95 p-3; enter `y:22, scale:.96, blur(10px)`, spring `{420, 34, .75}`, exit .18s blurred; max 4 visible, 4.2s default.
- Checkbox: 20px box, check path draw 0.3s ease-out after .04s, press .92.
- Numbers: animated count 1.2s ease-out with tabular-nums.
- Rejected: ±12° tilt card (pointer-only).

## Zeron (github.com/zeronsh/zeron, MIT; check font/icon licences)
- Layered near-black surfaces (dark) / pearl (light), translucent white interaction washes, low-opacity hairlines.
- 20-26px rounded panels, 44px touch controls, 50px primary buttons, grouped cards with inset separators (radius 20, fill white 4.5%, 1px white-6% stroke, separators inset 16px, rows 16px horizontal / 11-12px vertical, title 15 / subtitle 12.5).
- Short reduced-motion-aware transitions; `backdrop-filter` on a few major surfaces only, never per row.

## transitions.dev
- Toast shell radius 52, padding 0 16, gap 10; shadow `0 4px 42px rgba(0,0,0,.06), 0 2px 6px rgba(0,0,0,.05), 0 0 0 1px rgba(0,0,0,.06)`. Enter `translateY(16px) scale(.97) blur(2px)` 350ms, exit 250ms, both `cubic-bezier(.22,1,.36,1)`.
- Sliding tabs: container radius 48, padding 3, bg #f1f1f1, white indicator; tabs 30px tall, 13px/500; indicator 250ms same curve.
- Success check: 48px circle, path draw 500ms after 80ms, blur 10px to 0.
- Text status swap `translateY(4px) + blur(2px)` 150ms; two-line reveal 12px + blur(3px) 500ms, 40ms stagger.

## kinetics.colorion.co
- Hold-to-confirm fill 0.8s linear; early release reverts 0.2s ease-out.
- Copy check `scale(.5) → 1` 0.3s `cubic-bezier(.34,1.56,.64,1)`, reverts after 1.4s.
- Tab pill glide 0.4s `cubic-bezier(.65,0,.35,1)`; toast overshoot `cubic-bezier(.18,1.25,.4,1)`.

## devouringdetails.com
- Dev-tools badge: 36px pill, `rgba(0,0,0,.8)`, blur 48px; width morph 0.25s, scale 0.15s, `cubic-bezier(.23,.88,.26,.92)`; press .95. Never animate width on first render.

## Emil Kowalski (emil-design-eng skill)
- `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`; `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`; drawer `cubic-bezier(0.32, 0.72, 0, 1)`.
- Press 100-160ms; popovers 125-200ms; dropdowns 150-250ms; modals/drawers 200-500ms. UI under 300ms. Exit faster than enter. Stagger 30-80ms. Never `scale(0)`; start at .95 + opacity 0.

## Nexvyn (ui.nexvyn.dev)
- Durations: instant 50ms, fast 120ms, base 200ms, slow 320ms. Easings: out `(0.22, 1, 0.36, 1)`, in-out `(0.65, 0, 0.35, 1)`. Springs: fast `{400, 30, 0.8}`, press `{700, 32, 1}`, settle `{260, 26, 1}`.
- Button: press scale(0.97) translateY(1px); sizes sm 36 / md 44 / lg 48px tall; focus ring-2 + offset-2; colours transition fast ease-out only.
- ActionButton: idle/pending/success/error crossfade (opacity + scale .95 + 1px blur), width locked by an invisible sizing layer; minPending 600ms kills flicker; aria-live announcements, focus never moves.
- Checkbox: 20px, radius 5px, stroke 2 round caps; draw only after the first toggle; reduced motion instant.

## Galleries (styles.refero.design, Mobbin glossary, Apple HIG; Sep 27)
- **Linear:** one accent per view, used on a single primary action; neutrals #08090a / #0f1011 / #161718; hairlines 0.5px; tracking -0.022em at 48px+, -0.011em at 15px; radii buttons 6, cards 12, pills 9999; elevation from hairlines + inner shadows, not drop shadows.
- **Things:** canvas #f2f5f7, cards #fff, ink #303336 (never pure black), secondary #838b96; body 17-18px/1.6 at ~540px max width; cards 18px, buttons/inputs 6px; sections split by whitespace or a background band, never hairline dividers.
- **Todoist:** one accent per view; single 8px radius; status badges = pale wash + chromatic text (e.g. #f0f6df bg + #446c3d text). Never grayscale status.
- **Apple:** body 17px tracking -0.022em; Large Title 34/41 Regular; one blue role per element; no drop shadows on cards/buttons/nav, use surface shifts.
- **GitHub (designmd.me):** canvas #010409, surface #0D1117, border #30363D, link #1F6FEB, success #1F883D, danger #CF222E; radii 4/6/12/999; spacing 4/8/16/24/32/48; input 32px tall.
- **Empty states (Mobbin):** one context line + one CTA + small visual; no generic "no data". Types: first-use, no-results, post-completion, feature-education.
- **Skeletons (Mobbin):** light-grey blocks mirroring the layout, one shimmer, preserve space; skip when content is near-instant (<500ms).
- Simplify: one accent per screen; show each timestamp once; no status label AND badge; radii 8 inputs/buttons, 16 cards/sheets.

## Arc foundation (uiarc.dev/r/arc-foundation.json)
- Radii control 18 / panel 26 / surface 34 / pill 9999; heights 36/44/50; type 12,14,16,18,22,28,36,52,72; display tracking -.03em, body -.01em.
- Shadows: rest `0 1px 2px` 3.5%; raised `0 6px 18px` 6.5% + `0 1px 3px` 3.5%; float `0 20px 48px` 10.5% + `0 3px 10px` 4.5%. Durations 120/160/240/480; enter `.16,1,.3,1`, standard `.22,1,.36,1`, exit `.7,0,.84,0`.
- Line chart: 220px tall, 48px value axis, 1px grid, 2px line, dashed comparison 1.75px `4 5`, area = series at 9%, tooltip 1px border / 14px radius / 10px 12px padding.

## Charts (evilcharts.com)
- Bar radius 2px; bars grow 0.5s with 0.05s stagger, `cubic-bezier(0,.7,.5,1)`; area gradient .1 → 0; tooltip 200ms; dashed cursor and horizontal grid `3 3`; hover dims other bars to ~.38.

## Refero / Open Design (Oct 5)
- Notion: canvas #f6f5f4, card #fff, muted #615d59, border rgba(0,0,0,.08), card radius 12, padding 24. Vercel: canvas #fafafa, ink #171717, hairline rings not shadows.
- 8px base; one accent per screen; no decorative gradients; borders and surface shifts for grouping, shadows only for raised/menus; display tracking negative above ~40px; metric numbers 40-48px.
- Dim currency cents/symbols (.52em, .5 opacity) next to a large number.

## Lapa Ninja samples (Oct 5; three pages, not representative)
- Vercel: hero 64/64px, -3.84px tracking; 14/20 body; CTA 150ms `cubic-bezier(.4,0,.2,1)`.

## affectUI + AI SDK Agents (Oct 17)
- Full measured scale, copy patterns and component anatomy live in the `component-craft` skill's references. Headline: 4 easings (`.22,1,.36,1` out, `.34,1.56,.64,1` pop, `.34,1.3,.64,1` spring, `.32,.72,.24,1` drawer); durations 160/260/380/460; type 13 / 12.5 / 13.5px at w500; radii 8/10/14/16; tray `#f0f0f0` + card `#fff` hairline.

## Rejected across sites
- 21st.dev conic glow and beam cards; glow buttons (hover-only, black halo on light); 8-bit kits wholesale; spell.sh 3D pop button and emoji-burst input (toy-like, wrong tone).
