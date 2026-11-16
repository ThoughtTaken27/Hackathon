"""Write the WAV the urgent-alert browser test plays into Chromium's fake microphone: three synthetic NFPA 72 T3 smoke-alarm
clips (eval/synth_alarms.py, held-out seed 31, 20 dB over ESC-50 household sound), 30 s at 16 kHz.

    python tools/make_alarm_wav.py out.wav
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval.synth_alarms import synth  # noqa: E402

x = np.concatenate([synth("t3", 31, 20) for _ in range(3)])
sf.write(sys.argv[1], (x * 0.9 / np.abs(x).max()).astype(np.float32), 16000, subtype="PCM_16")
print(sys.argv[1], len(x) / 16000, "s")
