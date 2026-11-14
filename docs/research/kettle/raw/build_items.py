"""Collect every review/post gathered for the Kettle teardown into one list (items.json).
Sources: App Store RSS JSON (fetched directly) and the read-only Aside research write-ups in this folder.
Each item: id, product, source, url, rating (None if no stars), date, text (paraphrase or review text), kind (review|post|press)."""
import json, re, os
ASIDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../.overnight/kettle/aside/")  # raw Aside transcripts: local only (they contain reviewer names)
items = []
def add(product, source, url, rating, date, text, kind="review"):
    items.append(dict(id=f"{product}-{len(items)+1:03d}", product=product, source=source, url=url,
                      rating=rating, date=date, text=text.strip(), kind=kind))

# 1. App Store reviews (all products; Snug only <=4 stars because its 327 five-star check-in reviews would swamp the sensor products)
store = json.load(open("appstore-reviews.json"))
names = {"howz": "Howz", "canarycare": "Canary Care", "assistiv": "Assistiv", "caredaily": "Care Daily",
         "stackcare": "StackCare", "caregiver-aware": "Caregiver (Cognitive)", "parentsareok": "Parents are OK", "snug": "Snug"}
for k, revs in store.items():
    if k not in names: continue
    for r in revs:
        if k == "snug" and r["rating"] == 5: continue
        add(names[k], f"App Store {r['cc'].upper()}", r["url"], r["rating"], r["date"], r["title"] + ". " + r["text"])

# 2. Howz: Google Play + Trustpilot paraphrases (aside-howz.txt)
t = open(ASIDE + "aside-howz.txt").read()
play = t[t.find("## 2. Google Play reviews"):t.find("## 3. Trustpilot")]
for m in re.finditer(r"- (\d) stars?, (\d+ \w+ \d{4}), [^:]+: (.+)", play):
    add("Howz", "Google Play", "https://play.google.com/store/apps/details?id=com.intelesant.howz", int(m[1]), m[2], m[3])
tp = t[t.find("## 3. Trustpilot"):t.find("**Apple App Store UK")]
for m in re.finditer(r"- (\d) stars?, (\d+ \w+ \d{4}), [^:]+: (.+)", tp):
    add("Howz", "Trustpilot", "https://uk.trustpilot.com/review/howz.com", int(m[1]), m[2], m[3])

# 3. Canary Care: Trustpilot (112), Play (3), forums (aside-canary-final.txt)
t = open(ASIDE + "aside-canary-final.txt").read()
s1 = t[t.find("## 1. Trustpilot"):t.find("## 2. Trustpilot")]
for m in re.finditer(r"\d+\. (\d)★, (\d{4}-\d\d-\d\d), [^:]+: (.+?) (https://\S+)", s1):
    add("Canary Care", "Trustpilot", m[4], int(m[1]), m[2], m[3])
s2 = t[t.find("## 2. Trustpilot"):t.find("## 3. Google Play")]
for m in re.finditer(r"\d+\. (\d{4}-\d\d-\d\d), [^:]+: (.+) ([0-9a-f]{24})\s*$", s2, re.M):
    add("Canary Care", "Trustpilot", "https://uk.trustpilot.com/reviews/" + m[3], 5, m[1], m[2])
s3 = t[t.find("## 3. Google Play"):t.find("## 4. Forum")]
for m in re.finditer(r"- (\d{4}-\d\d-\d\d), [^:]+: (.+)", s3):
    add("Canary Care", "Google Play", "https://play.google.com/store/apps/details?id=uk.co.canarycare.android", None, m[1], m[2])
s4 = t[t.find("## 4. Forum"):t.find("Not found: no Amazon")]
for m in re.finditer(r"- ([\d-]+), ([^,]+), [^:]+: (.+?) (https?://\S+)", s4):
    add("Canary Care", m[2], m[4], None, m[1], m[3], "post")

# 4. Alexa Together / Emergency Assist (aside-alexa-final.txt), numbered list
t = open(ASIDE + "aside-alexa-final.txt").read()
s = t[t.find("## 3. User opinions"):]
last_url = None
for m in re.finditer(r"^(\d+)\. (.+)$", s, re.M):
    line = m[2]
    u = re.findall(r"https?://\S+", line)
    if u: last_url = u[-1].rstrip(".")
    d = re.search(r"(\d{4}-\d\d-\d\d|\d{4}-\d\d|\w+ \d{4}|spring \d{4})", line)
    stars = re.search(r"score (\d+)/10", line)
    add("Alexa Together / Emergency Assist", line.split(",")[0][:40], last_url, None, d[1] if d else "", re.sub(r"https?://\S+", "", line), "post")

json.dump(items, open("items.json", "w"), indent=1, ensure_ascii=False)
from collections import Counter
print(len(items), Counter(i["product"] for i in items))

# 5. Reddit caregiver/older-adult voice (aside-reddit-final.txt): 12 threads, 75 comments; founder/promo (F) kept but tagged
t = open(ASIDE + "aside-reddit-final.txt").read()
t = t[t.find("**1. r/eldercare"):t.find("**Patterns across all 12:**")]
url = None; sub = None; year = None
for line in t.split("\n"):
    m = re.match(r"\*\*\d+\. (r/\w+),", line)
    if m: sub = m[1]; continue
    m = re.match(r"(https://www\.reddit\.com/\S+) \(posted (\d{4})", line)
    if m: url, year = m[1], m[2]; continue
    m = re.match(r"- ([A-Z/?-]+(?:-side|-leaning)?)(?: \(OP[^)]*\))?(?:, ([\d-]+)(?: reply)?)?: (.+)", line)
    if m and url:
        role = m[1]; date = m[2] or ""
        if date and len(date) == 5: date = f"{year}-{date}"
        add("Reddit (no product)", sub, url, None, date, f"[{role}] {m[3]}", "post")

# 6. Apple Sound Recognition opinions (aside-havn-assistiv-apple.txt), 19 items
t = open(ASIDE + "aside-havn-assistiv-apple.txt").read()
t = t[t.find("**User opinions (19)**"):t.find("**Gaps**", t.find("**User opinions (19)**"))]
last = None
for m in re.finditer(r"^\d+\. (.+)$", t, re.M):
    line = re.sub(r'<citation refs="[^"]*">|</citation>', "", m[1])
    u = re.findall(r"https?://\S+", line)
    if u: last = u[0]
    d = re.search(r"\((\d{4}-\d\d-\d\d|\w+ \d+ \d{4})", line)
    add("Apple Sound Recognition", "Reddit/Apple Community", last, None, d[1] if d else "", re.sub(r"https?://\S+ ", "", line), "post")

json.dump(items, open("items.json", "w"), indent=1, ensure_ascii=False)
print(len(items), Counter(i["product"] for i in items))

# 7. Care Daily Google Play written reviews (aside-stack-caredaily-final.txt), 9 items
t = open(ASIDE + "aside-stack-caredaily-final.txt").read()
t = t[t.find("**All Play reviews"):t.find("Distribution is 20")]
for m in re.finditer(r"- (\d) stars?, (\w+ \d+, \d{4})(?: \([^)]*\))?: (.+)", t):
    add("Care Daily", "Google Play", "https://play.google.com/store/apps/details?id=com.peoplepowerco.family", int(m[1]), m[2], m[3])
json.dump(items, open("items.json", "w"), indent=1, ensure_ascii=False)
print(len(items), Counter(i["product"] for i in items))
