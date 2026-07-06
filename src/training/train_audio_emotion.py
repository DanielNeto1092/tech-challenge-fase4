"""Train audio emotion baseline (Logistic Regression on RAVDESS/CREMA-D)."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.extractors.audio import AudioExtractor

EMOTIONS = ["angry", "disgust", "fearful", "happy", "neutral", "sad"]
FEATURE_COLUMNS = ["duration_s", "rms_mean", "rms_std", "rms_p95", "rms_dynamic_range", "zcr_mean", "zcr_std", "silence_ratio", "clipping_ratio"]


def _extract_wav(video_path: Path, wav_path: Path) -> None:
    if wav_path.exists() and wav_path.stat().st_size > 44:
        return
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video_path), "-ac", "1", "-ar", "16000", str(wav_path)], check=True)


def _load_cache(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out[row["relative_path"]] = row
    return out


def _write_cache(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dataset", "relative_path", "emotion", "split", "actor_folder", *FEATURE_COLUMNS]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def build_features(manifest: pd.DataFrame, *, max_per_emotion: int, wav_cache: Path, feat_cache: Path) -> pd.DataFrame:
    extractor = AudioExtractor()
    cached = _load_cache(feat_cache)
    rows: list[dict] = []

    selected = manifest[manifest["emotion"].isin(EMOTIONS) & manifest["modality"].isin(["audio_video", "audio_only"])]
    parts = []
    for emo in EMOTIONS:
        sub = selected[selected["emotion"] == emo].sort_values("relative_path")
        if max_per_emotion > 0:
            sub = sub.head(max_per_emotion)
        parts.append(sub)
    selected = pd.concat(parts, ignore_index=True)

    for item in selected.to_dict(orient="records"):
        rp = str(item["relative_path"])
        if rp in cached:
            rows.append(cached[rp])
            continue

        video = Path(item["path"])
        wav = wav_cache / f"{hashlib.sha1(rp.encode()).hexdigest()[:20]}.wav"
        _extract_wav(video, wav)
        feats = extractor.extract_features(wav)

        row = {"dataset": item["dataset"], "relative_path": rp, "emotion": item["emotion"], "split": item["split"], "actor_folder": item["actor_folder"]}
        for c in FEATURE_COLUMNS:
            row[c] = float(feats.get(c, 0.0))
        rows.append(row)

    _write_cache(feat_cache, rows)
    return pd.DataFrame(rows)


def train(features: pd.DataFrame, out_dir: Path) -> dict[str, Any]:
    train_df = features[features["split"] == "train"]
    eval_df = features[features["split"].isin(["validation", "test"])]

    X_train = train_df[FEATURE_COLUMNS].apply(pd.to_numeric)
    y_train = train_df["emotion"]
    X_eval = eval_df[FEATURE_COLUMNS].apply(pd.to_numeric)
    y_eval = eval_df["emotion"]

    pipe = Pipeline([
        ("pre", ColumnTransformer([("num", StandardScaler(), FEATURE_COLUMNS)])),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_eval)

    labels = sorted(y_train.unique())
    metrics = {
        "accuracy": float(accuracy_score(y_eval, y_pred)),
        "macro_f1": float(f1_score(y_eval, y_pred, average="macro", zero_division=0)),
        "labels": labels,
        "train_rows": len(train_df),
        "eval_rows": len(eval_df),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipe, "feature_columns": FEATURE_COLUMNS, "labels": labels, "metrics": metrics}, out_dir / "audio_emotion_baseline.joblib")
    (out_dir / "audio_emotion_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="data/manifests/emotion_video_manifest.csv")
    p.add_argument("--out-dir", default="models/audio_emotion_baseline")
    p.add_argument("--wav-cache", default="data/cache/audio_emotion_wav")
    p.add_argument("--feat-cache", default="data/cache/audio_emotion_features.csv")
    p.add_argument("--max-per-emotion", type=int, default=180)
    args = p.parse_args()

    manifest = pd.read_csv(args.manifest)
    features = build_features(manifest, max_per_emotion=args.max_per_emotion, wav_cache=Path(args.wav_cache), feat_cache=Path(args.feat_cache))
    metrics = train(features, Path(args.out_dir))
    print(f"accuracy={metrics['accuracy']:.3f} macro_f1={metrics['macro_f1']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
