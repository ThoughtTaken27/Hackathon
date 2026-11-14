"""Encoders used only for baselines and ablations (never at runtime): AST, CED-small, CLAP, log-mel statistics.

Each make_*() returns f(waves float32 [B, 160000] at 16 kHz) -> (embedding [B, D], scores [B, S] or None).
AST / CED-small / CLAP load from the local Hugging Face cache (downloaded once in stage 2).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

MAPS = Path(__file__).resolve().parents[1] / "docs" / "research" / "kettle" / "probes" / "maps"


def make_ast(device: str = "cpu"):
    from transformers import ASTFeatureExtractor, ASTForAudioClassification
    mid = "MIT/ast-finetuned-audioset-10-10-0.4593"
    fe = ASTFeatureExtractor.from_pretrained(mid)
    m = ASTForAudioClassification.from_pretrained(mid).to(device).eval()

    @torch.no_grad()
    def f(x):
        inp = fe(list(x), sampling_rate=16000, return_tensors="pt").to(device)
        out = m.audio_spectrogram_transformer(**inp)
        return out.pooler_output.float().cpu().numpy(), torch.sigmoid(m.classifier(out.pooler_output)).float().cpu().numpy()
    return f


def make_ced_small(device: str = "cpu"):
    from transformers import AutoModelForAudioClassification
    import torchaudio.transforms as T
    m = AutoModelForAudioClassification.from_pretrained("mispeech/ced-small", trust_remote_code=True).to(device).eval()
    mel = T.MelSpectrogram(sample_rate=16000, n_fft=512, win_length=512, hop_length=160, f_min=0, f_max=None, n_mels=64, center=True).to(device)
    db = T.AmplitudeToDB(top_db=120).to(device)

    @torch.no_grad()
    def f(x):
        feats = db(mel(torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).to(device)))
        emb = m.encoder(feats).logits.mean(1)
        return emb.float().cpu().numpy(), m.outputlayer(emb).sigmoid().float().cpu().numpy()
    return f


def make_clap(device: str = "cpu"):
    from transformers import ClapModel, ClapProcessor
    import librosa
    mid = "laion/clap-htsat-unfused"
    p, m = ClapProcessor.from_pretrained(mid), ClapModel.from_pretrained(mid).to(device).eval()
    prompts = json.loads((MAPS / "clap_prompts.json").read_text())["prompts"]
    with torch.no_grad():
        t = p(text=list(prompts.values()), return_tensors="pt", padding=True).to(device)
        te = m.get_text_features(**t)
        te = torch.nn.functional.normalize(getattr(te, "pooler_output", te), dim=-1)

    @torch.no_grad()
    def f(x):
        x48 = np.stack([librosa.resample(w, orig_sr=16000, target_sr=48000) for w in x])
        inp = p(audio=list(x48), sampling_rate=48000, return_tensors="pt").to(device)
        ae = m.get_audio_features(**inp)
        ae = torch.nn.functional.normalize(getattr(ae, "pooler_output", ae), dim=-1)
        return ae.float().cpu().numpy(), (ae @ te.T).float().cpu().numpy()
    return f


def make_logmel(device: str = "cpu"):
    """The no-deep-learning trained baseline's features: mean and std of 64 log-mel bands, plus RMS (129 numbers)."""
    import torchaudio.transforms as T
    mel = T.MelSpectrogram(sample_rate=16000, n_fft=512, win_length=512, hop_length=160, n_mels=64)

    def f(x):
        t = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32))
        lm = torch.log(mel(t) + 1e-6)
        rms = torch.sqrt((t ** 2).mean(-1, keepdim=True) + 1e-12)
        return torch.cat([lm.mean(-1), lm.std(-1), torch.log(rms)], -1).numpy(), None
    return f
