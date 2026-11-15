# Kettle web: the shareable version

The same Kettle, as a web app anyone can try with two devices and no install:
**the parent's kitchen laptop** labels sound in its own browser (the frozen CED-tiny encoder + head, exported to ONNX),
and **the family member's phone** sees the day. Only labels, times and scores travel, through a tiny sync service
(one Cloudflare Durable Object per home). No accounts: each home has two private links and short pairing codes.

## Run it locally (no dependencies beyond Node 20+)

```bash
cd web && npm install && node dev.mjs     # http://localhost:8787
```

Open `/start` on one device and `/kitchen` on another (or two browser windows). Households are kept in `web/.data/dev.json`.

## What proves it's the same Kettle

| Check | Command | Result |
|---|---|---|
| ONNX graphs vs the Python pipeline, 90 sample clips | `python tools/export_onnx.py` | same label 90/90, embedding diff < 1e-5 (`public/model/parity.json`) |
| The browser runtime + JS head vs Python labels | `python web/test/prepare.py` then `node web/test/parity-web.mjs web/.data/test` | label, "unlike anything learned" and top sound 90/90; ~0.46 s per 10-s window (`public/model/parity-web.json`) |
| Timeline, summary, checks, heartbeat vs Python `view.today()` | `cd web && npm test` | 16 states across 3 sample days, identical text (`test/fixtures.json` from `tools/export_web_fixtures.py`) |
| Sync API: pairing, consent gate, roles, delete | `cd web && npm test` | `test/api.test.mjs` |
| End to end: set up, pair by code, consent, fake mic, family view, pause, delete | `python web/test/e2e.py http://localhost:8787 web/.data/test/fake-kitchen.wav web/.data/test` | first label in ~12 s; pause reaches the family view; delete leaves a 404 |

Differences from the Python app, on purpose: windows are 10 s apart (not 2 s) to keep sync light; the kitchen "Sounds like…" chip
uses the latest 10-s window (not a separate 5-s one). The model, head, threshold and every timeline/check rule are unchanged.

## Deploy (free Cloudflare plan)

```bash
cd web && npx wrangler login && npx wrangler deploy
```

`wrangler.toml` serves `public/` as static assets and binds two SQLite-backed Durable Objects (`Household`, `Codes`).
Labels older than 8 days are deleted; "Delete this home" removes everything.

## Privacy, plainly

- Audio: a 10-second array in the kitchen tab's memory, overwritten continuously, dropped on pause. Never stored or sent.
- Sent: activity label, 9 scores, a "novel" flag, the top 3 household sound names and scores, start and end time.
- Keys live in the link's `#fragment` (never sent to servers or logs) and in each device's local storage; the server stores only their SHA-256.
