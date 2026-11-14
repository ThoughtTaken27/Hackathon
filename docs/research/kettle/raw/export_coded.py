"""Write coded-items.csv (every item: link, product, stars, date, one-line text, themes) and theme-examples.md."""
import json, csv, re
from collections import Counter, defaultdict
items = json.load(open("coded.json"))
def oneline(it):
    t = re.sub(r"\s+", " ", it["text"])
    # drop usernames that open Alexa/forum lines: "r/alexa, Name, 2024-05-01. " / "Amazon Forum, Name, date. "
    t = re.sub(r"^(Same thread|r/\w+|Amazon Forum|Substack|The Verge review|Tech-enhanced Life|Reviewed\.com|Livingetc)(, [^,.]+)?(, [^.]*?\d{4}[^.]*)?\. ", r"\1. ", t)
    t = re.sub(r"\((Rachael|Katy|Phillip|Craig|Chris|Sandra)[^)]*\)", "", t)
    t = re.sub(r"\b[A-Z][A-Za-z]+_[A-Za-z]+\d*\b ", "a user ", t)
    return t[:180] + ("…" if len(t) > 180 else "")
with open("../coded-items.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "product", "source", "stars", "date", "kind", "themes", "one_line", "url"])
    for it in items:
        w.writerow([it["id"], it["product"], it["source"], it["rating"] if it["rating"] is not None else "", it["date"], it["kind"], ";".join(it["themes"]), oneline(it), it["url"]])
per = defaultdict(list)
for it in items:
    for th in it["themes"]: per[th].append(it)
with open("theme-examples.md", "w") as f:
    for th, lst in sorted(per.items(), key=lambda kv: -len(kv[1])):
        f.write(f"\n### {th} ({len(lst)})\n")
        for it in lst:
            f.write(f"- {it['id']} · {it['product']} · {it['rating'] or '–'}★ · {it['date']} · {oneline(it)} · {it['url']}\n")
print("rows", len(items))
