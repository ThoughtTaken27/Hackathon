# Design critique, round 1 (Sat Nov 14, 11:00–11:25 AM CT)

Inputs: `round-0/` (desktop light preview, 33 states) and the first 72 captures of `round-1/` (every kitchen state, how-sure, caregiver never/live-paused; desktop + phone, light + dark). The rest of round 1 was cut short by a 30-s request timeout while the machine was saturated (fetch + Apple + embeddings); those caregiver states were reviewed in `round-0/` and are re-captured in round 2.
Measured against: PRD §9, component-craft's ten laws, ui-patterns.md (incumbent screens), AGENTS.md bans.

## What works
- **Calm, not surveillant.** No alert counts (Canary's "9 alerts" banner), no live room location (havn's "ACTIVE NOW"), no red anywhere except the server-error state. The heartbeat is a sentence with a time, like Care Daily's "Looking good · 10 seconds ago", not an icon.
- **Words before colour.** Every rule card says its state in a sentence ("Can't tell: Kettle wasn't listening from 6:00–10:00 AM"); the dot only reinforces it.
- **Kitchen screen** reads from across a room: 40 px headline, 24 px body, a 96 px Pause, and every check Meera set is listed for the parent, so nothing is hidden from him.
- **How sure** leads with a verdict computed from the numbers, then the two macro-F1 figures with CI and N, then misses and false alarms as their own bold columns (the brief's ask).
- **CSS audit:** 0 FIX. Gradient hits are the hatch textures that encode "Not sure"/"Not listening" and the shimmer loader; `border-left` hits are the two-bar pause glyph and a chart axis, not side-stripe cards. No italic, no serif, no glow.

## Problems found (and fix status)
| # | Where | Problem | Law / source | Fix |
|---|---|---|---|---|
| 1 | caregiver, all states | `.empty-day { display:flex }` overrode `[hidden]`: "Nothing heard yet today." sat on top of a day that had vacuuming (live-paused phone) | law 4 (every state designed), correctness | Global `[hidden] { display:none !important }` — **fixed** |
| 2 | caregiver desktop | Day bar spent ~70% of its width on the future; at 393 px a 20-min block was ~6 px (unreadable, untappable); only one label fitted | PRD §9.4 narrow rules, law 10 | Bar spans 6 AM → a little after now (≥ 6 h; whole day once late) — **fixed**, decision logged |
| 3 | caregiver phone | Title wrapped to two lines beside a long "How sure is Kettle?" button | hierarchy | Button shortens to "How sure?" under 520 px — **fixed** |
| 4 | caregiver + kitchen, paused | Pause glyph drew as a rounded "( )" after the radius consolidation | glyph clarity | Square bars (radius 0) — **fixed** |
| 5 | kitchen phone | Hour ticks collided ("6 AM7 AM") | law 5 | Tick step chosen so each label gets ≥ 64 px — **fixed** |
| 6 | how-sure phone | Per-activity table cut off at the right ("Rig / wher / says") | law 10 | Below 520 px the precision and N columns drop (still in the desktop table and metrics.md) — **fixed** |
| 7 | kitchen mic-denied | "Steps for a helper" had no disclosure marker; looked like plain text | affordance | `summary` as a list item with its triangle — **fixed** |
| 8 | kitchen, every state | Content pinned top-left over a large empty area on a screen read from 1–2 m | composition | Main column vertically centred — **fixed** |
| 9 | kitchen consent | Copy says "Meera sees a day timeline like this one" but no timeline was shown | copy ↔ screen mismatch | A drawn example bar tagged "Example, not real" — **fixed** |
| 10 | caregiver never-started | A judge's first screen: an empty bar and "Kettle isn't on yet", with the sample day buried below the fold | first 15 seconds (AGENTS.md §4) | Intro card under the heartbeat with "Play a sample day" as the primary action — **fixed** |
| 11 | caregiver | Heartbeat line was `aria-live` and changes every second | a11y spam | Only state changes are announced, via one polite region; new blocks announced ("Washing up, 8:45 AM, how sure: high") — **fixed** |
| 12 | how-sure | Verdict capitalised names mid-sentence ("catches Vacuuming and TV") | copy | Lower-cased — **fixed** |
| 13 | rule-editor sheet | Closed sheet leaked into full-page captures (only translated off-screen) | law 6 | `visibility:hidden` when closed, delayed so the exit still animates — **fixed** |
| 14 | type and radius scale | 12 radii and 5 raw font sizes | law 1 | Radii now 0/4/6/8/12/16/20/pill (the PRD hierarchy); every size is one of the 8 tokens — **fixed** |
| 15 | activity colours | First palette failed `validate_palette.js` (slate pair ΔE 13 normal vision; teal/rose ΔE 3.8 for deuteranopes) | dataviz skill | Reference palette hues assigned so real neighbours pass CVD and normal-vision checks in both themes; red reserved — **fixed** |
| 16 | kitchen "starting" | Under heavy CPU load the headline stayed "Listening…" for 30 s | live latency | Re-check in round 2 with the machine idle (privacy-check run reached "Listening for kitchen sounds") |
| 17 | how-sure, dark | Plot PNGs are white boxes on the dark canvas | dark mode | Open: accept for now (dark mode is 3rd in the cut order); revisit in round 3 |

## Motion added this round
Block settle (scaleX from its left edge, 380 ms out-curve) + label fade-in (+120 ms, 4 px rise, 3 px blur) + summary blur-crossfade; press feedback `scale(.97)` 160 ms on every button; heartbeat "last heard" digits roll (160 ms) without moving the sentence; how-sure headline numbers count up once (600 ms). `prefers-reduced-motion`: animations off, 120 ms opacity only.
