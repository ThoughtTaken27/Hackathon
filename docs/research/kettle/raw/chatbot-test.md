# Chatbot test (product-teardown step 9), Sat Nov 14 2026 ~09:27 CT

Model: Claude Haiku 5.5 as a fresh subagent, no repo context, no tools, no web. Answer below is its reply, verbatim apart from formatting. Its facts (phone numbers, prices, model names) are **unverified** and are not cited anywhere else.

## Prompt
"My dad is 79, has early memory loss and lives alone 300 miles from me. At 11 AM I often wonder whether he ate breakfast. He would hate a camera and won't wear a pendant. I have an old laptop I could leave in his kitchen. What can I do, concretely, to know his day went normally? And if I used the laptop's microphone to recognise sounds like dishes, cooking or the TV, how accurate would that be?"

## Reply
Concrete options, roughly from least to most intrusive:
1. **Agree on a routine with him first.** Ask him to text one word ("ate") or do a 9 AM phone call.
2. **Meal support.** Home-delivered meals bring a daily visit and a meal; local aging agencies can arrange daily check-in calls.
3. **Non-camera sensors (about $10–30 each).** Fridge/front-door contact, kitchen motion sensor, smart plug on the kettle or microwave. Pattern alerts ("no fridge opening by 11 AM") tell you more than raw data.
4. **Voice assistant** running a morning routine that asks "Did you have breakfast?"
5. **Pre-set breakfast** so a "yes" is easy to confirm.

On the laptop idea: pretrained audio models (e.g. YAMNet, trained on AudioSet) recognise broad classes (speech, TV, running water, dishes, kettle/microwave); reasonably accurate on clean sounds but "I can't give you a reliable percentage without testing it in his kitchen". Real kitchens with TV, fan or radio cause confusions (running water vs dishes, cooking vs TV). **"Sound can show that activity happened. It can't show that he ate."** Privacy: only with his informed consent, keep no audio. Recommendation: start with a routine and sensors; if using the laptop, record labelled samples from his kitchen with consent, test the classifier on them, and treat output as "kitchen activity detected", never proof he ate.

## What this means for Kettle
- The chatbot cannot do the job (it can't hear), but it **names our evaluation plan** (test on labelled kitchen recordings) and our honest limit. Our edge over it must be measured: actual per-activity numbers on SINS and our kitchens, where it can only say "I can't give a percentage".
- Copy rule for stage 3: Kettle says "kitchen activity: cooking 8:20–8:40", never "Dad ate breakfast". The SINS "eating" class exists but is weak; report it honestly.
- It independently suggests the "no X by 11 AM" pattern alert, which matches theme 10b.
