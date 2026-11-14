# Chatbot test: scam-text check (Fri Nov 13, 11:49 PM CT)

**Method.** A fresh subagent (Claude Sonnet 5.5, no tools, no project context) was told it is a general chatbot that a 74-year-old forwards texts to, and asked to label 12 messages SCAM or LEGIT with confidence and one reason. The 12 messages are **synthetic**, written by the overnight agent from the public patterns in the FTC "top text scams of 2024" spotlight (package, toll, bank impersonation, "wrong number"/reply-bait) plus legit look-alikes (pharmacy, bank fraud alert, SSA code, doctor reminder). Phone numbers use 555. N = 12, so this is a smoke test, not a measurement.

| # | Message (short) | Our intended label | Chatbot | Conf |
| --- | --- | --- | --- | --- |
| 1 | USPS on-hold, lookalike link | scam | SCAM | 97 |
| 2 | CVS prescription ready | legit | LEGIT | 75 |
| 3 | Chase fraud alert, reply YES/NO | legit | LEGIT | 70 |
| 4 | "Hi, is this Linda? It's Karen from the book club…" | **scam (wrong-number opener)** | **LEGIT** | 60 |
| 5 | E-ZPass unpaid toll, .info link | scam | SCAM | 97 |
| 6 | Medicare card, call to confirm SSN | scam | SCAM | 98 |
| 7 | SSA verification code | legit | LEGIT | 55 |
| 8 | "Grandma it's me… don't tell mom" | scam | SCAM | 96 |
| 9 | Wells Fargo new device, call number on card | legit | LEGIT | 72 |
| 10 | Dr. Patel appointment reminder | legit | LEGIT | 80 |
| 11 | Amazon verify payment, lookalike domain | scam | SCAM | 98 |
| 12 | "Hey how have you been? found your number" | scam | SCAM | 85 |

**Result:** 11/12. The miss is the reply-bait "wrong number" opener (#4), the scam family the 2020–2025 Reddit study reports as fastest-growing and worst-detected (see `research-finance.md`). Confidence on legit look-alikes (#2, #3, #7, #9, #10) is only 55–80: it hedges exactly where an older adult needs a clear answer.

**Implication.** A frontier chatbot is a strong baseline on link-based scams. Our edge must be measured, not claimed: (1) the reply-bait slice, (2) false alarms on legit look-alikes, (3) runs offline and free on the device, so no private texts leave the phone, (4) a calibrated "ask someone" band instead of a coin-flip label. The chatbot becomes our **third baseline**, run once on the frozen test set with the transcript saved.
