"""Code every collected item into pain themes with transparent keyword rules (one coder: the teardown agent).
A theme counts only when the item expresses that pain (not praise). Output: coded.json + printed counts.
Severity (1-3) is the agent's judgement of harm to the parent/caregiver if the pain happens; stated in pain-points.md."""
import json, re
from collections import Counter, defaultdict
items = json.load(open("items.json"))
T = {  # theme: (severity, regex on lowercased text)
 "missed_real_problem": (3, r"didn'?t (alert|send|notify|recogni|pick)|no alerts? at all|never (actually )?(seen it )?(set off|went off)|failed in the actual|forgot the watch|smoke alerts? (don'?t|came through about)|doesn'?t get my notif|no baby-crying alert|undiscovered|found hours later|lay .* hours|on the floor for 2 hours|sometimes doesn'?t see a missed|not consistently|then none did|can'?t start a 911|only caught|stuck on \"being trained\"|hours later"),
 "false_alarms": (2, r"false|unnecessary panic|erroneous|annoying notif|every 5 minutes|30 notifications|knock alerts|misrecogni|too sensitive|very sensitive|going off|police officers came|cops\" got called|triggered false|anxious because they arrive|so mad when she answered|good-morning text pact|went 6\+ hours|throw \"a lot of false|mistaking dad|false identification|keeps pinging|pinging him daily|water running\" alert while"),
 "dignity_surveillance": (3, r"spying|spied|surveil|intrusi(on|ve)|hated (it|cameras)|felt like spying|hovering|micromanag|helicopter|step too far|hard no|privacy pushback|wouldn'?t want her phone|never tell them where|overkill|doesn'?t mean someone needs tracking|looks like spying|camera.*(objection|refuse)|refuse cameras|not wanting cameras|insisting\" on privacy|feel natural"),
 "consent_overridden": (3, r"didn'?t ask, i just did|unplugs them|doesn'?t really know what they are|objection usually comes from the parent|parents themselves refuse|refuse fall devices|they refuse|wouldn'?t wear|won'?t buy|say no to both|paranoia"),
 "price_subscription": (2, r"expensive|overpriced|\$\d|£\d|per month|a month|/month|subscription|joke\.|charging|charged|billing|cost|cheaper|fee\b|paid support"),
 "cancel_support_refund": (1, r"cancel|refund|support (went quiet|is also unreliable)|agent hung up|hung up|no response from company|customer service\. awful|keep billing|continue charging"),
 "app_bugs_logins": (1, r"log(s|ged)? (you )?out|logs you out|crash|won'?t open|not open at all|fails to open|re-?download|password|verification code|error (message|when)|stopped asking|bug|update (stopped|broke)|charts out of sync|icon won'?t|can'?t sign up|can'?t just log|uglier|redesign|not searchable|not compatible|apple pay"),
 "hub_wifi_battery_power": (2, r"hub (is )?forever going down|wifi|wi-fi|battery|batteries|charg(ed|ing) every|hardwired|power cut|power (hog|issues)|% of (my )?(battery|power)|phone battery died|internet|within wi-fi range|flicker"),
 "silent_failure_no_news": (3, r"forever going down|no information from the sensors|stale|sporadic|no notices are sent|may or may not work|didn'?t want my contact people to get an erroneous|unsure if .* worked|can'?t tell|is it working|still working|offline"),
 "install_hardware": (1, r"install(ation)? (problem|fail)|setup problem|initial setup problem|needs a room sensor|fix sensors lower|proprietary hub|setup work|ugly|requires their alarm system|re-setup|dead end|confusing|can'?t be used as an emergency contact|hard spot|placed low"),
 "cold_start_learning": (1, r"learning period|two-week|7 to 14 days|learn(s|ing)? (the )?routine|baseline over"),
 "raw_data_not_meaning": (2, r"how you decide \"she'?s good\"|need the opposite|no motion for x|lack of motion|alert on(ly)? motion|inverse|multi-sensor logic|enough information to say she is ok|needs to be slicker|less clear|too much data|raw|not worth \$20|high-level view"),
 "wants_no_activity_by_time": (2, r"no motion by|no movement by|no motion for x|when there'?s no motion|lack of motion|nobody'?s detected by a set time|didn'?t show up one day|hadn'?t picked up his mail|no movement one day|first-activity|first activity|activity alerts|no-activity|no-motion|alert(ing)? on lack"),
 "burden_on_older_adult": (2, r"has to (actually )?use alexa|must be conscious|forgot|forgotten|leave(s)? (her|his) phone|phone on silent|check in at exactly|only allows daily|adhd|single day check|twice daily|wouldn'?t think to use|panicked|wouldn'?t call|can'?t use it|cover it|pendant comes off|left on the nightstand|getting her to pick up|quotes?|quotation|turn the phone away|deleted it|needs to be charged|has to be charged"),
 "siblings_sharing": (1, r"sister|brother|siblings|took turns|whole family|only one of my emergency contacts|only the primary caregiver|circle"),
 "product_discontinued": (2, r"discontinu|no longer (available|supported)|sunset|abandoned|ending in a month|killed echo connect|disabled echo connect|changed hands|silently turned into a paid|no software left|withdrawn|forgot about it|letter\.\.\. immensely"),
}
counts = Counter(); per = defaultdict(list); prods = defaultdict(Counter)
for it in items:
    txt = it["text"].lower()
    praise_only = (it["rating"] or 0) >= 5 and not re.search(r"\bbut\b|however|only|wish|annoy|problem|glitch|fault|slightly|blip", txt)
    it["themes"] = []
    if praise_only: continue
    for th, (sev, rx) in T.items():
        if re.search(rx, txt):
            # price words inside praise ("cheap versus rivals") are not pain
            if th == "price_subscription" and re.search(r"cheap versus|beats no way|not too much|no monthly fee|cheaper than a facility", txt): continue
            it["themes"].append(th); counts[th] += 1; per[th].append(it); prods[th][it["product"]] += 1
# Manual review pass (agent read every match; see pain-points.md "Method"): remove false positives, add misses.
REMOVE = {"burden_on_older_adult": ["039","073","393","296"],
          "price_subscription": ["049","053","069","292","304","361","365","290","250","272"],
          "dignity_surveillance": ["016","028","276","295","331"],
          "siblings_sharing": ["052","071","370","028"],
          "hub_wifi_battery_power": ["343","360","404"],
          "raw_data_not_meaning": ["233","259"],
          "consent_overridden": ["262"],
          "install_hardware": ["341"],
          "app_bugs_logins": ["232"],
          "cancel_support_refund": ["067"]}
ADD = {"silent_failure_no_news": ["077","086"], "false_alarms": [i["id"][-3:] for i in items if "aren't always accurate" in i["text"]], "install_hardware": [], "consent_overridden": ["334","369"],
       "dignity_surveillance": ["341"], "price_subscription": ["057"], "app_bugs_logins": [i["id"][-3:] for i in items if re.search(r"behind in time|too much trouble to turn devices|New Zealand phone", i["text"])]}
mike = [i for i in items if "sensors lower than" in i["text"]]
for i in mike: ADD["install_hardware"].append(i["id"][-3:]); ADD.setdefault("missed_real_problem", []).append(i["id"][-3:])
byid = {i["id"][-3:]: i for i in items}
for th, ids in REMOVE.items():
    for x in ids:
        if th in byid[x]["themes"]: byid[x]["themes"].remove(th)
for th, ids in ADD.items():
    for x in ids:
        if th not in byid[x]["themes"]: byid[x]["themes"].append(th)
counts = Counter(); prods = defaultdict(Counter)
for it in items:
    for th in it["themes"]: counts[th] += 1; prods[th][it["product"]] += 1
json.dump(items, open("coded.json", "w"), indent=1, ensure_ascii=False)
coded = sum(1 for i in items if i["themes"])
print("items", len(items), "items with >=1 pain theme", coded)
for th, n in counts.most_common():
    print(f"{th:28s} n={n:3d} sev={T[th][0]} score={n*T[th][0]:4d}  {dict(prods[th])}")
