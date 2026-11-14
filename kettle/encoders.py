"""CED-tiny: a small pretrained audio model that turns 10 s of sound into 192 numbers.

Kettle never trains this model. It is frozen; we only train the small head in kettle/model.py.
The same forward pass also gives CED's own AudioSet scores (527 everyday sound names), which we
show as evidence ("Sounds Kettle heard: dishes, pots and pans 0.36").

Weights: models/ced-tiny (Apache-2.0, Xiaomi). Code: kettle/vendor/ced (vendored, no remote code).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torchaudio.transforms as T

from kettle.vendor.ced.configuration_ced import CedConfig
from kettle.vendor.ced.modeling_ced import CedForAudioClassification

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "ced-tiny"
SR = 16000
EMB_DIM = 192


def load(device: str = "cpu") -> dict:
    """Load CED-tiny from the committed weights (no network). Returns a plain dict used by embed()."""
    torch.manual_seed(0)
    cfg = CedConfig.from_pretrained(MODEL_DIR)
    model = CedForAudioClassification.from_pretrained(MODEL_DIR, config=cfg).to(device).eval()
    pre = json.loads((MODEL_DIR / "preprocessor_config.json").read_text())
    mel = T.MelSpectrogram(sample_rate=SR, n_fft=pre["n_fft"], win_length=pre["win_size"],
                           hop_length=pre["hop_size"], f_min=pre["f_min"], f_max=pre["f_max"],
                           n_mels=pre["feature_size"], center=pre["center"]).to(device)
    to_db = T.AmplitudeToDB(top_db=120).to(device)
    labels = [cfg.id2label[i] for i in range(len(cfg.id2label))]
    return {"name": "ced-tiny", "model": model, "mel": mel, "db": to_db, "labels": labels, "device": device}


@torch.no_grad()
def embed(enc: dict, waves: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """float32 [B, samples] at 16 kHz -> (embeddings [B, 192], AudioSet probabilities [B, 527]).

    The embedding is the mean of CED's output tokens (the same pooling CED uses for its own head).
    """
    x = torch.from_numpy(np.ascontiguousarray(waves, dtype=np.float32)).to(enc["device"])
    feats = enc["db"](enc["mel"](x))
    tokens = enc["model"].encoder(feats).logits          # [B, tokens, 192]
    emb = tokens.mean(1)
    audioset = enc["model"].outputlayer(emb).sigmoid()
    return emb.float().cpu().numpy(), audioset.float().cpu().numpy()
