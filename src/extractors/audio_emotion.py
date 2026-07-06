"""Audio emotion prediction from trained baseline model."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.extractors.audio import AudioExtractor

FEATURE_COLUMNS = [
    "duration_s", "rms_mean", "rms_std", "rms_p95", "rms_dynamic_range",
    "zcr_mean", "zcr_std", "silence_ratio", "clipping_ratio",
]


def predict_audio_emotion(
    wav_path: Path,
    model_path: Path,
) -> dict[str, Any]:
    if not model_path.exists():
        return {"available": False, "reason": f"model_not_found: {model_path}"}

    import joblib
    bundle = joblib.load(model_path)
    pipeline = bundle["pipeline"]
    labels: list[str] = list(bundle["labels"])

    feats = AudioExtractor().extract_features(wav_path)
    import pandas as pd
    X = pd.DataFrame([[float(feats.get(c, 0.0)) for c in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)

    predicted = str(pipeline.predict(X)[0])
    probabilities: dict[str, float] = {}
    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba(X)[0]
        probabilities = {str(c): round(float(p), 3) for c, p in zip(pipeline.classes_, probs)}
    else:
        probabilities = {label: (1.0 if label == predicted else 0.0) for label in labels}

    confidence = float(probabilities.get(predicted, 0.0))
    duration = float(feats.get("duration_s", 0.0))
    warnings: list[str] = []
    if duration > 30.0:
        confidence = min(confidence, 0.50)
        warnings.append("audio_longer_than_training_clips")

    return {
        "available": True,
        "predictedEmotion": predicted,
        "confidence": round(confidence, 3),
        "probabilities": probabilities,
        "domainWarnings": warnings,
    }
