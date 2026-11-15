"""Export the frozen CED-tiny encoder (with its log-mel front end) to ONNX for the browser, and prove it matches.

The browser version of Kettle runs the same frozen model on the parent's own device, so audio never leaves it.
torchaudio's STFT returns complex numbers, which ONNX can't export, so the front end is rebuilt here from plain
ops (reflect pad, a windowed DFT as a 1-D convolution, the same mel filter bank, 10*log10, top_db=120). This script
checks that rebuild against torchaudio, then checks the exported graph against the Python pipeline on the 90 sample-day
clips: embeddings, AudioSet scores, and the final label after the frozen head.

    python tools/export_onnx.py            # writes web/public/model/ced-tiny.onnx + web/public/model/parity.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio.functional as AF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kettle import encoders, model  # noqa: E402

OUT = ROOT / "web" / "public" / "model"
SR, N_FFT, HOP, N_MELS, WIN_S = 16000, 512, 160, 64, 10


class LogMel(torch.nn.Module):
    """torchaudio MelSpectrogram(center=True, hann, power 2) + AmplitudeToDB(top_db=120), from exportable ops."""

    def __init__(self):
        super().__init__()
        n = torch.arange(N_FFT, dtype=torch.float64)
        f = torch.arange(N_FFT // 2 + 1, dtype=torch.float64)[:, None]
        w = torch.hann_window(N_FFT, periodic=True, dtype=torch.float64)
        ang = 2 * math.pi * f * n / N_FFT
        self.register_buffer("k_re", (w * torch.cos(ang)).float()[:, None, :])
        self.register_buffer("k_im", (-w * torch.sin(ang)).float()[:, None, :])
        fb = AF.melscale_fbanks(N_FFT // 2 + 1, f_min=0.0, f_max=SR / 2, n_mels=N_MELS, sample_rate=SR, norm=None, mel_scale="htk")
        self.register_buffer("fb", fb.float())

    def forward(self, wave):                                     # [1, samples]
        x = torch.nn.functional.pad(wave[:, None, :], (N_FFT // 2, N_FFT // 2), mode="reflect")
        re = torch.nn.functional.conv1d(x, self.k_re, stride=HOP)
        im = torch.nn.functional.conv1d(x, self.k_im, stride=HOP)
        power = re * re + im * im                                # [1, 257, frames]
        mel = torch.matmul(power.transpose(1, 2), self.fb).transpose(1, 2)   # [1, 64, frames]
        db = 10.0 * torch.log10(torch.clamp(mel, min=1e-10))
        return torch.maximum(db, db.amax() - 120.0)


class EncHead(torch.nn.Module):
    """log-mel features [1, 64, 1001] -> (embedding [1, 192], AudioSet probabilities [1, 527]).

    Exported apart from the front end: as one graph, onnxruntime-web 1.22 fails to create the session (a raw wasm
    exception), while each half runs fine; two sessions back to back give the same numbers (checked below)."""

    def __init__(self, enc):
        super().__init__()
        self.model = enc["model"]

    def forward(self, feats):
        tokens = self.model.encoder(feats).logits
        emb = tokens.mean(1)
        return emb, self.model.outputlayer(emb).sigmoid()


def clip(path: Path) -> np.ndarray:
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    a = a[:, 0]
    assert sr == SR, (path, sr)
    out = np.zeros(SR * WIN_S, dtype=np.float32)
    out[: min(len(a), len(out))] = a[: len(out)]
    return out


def main() -> int:
    import onnxruntime as ort
    torch.manual_seed(0)
    enc = encoders.load()
    head = model.load(ROOT / "models" / "head.json")
    front, net = LogMel().eval(), EncHead(enc).eval()
    OUT.mkdir(parents=True, exist_ok=True)

    clips = sorted((ROOT / "demo_cache" / "clips").glob("*.flac"))
    waves = np.stack([clip(p) for p in clips])

    # 1. the rebuilt front end vs torchaudio
    with torch.no_grad():
        x = torch.from_numpy(waves[:4])
        ref = enc["db"](enc["mel"](x[:1]))
        mine = front(x[:1])
    fe_err = float((ref - mine).abs().max())
    print(f"front end max |dB diff| vs torchaudio: {fe_err:.5f}")

    # 2. export: the front end, then the encoder + AudioSet head
    dummy = torch.from_numpy(waves[:1])
    fpath, path = OUT / "logmel.onnx", OUT / "ced-tiny.onnx"
    torch.onnx.export(front, (dummy,), str(fpath), input_names=["wave"], output_names=["feats"], opset_version=17, dynamo=False)
    with torch.no_grad():
        feats0 = front(dummy)
    torch.onnx.export(net, (feats0,), str(path), input_names=["feats"], output_names=["emb", "audioset"], opset_version=17, dynamo=False)
    print(f"wrote {fpath} and {path} ({path.stat().st_size / 1e6:.1f} MB)")

    # 3. ONNX vs the Python pipeline, clip by clip (batch 1, as the live app runs)
    fsess = ort.InferenceSession(str(fpath), providers=["CPUExecutionProvider"])
    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    emb_err, as_err, same = 0.0, 0.0, 0
    for w in waves:
        e_py, a_py = encoders.embed(enc, w[None])
        f_ox = fsess.run(None, {"wave": w[None]})[0]
        e_ox, a_ox = sess.run(None, {"feats": f_ox})
        emb_err = max(emb_err, float(np.abs(e_py - e_ox).max()))
        as_err = max(as_err, float(np.abs(a_py - a_ox).max()))
        same += int(model.predict_proba(head, e_py).argmax() == model.predict_proba(head, e_ox).argmax())
    report = {"clips": len(waves), "front_end_max_db_diff": fe_err, "embedding_max_abs_diff": emb_err,
              "audioset_max_abs_diff": as_err, "same_label": same, "onnx_mb": round(path.stat().st_size / 1e6, 2),
              "head_sha256": head["sha256"]}
    (OUT / "parity.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    ok = same == len(waves) and emb_err < 1e-2
    print("PARITY", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
