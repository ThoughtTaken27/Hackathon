"""Drive probe 4 (latency) and probe 5 (nothing saved) without a human or a real microphone.

1. Builds a 60-s fake-mic WAV from real SINS probe clips: 20 s absence, 20 s vacuum, 20 s dishes.
2. Starts the probe server under a Python audit hook that logs every file opened for writing.
3. Snapshots files under the repo, $TMPDIR, /tmp and ~/Library/Caches before and after.
4. Launches headless Chromium with the WAV as its microphone, presses start, records every
   label the page shows with its time, and samples `lsof` on the server for open files.
Usage: python probe_live_drive.py HOP_S WINDOW_S SECONDS
"""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np, soundfile as sf

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
HOP, WIN, DUR = sys.argv[1], sys.argv[2], int(sys.argv[3])
PY = sys.executable
WATCH = [ROOT, Path(tempfile.gettempdir()), Path("/tmp"), Path.home() / "Library/Caches"]
AUDIO_EXT = {".wav", ".flac", ".mp3", ".ogg", ".webm", ".m4a", ".aiff", ".pcm", ".raw", ".npy", ".npz"}


def fake_mic():
    lab = json.loads((ROOT / "data/raw/sins/probe_dev/labels.json").read_text())
    pick = lambda c: [x["file"] for x in lab if x["label"] == c][:2]
    parts = [sf.read(ROOT / "data/raw/sins/probe_dev" / f, dtype="float32")[0][:160000]
             for c in ("absence", "vacuum_cleaner", "dishwashing") for f in pick(c)]
    x = np.concatenate(parts); x = x / max(1e-6, np.abs(x).max()) * 0.8   # Chrome reads it as-is
    out = HERE.parent.parent.parent.parent / "data/raw/sins/fake_mic.wav"
    sf.write(out, x, 16000, subtype="PCM_16"); return out, [0, 20, 40], ["absence", "vacuum_cleaner", "dishwashing"]


def snapshot():
    snap = {}
    for root in WATCH:
        for dp, dn, fn in os.walk(root):
            if any(s in dp for s in ("/.git", "/.venv-probe", "ms-playwright", "/data/raw")): continue
            for f in fn:
                p = os.path.join(dp, f)
                try: st = os.stat(p); snap[p] = (st.st_size, st.st_mtime)
                except OSError: pass
    return snap


def main():
    wav, onsets, names = fake_mic()
    before = snapshot(); t_start = time.time()
    audit_log = Path(tempfile.gettempdir()) / f"kettle_audit_{os.getpid()}.jsonl"
    hook = (
        "import sys, json, runpy\n"
        f"LOG = open({str(audit_log)!r}, 'w')\n"
        "def h(ev, args):\n"
        "    if ev == 'open':\n"
        "        path, mode = args[0], args[1]\n"
        "        if isinstance(mode, str) and any(c in mode for c in 'wax+'):\n"
        "            LOG.write(json.dumps({'ev': ev, 'path': str(path), 'mode': mode}) + '\\n'); LOG.flush()\n"
        "    elif ev in ('os.rename', 'shutil.copyfile', 'tempfile.mkstemp', 'tempfile.mkdtemp'):\n"
        "        LOG.write(json.dumps({'ev': ev, 'args': [str(a) for a in args]}) + '\\n'); LOG.flush()\n"
        "sys.addaudithook(h)\n"
        f"sys.argv = ['srv', {HOP!r}, {WIN!r}]\n"
        f"runpy.run_path({str(HERE / 'probe_live_server.py')!r}, run_name='__main__')\n")
    srv = subprocess.Popen([PY, "-c", hook], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    time.sleep(14)  # model load
    from playwright.sync_api import sync_playwright
    lsof_writes = set()
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                                    f"--use-file-for-fake-audio-capture={wav}", "--autoplay-policy=no-user-gesture-required"])
        pg = b.new_page(); pg.goto("http://127.0.0.1:8765/"); pg.click("#go")
        secure = pg.evaluate("window.isSecureContext")
        for _ in range(DUR // 3):
            time.sleep(3)
            out = subprocess.run(["lsof", "-p", str(srv.pid)], capture_output=True, text=True).stdout
            for line in out.splitlines()[1:]:
                f = line.split()
                if len(f) > 8 and f[4] == "REG" and any(m in f[3] for m in ("w", "u")):
                    lsof_writes.add(" ".join(f[8:]))
        ev = pg.evaluate("window.__events"); sr = pg.evaluate("window.__sr"); b.close()
    srv.terminate(); srv.wait(5)
    after = snapshot()
    new_or_changed = [p for p, v in after.items() if p not in before or before[p] != v]
    audio_like = [p for p in new_or_changed if Path(p).suffix.lower() in AUDIO_EXT]
    riff = []
    for p in new_or_changed:
        try:
            with open(p, "rb") as fh: head = fh.read(12)
            if head[:4] == b"RIFF" or head[:4] == b"fLaC" or head[:4] == b"OggS": riff.append(p)
        except OSError: pass
    audit = [json.loads(l) for l in open(audit_log)] if audit_log.exists() else []
    audit_log.unlink(missing_ok=True)
    # latency: first time after each onset that the page shows the new activity
    delays = {}
    for t, n in zip(onsets[1:], names[1:]):
        hits = [e["t"] for e in ev if e["t"] >= t and e["label"] == n and e["t"] < t + 20]
        delays[n] = round(hits[0] - t, 2) if hits else None
    rep = {"hop_s": float(HOP), "window_s": float(WIN), "secure_context_localhost": secure, "audiocontext_sr": sr,
           "n_labels_shown": len(ev), "server_infer_s_median": float(np.median([e["infer_s"] for e in ev])) if ev else None,
           "sound_onset_to_label_s": delays, "timeline": [(round(e["t"], 1), e["label"], e["conf"]) for e in ev],
           "privacy": {"files_new_or_changed_in_watched_dirs": len(new_or_changed),
                       "audio_extension_files": audio_like, "audio_magic_bytes_files": riff,
                       "python_open_for_write_events": audit, "lsof_regular_files_open_for_write": sorted(lsof_writes),
                       "watched": [str(w) for w in WATCH], "changed_sample": new_or_changed[:15]}}
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
