# Kettle web: what is stored, who can read it, what it can't protect (plan D6, D8, D9)

| Data | Where | Who can read it | Kept |
|---|---|---|---|
| Sound | the kitchen tab's memory: one 10-s array, overwritten | nobody else; never stored or sent | seconds |
| Setup windows ("Teach Kettle this kitchen"): 192 numbers per window, no audio | the kitchen browser's local storage | that browser only; never sent | until "Forget what it learned" or browser data is cleared |
| Window labels: activity, 9 scores, allowed sound-type names, time | Cloudflare Durable Object (SQLite) for that home | anyone holding the kitchen or family link | 8 days, then deleted; "Delete this home" removes all at once |
| Parent's choices: consent, pauses, private labels, switched-off sounds | same object | both links | until the home is deleted |
| Link keys | the links' `#fragment` (never sent to servers or logs); the server keeps only SHA-256 hashes | the people the links were given to | until the home is deleted |
| Pairing codes | Codes object, 6 letters (31^6 ≈ 887 million) | anyone who types the code within 48 h | 48 h |

Enforced on the server, not just in the page (`web/src/household.js cleanEvent`): only the 9 activity names and the
18 allowed sound-type names are stored; any other field a modified page sends is dropped.
Pairing: 10 wrong codes per address per 10 minutes, then a 10-minute wait (`web/src/router.js`).
Encryption: HTTPS in transit; at rest, Cloudflare's storage encryption. Kettle adds no encryption of its own.

**Kettle can't protect against:** a compromised laptop or phone, a malicious browser extension, someone who already
has a link (there is one family link per home; per-person links and revocation are not built yet), or the parent
being pressured to consent. It is not an emergency device and can't detect falls.

**Consent when memory is impaired (D5):** Kettle asks again every week and pauses if nobody answers. If a parent may
not be able to consent, involve a second trusted family member or the parent's doctor, keep the kitchen screen
visible so the parent always sees what is shared, and stop if the parent objects at any time.

Verify "nothing saved": `python -m eval.privacy_check` (the Python app) and `python web/test/e2e.py` (the web app,
which deletes its test home and checks the 404).
