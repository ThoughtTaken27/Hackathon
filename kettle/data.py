"""SINS / DCASE 2018 Task 5 data: labels, folds, and rate-limited clip fetching from Zenodo.

The full dataset is 46 GB of zips, so we never download a zip. We read each zip's directory once
(an index of where every clip sits) and then fetch one clip with one HTTP range request.
Zenodo allows about 133 requests a minute, so requests are spaced 0.5 s apart.

Usage:
    python -m kettle.data plan           # print the training subset and demo sessions, fetch nothing
    python -m kettle.data fetch-dev      # training subset -> data/clips/dev/*.flac (4 channels)
    python -m kettle.data fetch-demo     # held-out demo sessions -> data/clips/demo/*.flac
    python -m kettle.data fetch-eval     # pre-registered eval sample -> data/clips/eval/ (see eval/sample.py)
"""
from __future__ import annotations

import io
import json
import random
import re
import struct
import sys
import threading
import time
import zipfile
import zlib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf

from kettle.labels import CLASSES

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "data" / "meta"
RAW = ROOT / "data" / "raw" / "sins"           # git-ignored: zip indexes
CLIPS = ROOT / "data" / "clips"                # git-ignored: fetched audio
JOBS = ROOT / ".overnight" / "kettle" / "jobs"  # progress logs
RECORDS = {
    "dev": ("1247102", "DCASE2018-task5-dev.audio.{}.zip"),
    "eval": ("1291760", "DCASE2018-task5-eval.audio.{}.zip"),
}
MIN_GAP_S = 0.5           # Zenodo guest limit is 133 requests/minute; stay under 120
TRAIN_CAP_PER_CLASS = 1000
DEMO_SEGMENTS = 10        # contiguous 10-s clips kept per held-out demo session
DEMO_NODE = "DevNode1"
SEED = 0

_NAME = re.compile(r"(DevNode\d|EvalNode\d)_ex(\d+)_(\d+)\.wav")


# ---------------------------------------------------------------- labels and folds

def parse_name(name: str) -> dict:
    """'DevNode1_ex100_3.wav' -> {'node': 'DevNode1', 'ex': 100, 'seg': 3}."""
    m = _NAME.match(name)
    return {"node": m.group(1), "ex": int(m.group(2)), "seg": int(m.group(3))}


def dev_folds() -> dict[str, int]:
    """Clip name -> the official fold (1-4) whose test list contains it."""
    out = {}
    for k in range(1, 5):
        for line in open(META / "dev" / "evaluation_setup" / f"fold{k}_evaluate.txt"):
            out[Path(line.split("\t")[0]).name] = k
    return out


def load_meta(split: str) -> list[dict]:
    """Every clip of a split as {file, label, session, node, ex, seg, fold}.

    For eval, `file` is the anonymised zip name ('1.wav') and `orig` the real node name
    from map.txt (published with the labels in Zenodo record 1964758).
    """
    rows = []
    if split == "dev":
        fold = dev_folds()
        for line in open(META / "dev" / "meta.txt"):
            f, label, session = line.rstrip("\n").split("\t")
            name = Path(f).name
            rows.append({"file": name, "label": label, "session": session, **parse_name(name),
                         "fold": fold[name]})
    elif split == "eval":
        orig = {}
        for line in open(META / "eval" / "map.txt"):
            a, b = line.rstrip("\n").split("\t")
            orig[Path(b).name] = Path(a).name
        for line in open(META / "eval" / "meta.txt"):
            f, label, session = line.rstrip("\n").split("\t")
            name = Path(f).name
            rows.append({"file": name, "label": label, "session": session, "orig": orig[name],
                         **parse_name(orig[name]), "fold": None})
    else:
        raise ValueError(split)
    return rows


# ---------------------------------------------------------------- choosing clips

def demo_sessions(meta: list[dict], seed: int = SEED) -> dict[str, str]:
    """One whole dev session per activity, held out of training, used for demo days and golden clips.

    Picks, per class, a random session that has at least DEMO_SEGMENTS segments on DEMO_NODE.
    """
    segs = defaultdict(set)
    for r in meta:
        if r["node"] == DEMO_NODE:
            segs[(r["label"], r["session"])].add(r["seg"])
    rng, out = random.Random(seed), {}
    for c in CLASSES:
        ok = sorted(s for (lab, s), v in segs.items() if lab == c and len(v) >= DEMO_SEGMENTS)
        out[c] = rng.choice(ok)
    return out


def demo_clips(meta: list[dict], sessions: dict[str, str]) -> list[dict]:
    """The first DEMO_SEGMENTS segments (in time order) of each demo session, on DEMO_NODE."""
    out = []
    for c, s in sessions.items():
        rows = sorted((r for r in meta if r["session"] == s and r["node"] == DEMO_NODE), key=lambda r: r["seg"])
        out += rows[:DEMO_SEGMENTS]
    return out


def training_subset(meta: list[dict], held_out: set[str], cap: int = TRAIN_CAP_PER_CLASS,
                    seed: int = SEED) -> list[dict]:
    """Up to `cap` clips per class, round-robin over sessions so every session and node appears.

    Sessions in `held_out` (the demo sessions) are never chosen.
    """
    rng = random.Random(seed)
    by = defaultdict(lambda: defaultdict(list))
    for r in meta:
        if r["session"] not in held_out:
            by[r["label"]][r["session"]].append(r)
    chosen = []
    for c in CLASSES:
        pools = {s: rng.sample(v, len(v)) for s, v in sorted(by[c].items())}
        order = sorted(pools)
        rng.shuffle(order)
        picked = []
        while len(picked) < cap and any(pools.values()):
            for s in order:
                if pools[s] and len(picked) < cap:
                    picked.append(pools[s].pop())
        chosen += picked
    return chosen


def counts(rows: list[dict]) -> dict:
    """Counts per class, fold and node plus the number of sessions, for logging."""
    return {"n": len(rows), "classes": dict(Counter(r["label"] for r in rows)),
            "folds": dict(Counter(str(r["fold"]) for r in rows)),
            "nodes": dict(Counter(r["node"] for r in rows)),
            "sessions": len({r["session"] for r in rows})}


# ---------------------------------------------------------------- HTTP range reads

_LOCK, _LAST = threading.Lock(), [0.0]


def _throttle() -> None:
    """Space request starts at least MIN_GAP_S apart across all threads."""
    with _LOCK:
        wait = _LAST[0] + MIN_GAP_S - time.time()
        if wait > 0:
            time.sleep(wait)
        _LAST[0] = time.time()


def get_range(session, url: str, a: int, b: int, tries: int = 5) -> bytes:
    """GET bytes a..b inclusive with a 120 s timeout; retry with back-off on errors or short bodies."""
    import requests
    for t in range(tries):
        _throttle()
        try:
            r = session.get(url, headers={"Range": f"bytes={a}-{b}"}, timeout=120)
            if r.status_code == 206 and len(r.content) == b - a + 1:
                return r.content
            if r.status_code == 206 and len(r.content) > 0 and "Content-Range" in r.headers:
                end = int(r.headers["Content-Range"].split("/")[0].split("-")[-1])
                if len(r.content) == end - a + 1:
                    return r.content
            wait = 30 if r.status_code == 429 else 2 * (t + 1)
        except requests.RequestException:
            wait = 2 * (t + 1)
        time.sleep(wait)
    raise IOError(f"range read failed after {tries} tries: {url} {a}-{b}")


def zip_index(split: str) -> dict:
    """name -> [zip_url, local_header_offset, compressed_size, method]; built once (~35 s), cached."""
    path = RAW / f"{split}_zip_index.json"
    if path.exists():
        return json.loads(path.read_text())
    import requests

    class HttpFile(io.RawIOBase):
        """Just enough of a seekable file over HTTP for zipfile to read the central directory."""
        def __init__(self, s, url):
            r = s.head(url, allow_redirects=True, timeout=30)
            self.s, self.url, self.size, self.pos = s, r.url, int(r.headers["Content-Length"]), 0
        def seekable(self): return True
        def readable(self): return True
        def tell(self): return self.pos
        def seek(self, off, whence=0):
            self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
            return self.pos
        def read(self, n=-1):
            end = self.size if n < 0 else min(self.size, self.pos + n)
            if end <= self.pos:
                return b""
            b = get_range(self.s, self.url, self.pos, end - 1)
            self.pos = end
            return b

    s, (rec, pat), idx = requests.Session(), RECORDS[split], {}
    for k in range(1, 24):
        hf = HttpFile(s, f"https://zenodo.org/api/records/{rec}/files/{pat.format(k)}/content")
        for zi in zipfile.ZipFile(hf).infolist():
            if zi.filename.endswith(".wav"):
                idx[Path(zi.filename).name] = [hf.url, zi.header_offset, zi.compress_size, zi.compress_type]
    RAW.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(idx))
    return idx


def fetch_one(session, entry: list) -> tuple[np.ndarray, int]:
    """One range GET (local header + data) -> float32 audio [samples, channels] and bytes on the wire."""
    url, off, csize, method = entry
    b = get_range(session, url, off, off + 30 + 512 + csize)
    n, m = struct.unpack("<HH", b[26:30])
    data = b[30 + n + m: 30 + n + m + csize]
    raw = zlib.decompress(data, -15) if method == 8 else data
    x, sr = sf.read(io.BytesIO(raw), dtype="int16", always_2d=True)
    if sr != 16000:
        raise IOError(f"unexpected sample rate {sr}")
    return x, len(b)


def fetch(rows: list[dict], split: str, out_dir: Path, log_name: str, mono: bool = False,
          threads: int = 8) -> dict:
    """Fetch every row's clip to out_dir/<file stem>.flac (skips clips already on disk); log progress."""
    import requests
    idx = zip_index(split)
    out_dir.mkdir(parents=True, exist_ok=True)
    JOBS.mkdir(parents=True, exist_ok=True)
    log = open(JOBS / log_name, "a")
    todo = [r for r in rows if not (out_dir / (Path(r["file"]).stem + ".flac")).exists()]
    print(f"{time.strftime('%H:%M:%S')} start {len(todo)} of {len(rows)} clips -> {out_dir}", file=log, flush=True)
    s, done, failed, t0 = requests.Session(), [0], [], time.time()

    def job(r):
        try:
            x, _ = fetch_one(s, idx[r["file"]])
            if mono:
                x = x[:, :1]
            tmp = out_dir / (Path(r["file"]).stem + ".part.flac")
            sf.write(tmp, x, 16000, format="FLAC", subtype="PCM_16")
            tmp.rename(out_dir / (Path(r["file"]).stem + ".flac"))
        except Exception as e:  # a failed clip is logged and skipped; rerun to retry it
            failed.append(r["file"])
            print(f"FAIL {r['file']}: {e}", file=log, flush=True)
        done[0] += 1
        if done[0] % 100 == 0:
            rate = done[0] / (time.time() - t0)
            print(f"{time.strftime('%H:%M:%S')} {done[0]}/{len(todo)} {rate:.2f} clips/s "
                  f"eta {(len(todo) - done[0]) / rate / 60:.1f} min, {len(failed)} failed", file=log, flush=True)

    with ThreadPoolExecutor(threads) as ex:
        list(ex.map(job, todo))
    rep = {"split": split, "requested": len(rows), "fetched": len(todo) - len(failed), "failed": failed,
           "minutes": round((time.time() - t0) / 60, 1)}
    print(f"{time.strftime('%H:%M:%S')} done {json.dumps(rep)}", file=log, flush=True)
    return rep


# ---------------------------------------------------------------- the plan, written to disk

def plan() -> dict:
    """Decide demo sessions and the training subset; write data/meta/plan.json (small, committed)."""
    meta = load_meta("dev")
    demo = demo_sessions(meta)
    train = training_subset(meta, set(demo.values()))
    demo_rows = demo_clips(meta, demo)
    out = {"seed": SEED, "cap_per_class": TRAIN_CAP_PER_CLASS, "demo_node": DEMO_NODE,
           "demo_sessions": demo, "train_counts": counts(train), "demo_counts": counts(demo_rows),
           "train_files": sorted(r["file"] for r in train), "demo_files": [r["file"] for r in demo_rows]}
    (META / "plan.json").write_text(json.dumps(out, indent=1))
    return out


def load_plan() -> dict:
    """The committed plan (demo sessions, training files)."""
    return json.loads((META / "plan.json").read_text())


def main(cmd: str) -> None:
    meta = {r["file"]: r for r in load_meta("dev")}
    if cmd == "plan":
        p = plan()
        print(json.dumps({k: v for k, v in p.items() if not k.endswith("_files")}, indent=1))
    elif cmd == "fetch-dev":
        p = load_plan()
        print(json.dumps(fetch([meta[f] for f in p["train_files"]], "dev", CLIPS / "dev", "fetch-dev.log")))
    elif cmd == "fetch-demo":
        p = load_plan()
        print(json.dumps(fetch([meta[f] for f in p["demo_files"]], "dev", CLIPS / "demo", "fetch-demo.log")))
    elif cmd == "fetch-eval":
        from eval.sample import load_sample
        rows = load_sample()
        print(json.dumps(fetch(rows, "eval", CLIPS / "eval", "fetch-eval.log")))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
