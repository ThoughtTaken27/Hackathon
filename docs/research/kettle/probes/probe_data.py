"""Probe 1: range-read SINS clips out of the remote Zenodo zips without downloading 46 GB.

Builds a central-directory index of every zip (name -> zip, offset, size), then fetches a
balanced sample of clips with one HTTP range request each, keeps channel 0 at 16 kHz and
times everything. Usage: python probe_data.py dev 306   |   python probe_data.py eval 108
"""
import io, json, random, sys, time, zipfile, zlib, struct
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, requests, soundfile as sf

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/raw/sins"
DEV_META = ROOT / "docs/research/samples/wow/sins/DCASE2018-task5-dev"
EVAL_META = RAW / "eval2-meta/DCASE2018-task5-eval"
RECORDS = {"dev": ("1247102", "DCASE2018-task5-dev.audio.{}.zip"),
           "eval": ("1291760", "DCASE2018-task5-eval.audio.{}.zip")}
S = requests.Session()


class HttpFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests (enough for zipfile's index read)."""
    def __init__(self, url):
        self.url, self.pos = url, 0
        r = S.head(url, allow_redirects=True, timeout=30)
        self.url, self.size = r.url, int(r.headers["Content-Length"])
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]; return self.pos
    def read(self, n=-1):
        end = self.size if n < 0 else min(self.size, self.pos + n)
        if end <= self.pos: return b""
        b = get_range(self.url, self.pos, end - 1)
        self.pos = end; return b


RETRIES = Counter()
import threading
_LOCK, _LAST = threading.Lock(), [0.0]
MIN_GAP_S = 0.5  # Zenodo allows 133 requests/minute for guests (x-ratelimit-limit); stay under 120


def throttle():
    """Space request starts at least MIN_GAP_S apart across all threads."""
    with _LOCK:
        wait = _LAST[0] + MIN_GAP_S - time.time()
        if wait > 0: time.sleep(wait)
        _LAST[0] = time.time()


def get_range(url, a, b, tries=5):
    """GET bytes a..b inclusive; retry (with backoff) on non-206 or short bodies, which Zenodo
    sometimes returns under parallel load."""
    for t in range(tries):
        throttle()
        try:
            r = S.get(url, headers={"Range": f"bytes={a}-{b}"}, timeout=120)
            want = int(r.headers.get("Content-Range", "/").split("/")[0].split("-")[-1] or -1) - a + 1 if r.status_code == 206 else -1
            if r.status_code == 206 and len(r.content) == want: return r.content
            RETRIES[r.status_code] += 1
        except requests.RequestException:
            RETRIES["exc"] += 1
        time.sleep(20 if RETRIES.get(429) else 1.5 * (t + 1))
    raise IOError(f"range read failed after {tries} tries: {url} {a}-{b}")


def build_index(split):
    """Read every zip's central directory once; cache name -> [zip_url, offset, csize, method]."""
    out = RAW / f"{split}_zip_index.json"
    if out.exists(): return json.loads(out.read_text()), 0.0
    rec, pat = RECORDS[split]; idx, t0 = {}, time.time()
    for k in range(1, 24):
        url = f"https://zenodo.org/api/records/{rec}/files/{pat.format(k)}/content"
        hf = HttpFile(url); zf = zipfile.ZipFile(hf)
        for zi in zf.infolist():
            if zi.filename.endswith(".wav"):
                idx[Path(zi.filename).name] = [hf.url, zi.header_offset, zi.compress_size, zi.compress_type]
        print(f"  zip {k}: {len(idx)} entries so far, {time.time()-t0:.1f}s", flush=True)
    out.write_text(json.dumps(idx)); return idx, time.time() - t0


def fetch(entry):
    """One range GET for local header + data; returns (channel-0 float32 16 kHz, bytes, seconds)."""
    url, off, csize, method = entry; t0 = time.time()
    b = get_range(url, off, off + 30 + 512 + csize); n, m = struct.unpack("<HH", b[26:30]); data = b[30+n+m:30+n+m+csize]
    raw = zlib.decompress(data, -15) if method == 8 else data
    x, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
    assert sr == 16000, sr
    return x[:, 0], len(b), time.time() - t0, x.shape[1]


def folds_of_dev():
    """Session -> official fold (the fold whose test list contains it)."""
    f = {}
    for k in range(1, 5):
        for l in open(DEV_META / f"evaluation_setup/fold{k}_evaluate.txt"):
            f[Path(l.split("\t")[0]).name] = k
    return f


def pick(split, n, seed=0):
    """Balanced over classes; round-robin over sessions so many sessions/nodes/folds appear."""
    meta = DEV_META / "meta.txt" if split == "dev" else EVAL_META / "meta.txt"
    rows = [l.rstrip("\n").split("\t") for l in open(meta)]
    if split == "eval":
        names = dict(l.rstrip("\n").split("\t")[::-1] for l in open(EVAL_META / "evaluation_setup/map.txt"))
        rows = [[f, c, s, Path(names[f]).name] for f, c, s in rows]
    by = defaultdict(lambda: defaultdict(list))
    for r in rows: by[r[1]][r[2]].append(r)
    rng, chosen = random.Random(seed), []
    per = n // len(by)
    for c, sess in sorted(by.items()):
        keys = sorted(sess); rng.shuffle(keys); i = 0
        while sum(1 for x in chosen if x[1] == c) < per:
            chosen.append(rng.choice(sess[keys[i % len(keys)]])); i += 1
    return chosen


def main(split, n):
    idx, t_index = build_index(split)
    rows = pick(split, n); fold = folds_of_dev() if split == "dev" else {}
    outdir = RAW / f"probe_{split}"; outdir.mkdir(parents=True, exist_ok=True)
    def job(r):
        name = Path(r[0]).name
        x, nb, dt, ch = fetch(idx[name])
        sf.write(outdir / name, x, 16000, subtype="PCM_16")
        return r, nb, dt, ch
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(job, rows))
    wall = time.time() - t0
    lab = [{"file": Path(r[0]).name, "label": r[1], "session": r[2],
            "node": (r[3] if split == "eval" else Path(r[0]).name).split("_")[0],
            "fold": fold.get(Path(r[0]).name), "orig": r[3] if split == "eval" else None} for r, *_ in res]
    (outdir / "labels.json").write_text(json.dumps(lab, indent=1))
    per = [dt for _, _, dt, _ in res]; nbytes = sum(nb for _, nb, _, _ in res)
    rep = {"split": split, "n": len(res), "index_build_s": round(t_index, 1), "wall_s": round(wall, 1),
           "per_clip_latency_s_median": round(float(np.median(per)), 2),
           "throughput_clips_per_s_8_threads": round(len(res) / wall, 2),
           "mean_bytes_per_clip": int(nbytes / len(res)), "channels_in_file": res[0][3],
           "est_minutes_6k": round(6000 / (len(res) / wall) / 60, 1),
           "est_minutes_12k": round(12000 / (len(res) / wall) / 60, 1),
           "classes": Counter(x["label"] for x in lab), "sessions": len({x["session"] for x in lab}),
           "nodes": Counter(x["node"] for x in lab), "folds": Counter(x["fold"] for x in lab),
           "retries_by_status": dict(RETRIES)}
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
