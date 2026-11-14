"""python -m eval.privacy_check : prove that Kettle's own code never writes audio to disk.

Runs the real app (python app.py) under a Python audit hook, opens the kitchen page in headless Chromium with a
recorded sample day as the fake microphone, says "Yes" on the consent screen and lets it listen for --seconds.
Four independent checks while it runs:
 1. audit hook: every file the server opens for writing, plus renames, copies and temp files;
 2. lsof every 3 s: regular files the server process holds open for writing (catches C-level writes);
 3. before/after snapshot of the repo, $TMPDIR, /tmp and ~/Library/Caches: new or changed files with audio extensions;
 4. magic bytes (RIFF / fLaC / OggS / ID3) of every new or changed file, whatever its name.
Then a 5 MB upload to "Try your own sound" must leave nothing new in $TMPDIR.
Allowed writes: the labels file (data/timeline_privacy_check/<date>.jsonl, a separate folder for this check).
Threat model: proves Kettle's code doesn't save or send audio; not a defence against a compromised OS, browser
extensions, crash dumps or someone at the unlocked laptop. Not a kernel trace (see the optional sudo fs_usage step).
Outputs results/privacy_check.json, results/privacy_check.txt and results/runtime.json. Exit 1 on any audio write.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765
LABELS_DIR = ROOT / "data" / "timeline_privacy_check"
FAKE_MIC = ROOT / "data" / "raw" / "privacy_fake_mic.wav"
WATCH = [ROOT, Path(tempfile.gettempdir()), Path("/tmp"), Path.home() / "Library" / "Caches"]
SKIP = ("/.git", "/.venv", "ms-playwright", "/node_modules", "/__pycache__", "/data/raw", "/data/clips", "/data/emb")
AUDIO_EXT = {".wav", ".flac", ".mp3", ".ogg", ".webm", ".m4a", ".aiff", ".aif", ".pcm", ".raw", ".npy", ".npz", ".opus", ".caf"}
MAGIC = (b"RIFF", b"fLaC", b"OggS", b"ID3", b"FORM", b"caff")
SEGMENTS = [("DevNode1_ex30_1", "absence"), ("DevNode1_ex30_2", "absence"), ("DevNode1_ex224_1", "vacuum_cleaner"),
            ("DevNode1_ex224_2", "vacuum_cleaner"), ("DevNode1_ex56_1", "dishwashing"), ("DevNode1_ex56_2", "dishwashing"),
            ("DevNode1_ex206_1", "social_activity"), ("DevNode1_ex206_2", "social_activity")]


def fake_mic(seconds: int) -> list[tuple[float, str]]:
    """A WAV of held-out demo clips (quiet, vacuum, dishes, talk, repeated) for Chromium's fake microphone."""
    parts, onsets, t = [], [], 0.0
    while t < seconds:
        for name, lab in SEGMENTS:
            x, _ = sf.read(ROOT / "demo_cache" / "clips" / f"{name}.flac", dtype="float32")
            if not onsets or onsets[-1][1] != lab:
                onsets.append((t, lab))
            parts.append(x[:160000])
            t += 10
    x = np.concatenate(parts)
    FAKE_MIC.parent.mkdir(parents=True, exist_ok=True)
    sf.write(FAKE_MIC, x / max(1e-6, np.abs(x).max()) * 0.8, 16000, subtype="PCM_16")
    return onsets


def snapshot() -> dict:
    snap = {}
    for root in WATCH:
        for dp, _, fn in os.walk(root):
            if any(s in dp for s in SKIP):
                continue
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    st = os.stat(p)
                    snap[p] = (st.st_size, st.st_mtime)
                except OSError:
                    pass
    return snap


HOOK = r'''
import sys, json, runpy, os
LOG = open(sys.argv[1], "w")
def h(ev, args):
    if ev == "open":
        path, mode = args[0], args[1]
        if isinstance(mode, str) and any(c in mode for c in "wax+"):
            LOG.write(json.dumps({"ev": ev, "path": str(path), "mode": mode}) + "\n"); LOG.flush()
        elif isinstance(mode, int) and mode & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND):
            LOG.write(json.dumps({"ev": ev, "path": str(path), "flags": mode}) + "\n"); LOG.flush()
    elif ev in ("os.rename", "os.replace", "shutil.copyfile", "tempfile.mkstemp", "tempfile.mkdtemp", "os.link", "socket.connect"):
        LOG.write(json.dumps({"ev": ev, "args": [str(a) for a in args]}) + "\n"); LOG.flush()
sys.addaudithook(h)
sys.argv = ["app.py"]
runpy.run_path("app.py", run_name="__main__")
'''


def get(path: str):
    return json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=10).read())


def _listen(srv, seconds: int, lsof_writes: set, cpu: list, texts: list) -> None:
    """Open the kitchen page in Chromium with the fake mic, consent, and listen for `seconds`, sampling lsof and CPU."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                                    f"--use-file-for-fake-audio-capture={FAKE_MIC}", "--autoplay-policy=no-user-gesture-required"])
        pg = b.new_page()
        pg.goto(f"http://127.0.0.1:{PORT}/kitchen")
        pg.get_by_role("button", name="Next").click()
        pg.get_by_role("button", name="Yes, Meera can see this").click()
        t_end = time.time() + seconds
        while time.time() < t_end:
            time.sleep(3)
            out = subprocess.run(["lsof", "-p", str(srv.pid)], capture_output=True, text=True).stdout
            for line in out.splitlines()[1:]:
                f = line.split()
                if len(f) > 8 and f[4] == "REG" and any(m in f[3] for m in ("w", "u")):
                    lsof_writes.add(" ".join(f[8:]))
            ps = subprocess.run(["ps", "-o", "%cpu=,rss=", "-p", str(srv.pid)], capture_output=True, text=True).stdout.split()
            if len(ps) == 2:
                cpu.append((float(ps[0]), int(ps[1]) / 1024))
            texts.append(pg.locator("#head").inner_text())
        b.close()


def main(seconds: int) -> int:
    shutil.rmtree(LABELS_DIR, ignore_errors=True)   # a run cut short leaves today's consent behind; start clean
    onsets = fake_mic(seconds + 20)
    audit_log = Path(tempfile.gettempdir()) / f"kettle_audit_{os.getpid()}.jsonl"
    env = {**os.environ, "KETTLE_PORT": str(PORT), "KETTLE_TIMELINE_DIR": str(LABELS_DIR), "HF_HUB_OFFLINE": "1",
           "TRANSFORMERS_OFFLINE": "1"}
    try:                                             # another server on this port would be measured instead of ours
        get("/api/today")
        raise SystemExit(f"Port {PORT} is already in use; stop that server first.")
    except OSError:
        pass
    before = snapshot()
    srv = subprocess.Popen([sys.executable, "-c", HOOK, str(audit_log)], cwd=ROOT, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for _ in range(60):
        try:
            get("/api/today")
            break
        except OSError:
            time.sleep(0.5)
    lsof_writes, cpu = set(), []
    texts = []
    try:
        _listen(srv, seconds, lsof_writes, cpu, texts)
    except BaseException:
        srv.terminate()                              # never leave the audited server running on a failed run
        raise
    # 5 MB upload to "Try your own sound": must be read in memory, never spooled to a temp file
    tb = snapshot()
    rng = np.random.default_rng(0)
    import io
    buf = io.BytesIO()
    sf.write(buf, (rng.standard_normal(16000 * 160) * 0.05).astype(np.float32), 16000, format="WAV", subtype="PCM_16")
    data = buf.getvalue()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/try", data=data, method="POST",
                                 headers={"Content-Type": "application/octet-stream", "X-Filename": "five-mb.wav"})
    upload_status = json.loads(urllib.request.urlopen(req, timeout=60).read())["status"]
    ta = snapshot()
    upload_new = [q for q, v in ta.items() if q not in tb or tb[q] != v]
    runtime = get("/api/runtime")
    srv.terminate()
    srv.wait(10)
    after = snapshot()
    changed = [q for q, v in after.items() if q not in before or before[q] != v]
    audio_ext = [q for q in changed if Path(q).suffix.lower() in AUDIO_EXT]
    magic = []
    for q in changed:
        try:
            with open(q, "rb") as fh:
                if fh.read(4) in MAGIC:
                    magic.append(q)
        except OSError:
            pass
    audit = [json.loads(l) for l in open(audit_log)] if audit_log.exists() else []
    audit_log.unlink(missing_ok=True)
    allowed = lambda path: str(path).startswith(str(LABELS_DIR)) or "/huggingface/" in str(path) or str(path).startswith("/dev/")
    bad_audit = [a for a in audit if a["ev"] == "open" and not allowed(a.get("path", ""))]
    connects = [a for a in audit if a["ev"] == "socket.connect" and "127.0.0.1" not in json.dumps(a) and "::1" not in json.dumps(a)]
    bad_lsof = [f for f in lsof_writes if not allowed(f) and "kettle_audit_" not in f]
    labels_written = sorted(str(q) for q in LABELS_DIR.glob("*.jsonl"))
    label_kinds = set()
    for q in LABELS_DIR.glob("*.jsonl"):
        for line in open(q):
            label_kinds |= set(json.loads(line).keys())
    upload_audio = [q for q in upload_new if Path(q).suffix.lower() in AUDIO_EXT]
    ok = not (bad_audit or bad_lsof or audio_ext or magic or connects or upload_audio)
    windows = runtime["windows"]
    rep = {"pass": bool(ok and windows > 0), "seconds_listened": seconds, "windows_labelled": windows,
           "kitchen_headlines_seen": sorted(set(texts)),
           "checks": {"python_write_opens_outside_labels_file": bad_audit, "lsof_write_handles_outside_labels_file": bad_lsof,
                      "new_or_changed_audio_extension_files": audio_ext, "new_or_changed_files_with_audio_magic_bytes": magic,
                      "outbound_connections": connects, "upload_5mb_status": upload_status,
                      "files_new_after_5mb_upload": upload_new[:20]},
           "labels_file_fields": sorted(label_kinds), "labels_files": labels_written,
           "watched": [str(w) for w in WATCH], "skipped_dataset_caches": list(SKIP),
           "n_files_new_or_changed_any_process": len(changed),
           "threat_model": "Proves Kettle's own code doesn't write audio to disk or send it off the machine. Not a defence "
                           "against a compromised OS, browser extensions, crash dumps or someone at the unlocked laptop. "
                           "Not a kernel trace; OS swap is encrypted and outside our control.",
           "ran_at": time.strftime("%Y-%m-%d %H:%M %Z")}
    # latency: first 10-s window label of each new activity after its onset in the fake-mic file
    lat = []
    if runtime["first_audio_t"]:
        evs = [json.loads(l) for q in LABELS_DIR.glob("*.jsonl") for l in open(q)]
        evs = [e for e in evs if e.get("kind") == "window"]
        for t_on, lab in onsets[1:]:
            t_abs = runtime["first_audio_t"] + t_on
            if t_abs > runtime["first_audio_t"] + seconds - 12:
                break
            hit = [e["t"] for e in evs if e["label"] == lab and t_abs <= e["t"] < t_abs + 25]
            lat.append({"onset_s": t_on, "activity": lab, "label_after_s": round(hit[0] - t_abs, 2) if hit else None})
    got = [x["label_after_s"] for x in lat if x["label_after_s"] is not None]
    rt = {"split": "privacy-check live run, Chromium fake mic, held-out SINS clips", "seconds": seconds,
          "per_hop_s_median": runtime["median_s"], "per_hop_s_p90": runtime["p90_s"], "n_hops": runtime["n_hops"],
          "server_cpu_percent_mean": round(float(np.mean([c for c, _ in cpu])), 1) if cpu else None,
          "server_rss_mb_max": round(max(r for _, r in cpu), 0) if cpu else None,
          "activity_change_to_window_label_s": lat,
          "median_change_to_label_s": float(np.median(got)) if got else None, "n_changes": len(got),
          "note": "per hop = one 5-s chip + one 10-s window through CED-tiny + head on CPU; latency counts only the 10-s timeline label"}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "privacy_check.json").write_text(json.dumps(rep, indent=1))
    (ROOT / "results" / "runtime.json").write_text(json.dumps(rt, indent=1))
    lines = [f"Kettle privacy check ({rep['ran_at']}): {'PASS' if rep['pass'] else 'FAIL'}",
             f"Listened {seconds} s through Chromium's fake mic; {windows} windows labelled.",
             f"Python write-opens outside the labels file: {len(bad_audit)}", f"lsof write handles outside it: {len(bad_lsof)}",
             f"New/changed audio-extension files: {len(audio_ext)}", f"New/changed files with audio magic bytes: {len(magic)}",
             f"Outbound connections: {len(connects)}", f"5 MB upload: {upload_status}; files new afterwards: {len(upload_new)}",
             f"Fields in the labels file: {', '.join(sorted(label_kinds))}", "", rep["threat_model"]]
    (ROOT / "results" / "privacy_check.txt").write_text("\n".join(lines) + "\n")
    shutil.rmtree(LABELS_DIR, ignore_errors=True)
    print("\n".join(lines))
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=60)
    sys.exit(main(ap.parse_args().seconds))
