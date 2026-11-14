# Chatbot test: translating pharmacy directions into Marathi and Hindi (Nov 13 2026, ~11:25 PM CT)

**Setup:** a fresh general-purpose model (Claude Sonnet 5.5 subagent, no project context, no tools) got the user message below. The transcript is reproduced in full. The overnight lead agent checked the output, reading the Devanagari.

**User message:** "My grandmother only reads Marathi and a little Hindi. Please translate these pharmacy label instructions into Marathi AND into Hindi, line by line, and tell me if any line is risky to rely on:" followed by 8 lines (twice daily with food; 2 capsules at bedtime; no alcohol; half tablet, don't crush; inhaler 1 puff every 4–6 h, max 8 in 24 h; hold if BP < 100; 10 units under the skin before breakfast; Mon/Wed/Fri only).

**Chatbot output (verbatim translations):**
1. MR जेवणासोबत दिवसातून दोन वेळा १ गोळी तोंडाने घ्या. · HI खाने के साथ दिन में दो बार 1 गोली मुँह से लें।
2. MR झोपण्यापूर्वी (झोपताना) २ कॅप्सूल तोंडाने घ्या. · HI सोते समय 2 कैप्सूल मुँह से लें।
3. MR दारू (मद्य) सोबत घेऊ नका. · HI शराब के साथ न लें।
4. MR दररोज सकाळी अर्धी (१/२) गोळी घ्या. गोळी चुरडू नका किंवा चावू नका. · HI हर सुबह आधी (1/2) गोली लें। गोली को कुचलें नहीं और चबाएँ नहीं।
5. MR घरघर (दम लागल्यासारखा आवाज) होत असल्यास, गरजेनुसार दर ४ ते ६ तासांनी १ पफ घ्या. २४ तासांत ८ पफपेक्षा जास्त घेऊ नका. · HI साँस में घरघराहट (सीटी जैसी आवाज़) होने पर, ज़रूरत के अनुसार हर 4 से 6 घंटे में 1 पफ लें। 24 घंटे में 8 पफ से ज़्यादा न लें।
6. MR तुमचा रक्तदाब (ब्लड प्रेशर) १०० पेक्षा कमी असेल तर हे औषध त्या वेळी घेऊ नका. · HI अगर आपका ब्लड प्रेशर 100 से कम हो तो यह दवा उस समय न लें।
7. MR नाश्त्यापूर्वी १० युनिट त्वचेखाली (इंजेक्शनने) घ्या. · HI नाश्ते से पहले 10 यूनिट त्वचा के नीचे (इंजेक्शन से) लें।
8. MR फक्त सोमवार, बुधवार आणि शुक्रवारी १ गोळी घ्या. · HI केवल सोमवार, बुधवार और शुक्रवार को 1 गोली लें।

It then ranked the lines by clinical risk (insulin units, "hold", splitting a tablet), told the user to have a pharmacist or fluent speaker check, and said not to change any medicine.

**Verdict:** the chatbot **passes**. All 16 translations keep dose, frequency, timing, negation and route (lead agent's reading. **Not a blind native-speaker label;** the human Marathi/Hindi speaker should recheck this). Note that in Marathi it switched to Devanagari digits (१, २, ४, ६, ८, १०), which a naive digit-matching rule would miss, so the checker must normalise digits.

**What this means for the idea:**
- "A better translator" is dead as a pitch: a frontier chatbot already translates short directions well.
- What the chatbot does *not* give: a check that works on **whatever translation the family actually has** (a phone translator, a free offline model, a printed label from a relative). It also gives no measured miss rate. Its own risk ranking is about clinical risk, not "did this translation keep the facts". Its advice to "have a fluent speaker check" is exactly the step a family without a bilingual member can't do.
- So our product is the **checker**, and frontier-chatbot translations become one more system we audit (and the "best case" row in the results).
