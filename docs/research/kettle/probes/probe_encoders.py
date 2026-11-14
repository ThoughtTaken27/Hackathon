"""Probe 2: time three pretrained audio encoders on the probe clips and save their outputs.

For each encoder: seconds per 10-s clip on CPU and MPS (batch 8), peak RSS, a clip embedding,
and (where the model has them) AudioSet-527 scores; CLAP also gets text-prompt similarities.
Usage: python probe_encoders.py ast|ced-tiny|clap  [split=dev]
Outputs: data/raw/sins/probe_<split>/emb_<encoder>.npz
"""
import json, resource, sys, time
from pathlib import Path
import numpy as np, soundfile as sf, torch

ROOT = Path(__file__).resolve().parents[4]
MAPS = Path(__file__).resolve().parent / "maps"
torch.manual_seed(0)


def load_clips(split):
    d = ROOT / f"data/raw/sins/probe_{split}"
    lab = json.loads((d / "labels.json").read_text())
    wav = [sf.read(d / x["file"], dtype="float32")[0] for x in lab]
    return lab, np.stack([w[:160000] if len(w) >= 160000 else np.pad(w, (0, 160000 - len(w))) for w in wav])


def make(name, device):
    """Return f(batch of 16 kHz float32 waveforms) -> (embeddings [B,D], audioset scores [B,527] or None)."""
    if name == "ast":
        from transformers import ASTFeatureExtractor, ASTForAudioClassification
        mid = "MIT/ast-finetuned-audioset-10-10-0.4593"
        fe, m = ASTFeatureExtractor.from_pretrained(mid), ASTForAudioClassification.from_pretrained(mid).to(device).eval()
        def f(x):
            inp = fe(list(x), sampling_rate=16000, return_tensors="pt").to(device)
            out = m.audio_spectrogram_transformer(**inp)
            return out.pooler_output, torch.sigmoid(m.classifier(out.pooler_output))
        return f
    if name.startswith("ced"):
        from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
        mid = f"mispeech/{name}"
        fe = AutoFeatureExtractor.from_pretrained(mid, trust_remote_code=True)
        m = AutoModelForAudioClassification.from_pretrained(mid, trust_remote_code=True).to(device).eval()
        def f(x):
            inp = fe(list(x), sampling_rate=16000, return_tensors="pt")
            tok = m.encoder(inp["input_values"].to(device)).logits      # [B, tokens, D]
            emb = tok.mean(1)
            return emb, m.outputlayer(emb).sigmoid()
        return f
    if name == "clap":
        from transformers import ClapModel, ClapProcessor
        mid = "laion/clap-htsat-unfused"
        p, m = ClapProcessor.from_pretrained(mid), ClapModel.from_pretrained(mid).to(device).eval()
        prompts = json.loads((MAPS / "clap_prompts.json").read_text())["prompts"]
        t = p(text=list(prompts.values()), return_tensors="pt", padding=True).to(device)
        te = m.get_text_features(**t); te = getattr(te, "pooler_output", te)
        te = torch.nn.functional.normalize(te, dim=-1)
        def f(x):
            import librosa
            x48 = np.stack([librosa.resample(w, orig_sr=16000, target_sr=48000) for w in x])
            inp = p(audio=list(x48), sampling_rate=48000, return_tensors="pt").to(device)
            ae = m.get_audio_features(**inp); ae = getattr(ae, "pooler_output", ae)
            ae = torch.nn.functional.normalize(ae, dim=-1)
            return ae, ae @ te.T          # "scores" = cosine sim to the 9 frozen prompts
        return f
    raise ValueError(name)


def run(name, split="dev"):
    lab, X = load_clips(split)
    rep = {"encoder": name, "n_clips": len(X), "torch": torch.__version__}
    for device in (["mps", "cpu"] if torch.backends.mps.is_available() else ["cpu"]):
        t0 = time.time(); f = make(name, device); rep[f"load_s_{device}"] = round(time.time() - t0, 1)
        with torch.no_grad():
            f(X[:2])                                  # warm-up (not timed)
            n = len(X) if device == "mps" else min(48, len(X))   # CPU timed on a subset
            embs, scores, t0 = [], [], time.time()
            for i in range(0, n, 8):
                e, s = f(X[i:i + 8]); embs.append(e.float().cpu().numpy()); scores.append(s.float().cpu().numpy())
            if device == "mps": torch.mps.synchronize()
            dt = time.time() - t0
        rep[f"s_per_clip_{device}_batch8"] = round(dt / n, 3)
        if device == "mps" or "emb" not in rep:
            E, S = np.concatenate(embs), np.concatenate(scores)
            if len(E) == len(X):
                np.savez(ROOT / f"data/raw/sins/probe_{split}/emb_{name}.npz", emb=E, scores=S)
                rep["emb_dim"] = E.shape[1]; rep["emb"] = "saved"
        # single-clip latency (what live mode pays per window)
        with torch.no_grad():
            t0 = time.time()
            for i in range(5): f(X[i:i + 1])
            if device == "mps": torch.mps.synchronize()
        rep[f"s_single_clip_{device}"] = round((time.time() - t0) / 5, 3)
        del f
    rep["peak_rss_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 0)
    print(json.dumps(rep))


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "dev")
