"""Audio in memory: decode bytes, convert to 16 kHz mono, cut into 10-second windows.

Nothing here writes to disk. Uploaded files are decoded straight from the bytes in RAM.
"""
from __future__ import annotations

import io

import numpy as np
import soundfile as sf

SR = 16000
WIN_S = 10
MAX_S = 60          # "Try your own sound" reads the first 60 seconds only
MIN_S = 10          # one full window


class AudioError(Exception):
    """Raised with a short reason the UI turns into a designed message: 'unreadable' or 'too_short'."""

    def __init__(self, reason: str, seconds: float | None = None):
        super().__init__(reason)
        self.reason = reason
        self.seconds = seconds


def _decode_av(data: bytes) -> tuple[np.ndarray, int]:
    """Decode formats libsndfile can't read (M4A/AAC) with PyAV, from memory. Returns [channels, n]."""
    import av
    with av.open(io.BytesIO(data), mode="r") as box:
        stream = next(s for s in box.streams if s.type == "audio")
        sr = stream.rate
        chunks = [f.to_ndarray().astype(np.float32) for f in box.decode(stream)]
    if not chunks:
        raise AudioError("unreadable")
    x = np.concatenate(chunks, axis=1)
    if stream.format.is_planar is False and x.shape[0] == 1 and stream.channels > 1:
        x = x.reshape(-1, stream.channels).T
    if np.issubdtype(chunks[0].dtype, np.integer) or np.abs(x).max() > 1.5:
        x = x / 32768.0
    return x, sr


def decode(data: bytes) -> tuple[np.ndarray, int]:
    """Raw file bytes -> (float32 [channels, samples], sample rate). Raises AudioError('unreadable')."""
    try:
        x, sr = sf.read(io.BytesIO(data), dtype="float32", always_2d=True)
        x = x.T
    except Exception:
        try:
            x, sr = _decode_av(data)
        except AudioError:
            raise
        except Exception:
            raise AudioError("unreadable")
    if x.size == 0 or not np.isfinite(x).all():
        raise AudioError("unreadable")
    return x, int(sr)


def to_16k_mono(x: np.ndarray, sr: int, channel: int | None = None) -> np.ndarray:
    """[channels, n] at any rate -> float32 [n] at 16 kHz. channel=None averages all channels."""
    mono = x.mean(0) if channel is None else x[channel]
    if sr != SR:
        from scipy.signal import resample_poly
        g = np.gcd(sr, SR)
        mono = resample_poly(mono, SR // g, sr // g)
    return mono.astype(np.float32)


def windows(x: np.ndarray, win_s: float = WIN_S, hop_s: float = WIN_S) -> list[tuple[float, np.ndarray]]:
    """Cut a 16 kHz signal into (start_seconds, window) pairs. A trailing part shorter than a window is dropped."""
    w, h = int(win_s * SR), int(hop_s * SR)
    return [(i / SR, x[i:i + w]) for i in range(0, len(x) - w + 1, h)]


def read_upload(data: bytes) -> tuple[np.ndarray, float, bool]:
    """Bytes of an uploaded file -> (16 kHz mono first 60 s, original duration in s, was_cut).

    Raises AudioError('unreadable') or AudioError('too_short', seconds).
    """
    x, sr = decode(data)
    mono = to_16k_mono(x, sr)
    seconds = len(mono) / SR
    if seconds < MIN_S:
        raise AudioError("too_short", round(seconds, 1))
    cut = seconds > MAX_S
    return mono[: MAX_S * SR], seconds, cut
