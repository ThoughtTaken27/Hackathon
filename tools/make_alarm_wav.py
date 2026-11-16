"""Write the WAVs the urgent-alert browser test (web/test/e2e_urgent.py) plays into Chromium's fake microphone.

    python tools/make_alarm_wav.py smoke out.wav   three synthetic NFPA 72 T3 smoke-alarm clips (eval/synth_alarms.py, held-out
                                                   seed 31, 20 dB over ESC-50 household sound), 30 s at 16 kHz
    python tools/make_alarm_wav.py crash out.wav   30 s of everyday sound (ESC-50 pouring water, a can, typing), a held-out ESC-50
                                                   glass-breaking clip, then 3.5 minutes of a quiet room (low pink noise, never
                                                   digital silence, which the app reads as a muted microphone)
Needs data/clips/esc50_all (python -m eval.esc50_all).
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.offlist import pink  # noqa: E402
from eval.synth_alarms import synth  # noqa: E402

CLIPS = ROOT / "data" / "clips" / "esc50_all"


def clip(cat: str, i: int = 0) -> np.ndarray:
    return sf.read(sorted(CLIPS.glob(f"esc50_{cat}_*.flac"))[i], dtype="float32")[0]


def crash() -> np.ndarray:
    act = np.concatenate([clip("pouring_water", 30), clip("can_opening", 30), clip("keyboard_typing", 30)])
    glass = [f for f in sorted(CLIPS.glob("esc50_glass_breaking_*.flac")) if f.stem.split("_")[-1][0] in "45"][0]
    g = sf.read(glass, dtype="float32")[0][:80000]
    quiet = pink(16000 * 210, np.random.default_rng(3)).astype(np.float32)
    quiet *= 0.002 / np.sqrt(np.mean(quiet ** 2))
    return np.concatenate([act / np.abs(act).max() * 0.5, g / np.abs(g).max() * 0.9, quiet])


kind, out = sys.argv[1], sys.argv[2]
x = crash() if kind == "crash" else np.concatenate([synth("t3", 31, 20) for _ in range(3)]) * 1.0
if kind != "crash":
    x = (x * 0.9 / np.abs(x).max()).astype(np.float32)
sf.write(out, x, 16000, subtype="PCM_16")
print(out, len(x) / 16000, "s")
