from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

from src.domain.types import ModalityScore


def _pcm_to_float(samples: bytes, sample_width: int):
    import numpy as np
    dtypes = {1: np.uint8, 2: "<i2", 4: "<i4"}
    maxvals = {1: 128.0, 2: 32768.0, 4: 2147483648.0}
    if sample_width == 1:
        arr = np.frombuffer(samples, dtype=np.uint8).astype(np.float32)
        return (arr - 128.0) / 128.0
    if sample_width in dtypes:
        arr = np.frombuffer(samples, dtype=dtypes[sample_width]).astype(np.float32)
        return arr / maxvals[sample_width]
    raise ValueError(f"Unsupported WAV sample width: {sample_width}")


def read_wav_mono(path: Path) -> tuple:
    import numpy as np
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    audio = _pcm_to_float(frames, sample_width)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)
    return audio.astype(np.float32), int(sample_rate)


def _is_riff_wav(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            header = f.read(12)
    except OSError:
        return False
    return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE"


def ensure_wav(path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if _is_riff_wav(path):
        return path, None

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError(
            f"Arquivo de áudio não está em WAV RIFF/PCM válido ({path.name}). "
            "Envie um WAV válido ou instale ffmpeg no PATH para converter MP3/M4A/OGG/FLAC."
        )

    tmp = tempfile.TemporaryDirectory(prefix="sentinela_audio_")
    out = Path(tmp.name) / "converted.wav"
    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-vn",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode != 0:
        tmp.cleanup()
        raise ValueError(f"Falha ao converter áudio para WAV: {result.stderr[-500:]}")
    return out, tmp


class AudioExtractor:
    def __init__(self, frame_ms: float = 40.0, hop_ms: float = 20.0):
        self._frame_ms = frame_ms
        self._hop_ms = hop_ms

    def extract_features(self, path: Path) -> dict[str, Any]:
        import numpy as np
        wav_path, tmp = ensure_wav(path)
        try:
            audio, sr = read_wav_mono(wav_path)
        finally:
            if tmp is not None:
                tmp.cleanup()
        if audio.size == 0:
            return {"sample_rate": sr, "duration_s": 0.0, "empty": True}

        frame_len = max(1, int(sr * self._frame_ms / 1000.0))
        hop_len = max(1, int(sr * self._hop_ms / 1000.0))

        rms_vals: list[float] = []
        zcr_vals: list[float] = []
        for start in range(0, max(1, audio.size - frame_len + 1), hop_len):
            frame = audio[start:start + frame_len]
            if frame.size < frame_len:
                break
            rms_vals.append(float(math.sqrt(float(np.mean(frame * frame)))))
            signs = np.signbit(frame)
            zcr_vals.append(float(np.mean(signs[1:] != signs[:-1])) if frame.size > 1 else 0.0)

        rms = np.asarray(rms_vals or [0.0], dtype=np.float32)
        zcr = np.asarray(zcr_vals or [0.0], dtype=np.float32)

        return {
            "sample_rate": sr,
            "duration_s": round(float(audio.size / sr), 3),
            "frame_count": int(rms.size),
            "rms_mean": float(np.mean(rms)),
            "rms_std": float(np.std(rms)),
            "rms_p95": float(np.percentile(rms, 95)),
            "rms_dynamic_range": float(np.percentile(rms, 95) - np.percentile(rms, 5)),
            "zcr_mean": float(np.mean(zcr)),
            "zcr_std": float(np.std(zcr)),
            "silence_ratio": float(1.0 - np.mean(rms >= max(0.01, float(np.percentile(rms, 20)) * 0.7))),
            "clipping_ratio": float(np.mean(np.abs(audio) > 0.98)),
        }

    def score(self, path: Path) -> ModalityScore:
        feats = self.extract_features(path)
        if feats.get("empty"):
            return ModalityScore(modality="audio", score_0_1=0.0, confidence_0_1=0.0, evidence=feats)

        rms_mean = float(feats["rms_mean"])
        variability = min(1.0, float(feats["rms_std"]) / max(rms_mean, 1e-4))
        burstiness = min(1.0, float(feats["rms_dynamic_range"]) / max(rms_mean, 1e-4))
        pause_signal = max(0.0, min(1.0, (float(feats["silence_ratio"]) - 0.15) / 0.55))
        roughness = min(1.0, float(feats["zcr_mean"]) / 0.18)

        raw = 0.35 * variability + 0.25 * burstiness + 0.25 * pause_signal + 0.15 * roughness
        confidence = min(1.0, float(feats["duration_s"]) / 20.0)

        return ModalityScore(
            modality="audio",
            score_0_1=round(max(0.0, min(1.0, raw)), 3),
            confidence_0_1=round(confidence, 3),
            evidence={**feats, "components": {"variability": variability, "burstiness": burstiness, "pause_signal": pause_signal, "roughness": roughness}},
        )
