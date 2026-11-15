"""Kettle's safety layer in Python: a line-for-line mirror of web/public/js/safety.js (plan v3.1, Workstream E).

Danger detectors read the AudioSet scores CED-tiny already computes for each window; a pattern detector finds the
NFPA 72 smoke (T3) and carbon monoxide (T4) beep rhythms in the loudness envelope; a small sequence engine turns
detections plus time into "Urgent" or "Worth a look" alerts. Thresholds: web/public/model/safety.json, written by
eval/safety.py. web/test/safety.test.mjs replays web/test/safety_fixtures.json (made here) through the JS twin and
checks the answers are identical. The rule table is in the JS file's header and in docs/DECISIONS.md.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG: dict = json.loads((ROOT / "web" / "public" / "model" / "safety.json").read_text())

CHECKIN_S = {"fall": 60, "scream": 30, "shout": 30, "distress": 60, "stillness": 60}
FALL_DISTRESS_S, FALL_STILL_S, FALL_CANCEL_S, ACTIVE_BEFORE_S = 60, 120, 120, 1800   # v3.5: 2-minute stillness (was 10)
SCREAM_S, DISTRESS_S, SEPARATE_S, MEDIA_WINDOWS = 120, 300, 10, 3
SHOUT_S, SHOUTS = 60, 3
COOLDOWN_S, SMOKE_CLEAR_S = 600, 300
STOVE_S, STOVE_GAP_S, BEEP_S, BEEP_GAP_S, WATER_S, WATER_SHARE = 2400, 180, 300, 120, 1200, 0.8
KEEP_S, STRAY = 2 * 3600, 2
COOKING_KINDS = ["frying", "kettle", "boiling"]
OTHER_KITCHEN = ["dishes", "cutlery", "tap", "chopping", "cupboard", "drawer", "microwave", "blender", "pouring", "stirring"]
TEXT = {
    "smoke": "a smoke alarm", "co": "what sounds like a carbon monoxide alarm", "fall": "a crash, then a groan or cry",
    "fall_still": "a crash, then no movement for 2 minutes", "scream": "screaming", "shout": "shouting, again and again",
    "gunshot": "what sounded like a gunshot", "distress": "repeated groaning or crying",
    "help": "the I need help button", "stillness": "no activity for hours",
    "stove": "frying or boiling for 40 minutes with nothing else heard", "beep": "a timer or appliance beeping for 5 minutes",
    "water": "running water for 20 minutes", "scream_tv": "screaming while the TV or music was on",
    "gunshot_tv": "a bang like a gunshot while the TV or music was on", "test": "a test alert",
}


def _r3(x: float) -> float:
    """JS Math.round(x * 1000) / 1000 (halves round up, as in JS)."""
    return math.floor(x * 1000 + 0.5) / 1000


def detect(scores, cfg: dict = CFG) -> dict:
    """One window's AudioSet scores [527] -> {scores: {id: max}, hits: [ids over threshold], media: bool}."""
    out, hits = {}, []
    for d in cfg["detectors"]:
        s = max(float(scores[i]) for i in d["index"])
        out[d["id"]] = _r3(s)
        if s >= d["tau"]:
            hits.append(d["id"])
    m = max(float(scores[i]) for i in cfg["media"]["index"])
    return {"scores": out, "hits": hits, "media": m >= cfg["media"]["tau"]}


def envelope(wave, sr: int = 16000, frame_s: float = 0.05) -> list[float]:
    """dB per 50-ms frame of the first-differenced signal (a cheap high-pass that keeps alarm tones)."""
    n = int(sr * frame_s)
    out = []
    for f in range(len(wave) // n):
        seg = wave[f * n:(f + 1) * n]
        s = float(sum((float(seg[i]) - float(seg[i - 1])) ** 2 for i in range(1, n)))
        out.append(10 * math.log10(s / n) if s > 0 else -120.0)
    return out


def envelope_np(wave, sr: int = 16000, frame_s: float = 0.05) -> list[float]:
    """envelope() with numpy (same numbers, much faster), for evaluation scripts."""
    import numpy as np
    n = int(sr * frame_s)
    frames = len(wave) // n
    x = np.asarray(wave[:frames * n], dtype=np.float64).reshape(frames, n)
    s = (np.diff(x, axis=1) ** 2).sum(axis=1)
    return [10 * math.log10(v / n) if v > 0 else -120.0 for v in s]


def alarm_pattern(env: list[float], frame_s: float = 0.05) -> dict:
    """Complete T3 (three ~0.5-s beeps, ~1.5 s off) and T4 (four ~0.1-s beeps, ~5 s off) cycles in an envelope."""
    if not env:
        return {"t3": 0, "t4": 0}
    srt = sorted(env)
    floor = srt[int(0.2 * (len(srt) - 1))]
    if srt[-1] - floor < 12:
        return {"t3": 0, "t4": 0}
    segs: list[list] = []                 # [is_on, seconds, summed dB, frames]
    for v in env:
        on = v >= floor + 12
        if segs and segs[-1][0] == on:
            segs[-1][1] += frame_s
            segs[-1][2] += v
            segs[-1][3] += 1
        else:
            segs.append([on, frame_s, v, 1])

    def steady(ks):                        # an alarm beeps at one level
        lv = [segs[k][2] / segs[k][3] for k in ks]
        return max(lv) - min(lv) <= 6

    def near(x, lo, hi):
        return lo - 1e-9 <= x <= hi + 1e-9

    def seg(k):
        return segs[k] if k < len(segs) else None

    t3 = t4 = 0
    for i, s in enumerate(segs):
        if not s[0]:
            continue
        if (all(seg(i + k) and seg(i + k)[0] and near(seg(i + k)[1], 0.35, 0.7) for k in (0, 2, 4))
                and all(seg(i + k) and near(seg(i + k)[1], 0.3, 0.7) for k in (1, 3)) and seg(i + 5) and near(seg(i + 5)[1], 1.1, 2.2) and steady([i, i + 2, i + 4])):
            t3 += 1
        if (all(seg(i + k) and seg(i + k)[0] and near(seg(i + k)[1], 0.05, 0.2) for k in (0, 2, 4, 6))
                and all(seg(i + k) and near(seg(i + k)[1], 0.05, 0.2) for k in (1, 3, 5)) and seg(i + 7) and seg(i + 7)[1] >= 2.5 and steady([i, i + 2, i + 4, i + 6])):
            t4 += 1
    return {"t3": t3, "t4": t4}


# ---------------------------------------------------------------- the sequence engine
def new_engine() -> dict:
    return {"hist": [], "lastActive": None, "pending": None, "checkin": None, "last": {}, "smokeSince": None, "coSince": None,
            "stoveFrom": None, "stoveSeen": None, "beepFrom": None, "beepSeen": None, "waterFrom": None, "waterN": 0, "waterHit": 0}


def is_active(w: dict) -> bool:
    if w.get("kinds"):
        return True
    if w.get("floor") is not None and w.get("db") is not None:
        return w["db"] >= w["floor"] + 3
    return bool(w.get("label")) and w["label"] != "absence"


def _cooks(w: dict) -> bool:
    return w.get("label") in ("cooking", "dishwashing", "eating") or any(k in COOKING_KINDS or k in OTHER_KITCHEN for k in w.get("kinds") or [])


def _has(w: dict, i: str) -> bool:
    return i in (w.get("hits") or [])


def _separate(ws: list[dict], i: str, since: float) -> int:
    n, prev = 0, -math.inf
    for w in ws:
        if w["t"] >= since and _has(w, i) and w["t"] - prev >= SEPARATE_S:
            n += 1
            prev = w["t"]
    return n


def _alert(st, t, tier, typ, **extra) -> dict:
    st["last"][typ] = t
    return {"do": "alert", "tier": tier, "type": typ, "at": t, "text": TEXT[typ], **extra}


def _cool(st, typ, t) -> bool:
    return st["last"].get(typ) is None or t - st["last"][typ] >= COOLDOWN_S


def _start_checkin(st, t, rule, typ, evidence) -> dict:
    st["checkin"] = {"rule": rule, "type": typ, "at": t, "deadline": t + CHECKIN_S[rule], "evidence": evidence}
    st["last"][typ] = t
    return {"do": "checkin", "rule": rule, "type": typ, "at": t, "deadline": st["checkin"]["deadline"], "text": TEXT[typ]}


def _ev(w: dict, ids: list[str], pat: dict | None = None) -> dict:
    e = {i: w["scores"][i] for i in ids if w.get("scores") and w["scores"].get(i) is not None}
    if pat and (pat.get("t3") or pat.get("t4")):
        e.update({"t3": pat["t3"], "t4": pat["t4"]})
    return e


def step(st: dict, w: dict, urgent: bool = True, concern: bool = True, paused: bool = False, smoke_while_paused: bool = False) -> list[dict]:
    """One window (5-s hop) -> actions. Same contract as safety.js step()."""
    t, out = w["t"], []
    st["hist"].append({"t": t, "hits": w.get("hits") or [], "media": bool(w.get("media")) or w.get("label") == "watching_tv",
                       "active": is_active(w), "cooks": _cooks(w), "kinds": w.get("kinds") or [], "label": w.get("label")})
    st["hist"] = [h for h in st["hist"] if h["t"] > t - KEEP_S]
    h = st["hist"]
    me = h[-1]
    if me["active"]:
        st["lastActive"] = t
    out += timeouts(st, t)
    if not urgent and not concern:
        return out
    last3 = h[-3:]
    pat = w.get("pattern") or {"t3": 0, "t4": 0}
    me["t3"], me["t4"] = pat["t3"], pat["t4"]
    if urgent and (not paused or smoke_while_paused):
        smoke = sum(1 for x in last3 if _has(x, "smoke_alarm")) >= 2 or pat["t3"] >= 2
        if smoke:
            if st["smokeSince"] is None:
                st["smokeSince"] = t - 10
                out.append(_alert(st, t, "urgent", "smoke", since=st["smokeSince"], evidence=_ev(w, ["smoke_alarm"], pat)))
        elif st["smokeSince"] is not None and not any(x["t"] > t - SMOKE_CLEAR_S and (_has(x, "smoke_alarm") or x.get("t3")) for x in h):
            st["smokeSince"] = None
        co = _separate([{**x, "hits": ["t4"] if (x.get("t4") or 0) >= 1 else []} for x in h], "t4", t - 40) >= 2
        if co:
            if st["coSince"] is None:
                st["coSince"] = t - 10
                out.append(_alert(st, t, "urgent", "co", since=st["coSince"], evidence=_ev(w, ["smoke_alarm"], pat)))
        elif st["coSince"] is not None and not any(x["t"] > t - SMOKE_CLEAR_S and x.get("t4") for x in h):
            st["coSince"] = None
    if paused:
        return out
    media = any(x["media"] for x in h[-MEDIA_WINDOWS:])
    if urgent and (_has(me, "impact") or _has(me, "glass")) and not media and not st["pending"] and not st["checkin"]:
        before = any(x["t"] < t - 5 and x["t"] >= t - ACTIVE_BEFORE_S and x["active"] for x in h)
        st["pending"] = {"at": t, "before": before, "evidence": _ev(w, ["impact", "glass"])}
    if st["pending"] and not st["checkin"]:
        p = st["pending"]
        after = [x for x in h if x["t"] > p["at"] + 5]
        if any(x["t"] <= p["at"] + FALL_CANCEL_S and x["cooks"] for x in after):
            st["pending"] = None
        elif any(x["t"] <= p["at"] + FALL_DISTRESS_S and (_has(x, "distress") or _has(x, "scream")) for x in after):
            st["pending"] = None
            out.append(_start_checkin(st, t, "fall", "fall", {**p["evidence"], **_ev(w, ["distress", "scream"])}))
        elif t - p["at"] >= FALL_STILL_S:
            st["pending"] = None
            if p["before"] and sum(1 for x in after if x["active"]) <= STRAY:
                out.append(_start_checkin(st, t, "fall", "fall_still", p["evidence"]))
    if not st["checkin"] and (_separate(h, "scream", t - SCREAM_S) >= 2
                              or (_has(me, "scream") and any(x["t"] > t - SCREAM_S and _has(x, "distress") for x in h))):
        if media:
            if concern and _cool(st, "scream_tv", t):
                out.append(_alert(st, t, "concern", "scream_tv", evidence=_ev(w, ["scream"])))
        elif urgent and _cool(st, "scream", t):
            out.append(_start_checkin(st, t, "scream", "scream", _ev(w, ["scream", "distress"])))
    if _has(me, "gunshot"):                                   # U8: straight to the family; with media on, only a note
        if media:
            if concern and _cool(st, "gunshot_tv", t):
                out.append(_alert(st, t, "concern", "gunshot_tv", evidence=_ev(w, ["gunshot"])))
        elif urgent and _cool(st, "gunshot", t):
            out.append(_alert(st, t, "urgent", "gunshot", since=t, evidence=_ev(w, ["gunshot"])))
    if urgent and not st["checkin"] and not media and _cool(st, "shout", t) and _separate(h, "shout", t - SHOUT_S) >= SHOUTS:   # U9
        out.append(_start_checkin(st, t, "shout", "shout", _ev(w, ["shout"])))
    if (urgent and not st["checkin"] and not media and _cool(st, "distress", t) and _separate(h, "distress", t - DISTRESS_S) >= 3
            and not any(x["t"] > t - DISTRESS_S and x["cooks"] for x in h)):
        out.append(_start_checkin(st, t, "distress", "distress", _ev(w, ["distress"])))
    if concern:
        out += _device_concerns(st, w, t)
    return out


def _device_concerns(st: dict, w: dict, t: float) -> list[dict]:
    out, k = [], w.get("kinds") or []
    if any(x in COOKING_KINDS for x in k):
        if st["stoveFrom"] is None or t - st["stoveSeen"] > STOVE_GAP_S:
            st["stoveFrom"] = t
        st["stoveSeen"] = t
    if any(x in OTHER_KITCHEN or x == "footsteps" for x in k):
        st["stoveFrom"] = t if st["stoveSeen"] is not None else None
    if (st["stoveFrom"] is not None and t - st["stoveSeen"] <= STOVE_GAP_S and t - st["stoveFrom"] >= STOVE_S and _cool(st, "stove", t)):
        out.append(_alert(st, t, "concern", "stove", since=st["stoveFrom"]))
    if "beep" in (w.get("hits") or []) or "timer" in k:
        if st["beepFrom"] is None or t - st["beepSeen"] > BEEP_GAP_S:
            st["beepFrom"] = t
        st["beepSeen"] = t
    if st["beepFrom"] is not None and t - st["beepSeen"] <= BEEP_GAP_S and t - st["beepFrom"] >= BEEP_S and _cool(st, "beep", t):
        out.append(_alert(st, t, "concern", "beep", since=st["beepFrom"]))
    tap = "tap" in k
    if tap and st["waterFrom"] is None:
        st["waterFrom"], st["waterN"], st["waterHit"] = t, 0, 0
    if st["waterFrom"] is not None:
        st["waterN"] += 1
        st["waterHit"] += 1 if tap else 0
        if st["waterHit"] / st["waterN"] < WATER_SHARE:
            st["waterFrom"] = None
        elif t - st["waterFrom"] >= WATER_S and _cool(st, "water", t):
            out.append(_alert(st, t, "concern", "water", since=st["waterFrom"]))
    return out


def timeouts(st: dict, t: float) -> list[dict]:
    if not st["checkin"] or t < st["checkin"]["deadline"]:
        return []
    c = st["checkin"]
    st["checkin"] = None
    return [{"do": "alert", "tier": "urgent", "type": c["type"], "at": t, "since": c["at"], "text": TEXT[c["type"]],
             "checkin": "no_answer", "evidence": c["evidence"]}]


def answer(st: dict, t: float, reply: str) -> list[dict]:
    if not st["checkin"]:
        return [help_button(st, t)] if reply == "help" else []
    c = st["checkin"]
    st["checkin"] = None
    if reply == "help":
        return [{"do": "alert", "tier": "urgent", "type": "help", "at": t, "since": c["at"], "text": TEXT["help"], "checkin": "help",
                 "after": c["type"], "evidence": c["evidence"]}]
    return [{"do": "alert", "tier": "concern", "type": c["type"], "at": t, "since": c["at"], "text": TEXT[c["type"]], "checkin": "ok",
             "evidence": c["evidence"]}]


def help_button(st: dict, t: float) -> dict:
    st["last"]["help"] = t
    return {"do": "alert", "tier": "urgent", "type": "help", "at": t, "since": t, "text": TEXT["help"], "checkin": "help"}


def ask_stillness(st: dict, t: float) -> list[dict]:
    if st["checkin"] or not _cool(st, "stillness", t):
        return []
    return [_start_checkin(st, t, "stillness", "stillness", {})]


def cough_concern(days: list[float], today: float) -> dict | None:
    v = sorted([d for d in days if isinstance(d, (int, float)) and math.isfinite(d)][-7:])     # the last 7 days, then sorted
    if len(v) < 3:
        return None
    med = v[(len(v) - 1) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2
    if today > 3 * max(med, 2):
        return {"ratio": math.floor((today / max(med, 1)) * 10 + 0.5) / 10}
    return None
