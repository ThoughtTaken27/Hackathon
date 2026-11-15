# Web Push integration (for router/household wiring)

Files: `web/src/push.js` (server), `web/public/sw.js`, `web/public/js/pushclient.js`, `web/public/manifest.webmanifest`. Tests: `web/test/push.test.mjs` (matches the RFC 8291 Appendix A vector byte for byte).

## push.js exports
- `makeVapidKeys()` -> `{ publicKey, privateJwk }`. Codes DO generates once on first use, stores in its storage. No env or git secret.
- `validSubscription(sub)` -> cleaned `{endpoint, keys:{p256dh,auth}}` or null. Host allowlist, https only, key lengths checked. Run on every POST.
- `sendPush(sub, payload, keys, {ttl, urgency, fetchImpl})` -> `{ok, status, gone}`. Never throws, 8 s timeout. `gone` (404/410): delete that sub.
- `vapidHeaders`, `encryptPayload`: used inside sendPush.

## Server contract to wire
- `GET /api/push/key` -> `{ publicKey }` (from Codes DO).
- `POST /api/h/:id/push` body `{ subscription, name, quiet: {from,to}|null }`, family role only. Validate with `validSubscription`, dedupe by endpoint, keep at most 10 per home.
- `DELETE /api/h/:id/push` body `{ endpoint }`, family role only.
- Sending an alert:
  ```js
  const payload = { title, body, tag: `kettle-${homeId}`, url: `/family?h=${homeId}#${keyFragment}`, tier: "urgent"|"concern"|"test", alertId, home: homeId };
  const results = await Promise.all(subs.map(s => sendPush(s, payload, keys, { urgency: tier === "urgent" ? "high" : "normal" })));
  // drop subs where results[i].gone
  ```
  Skip non-urgent sends inside a sub's `quiet` window. Payload max is about 4 KB; keep it small. No health detail in the body of a lock-screen notification beyond what family agreed to.
- Family page: on load, if `?ack=<alertId>` is present, acknowledge that alert, then `history.replaceState` to strip it. The ack sits in the query string before the hash, so the family key never leaves the browser.

## Client
- Register on every page that wants offline: `import { registerSW } from "/js/pushclient.js"`.
- Enable button handler (must be a tap): `subscribe(publicKey)` then POST the result.
- `pushSupport().why`: `no-sw | no-push | ios-needs-home-screen | denied | null`.
- iOS: web push only works for a Home Screen web app, iOS 16.4+. Safari tab gets `ios-needs-home-screen`; show "Add to Home Screen first" steps.

## Notes
- `/listen` has no HTML file in `web/public` yet. Router must serve it (precache tolerates a miss).
- Bump `CACHE` in `sw.js` when shipping changed assets; `?v=` strings in the shell list must match the HTML.
- Docs/AI-USAGE-LOG row for push.js still to add by the team.
