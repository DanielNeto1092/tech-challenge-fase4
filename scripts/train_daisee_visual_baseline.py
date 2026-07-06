from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score, mean_absolute_error
from sklearn.multioutput import MultiOutputClassifier


LABEL_COLUMNS = ["boredom", "engagement", "confusion", "frustration"]
FEATURE_COLUMNS = [
    "frame_count_read",
    "brightness_mean",
    "brightness_std",
    "brightness_p10",
    "brightness_p90",
    "contrast_mean",
    "contrast_std",
    "motion_mean",
    "motion_std",
    "motion_p90",
    "edge_density_mean",
    "edge_density_std",
]


def _stable_key(path: str) -> str:
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:20]


def extract_visual_features(video_path: str | Path, *, max_frames: int = 24) -> dict[str, float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total > 0 and max_frames > 0:
        frame_indices = np.linspace(0, max(0, total - 1), num=min(max_frames, total), dtype=int)
    else:
        frame_indices = np.arange(max_frames)

    brightness: list[float] = []
    contrast: list[float] = []
    edge_density: list[float] = []
    motion: list[float] = []
    prev_gray = None

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        frame = cv2.resize(frame, (96, 96), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_f = gray.astype(np.float32) / 255.0

        brightness.append(float(np.mean(gray_f)))
        contrast.append(float(np.std(gray_f)))
        edges = cv2.Canny(gray, 80, 160)
        edge_density.append(float(np.mean(edges > 0)))
        if prev_gray is not None:
            motion.append(float(np.mean(np.abs(gray_f - prev_gray))))
        prev_gray = gray_f

    cap.release()

    if not brightness:
        return {col: 0.0 for col in FEATURE_COLUMNS}

    motion_arr = np.asarray(motion or [0.0], dtype=np.float32)
    brightness_arr = np.asarray(brightness, dtype=np.float32)
    contrast_arr = np.asarray(contrast, dtype=np.float32)
    edge_arr = np.asarray(edge_density, dtype=np.float32)

    return {
        "frame_count_read": float(len(brightness)),
        "brightness_mean": float(np.mean(brightness_arr)),
        "brightness_std": float(np.std(brightness_arr)),
        "brightness_p10": float(np.percentile(brightness_arr, 10)),
        "brightness_p90": float(np.percentile(brightness_arr, 90)),
        "contrast_mean": float(np.mean(contrast_arr)),
        "contrast_std": float(np.std(contrast_arr)),
        "motion_mean": float(np.mean(motion_arr)),
        "motion_std": float(np.std(motion_arr)),
        "motion_p90": float(np.percentile(motion_arr, 90)),
        "edge_density_mean": float(np.mean(edge_arr)),
        "edge_density_std": float(np.std(edge_arr)),
    }


def _load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out[row["relative_path"]] = row
    return out


def _write_cache(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["relative_path", "split", *LABEL_COLUMNS, *FEATURE_COLUMNS]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _sample_manifest(df: pd.DataFrame, max_per_split: int) -> pd.DataFrame:
    parts = []
    for split in ["train", "validation", "test"]:
        subset = df[(df["split"] == split) & (df["available"].astype(str).str.lower() == "true")]
        subset = subset.sort_values(["subject_id", "clip_id"])
        if max_per_split > 0:
            subset = subset.head(max_per_split)
        parts.append(subset)
    return pd.concat(parts, ignore_index=True)


def build_feature_table(
    selected: pd.DataFrame,
    *,
    project_root: Path,
    cache_path: Path,
    max_frames: int,
) -> pd.DataFrame:
    cached = _load_cache(cache_path)
    rows: list[dict[str, Any]] = []

    for item in selected.to_dict(orient="records"):
        relative_path = str(item["relative_path"])
        cached_row = cached.get(relative_path)
        if cached_row is not None:
            rows.append(cached_row)
            continue

        video_path = project_root / str(item["path"])
        features = extract_visual_features(video_path, max_frames=max_frames)
        row = {
            "relative_path": relative_path,
            "split": item["split"],
            **{label: int(item[label]) for label in LABEL_COLUMNS},
            **features,
        }
        rows.append(row)

    _write_cache(cache_path, rows)
    return pd.DataFrame(rows)


def train_and_evaluate(features: pd.DataFrame, out_dir: Path) -> dict[str, Any]:
    train_df = features[features["split"] == "train"].copy()
    eval_df = features[features["split"].isin(["validation", "test"])].copy()

    X_train = train_df[FEATURE_COLUMNS].apply(pd.to_numeric)
    y_train = train_df[LABEL_COLUMNS].astype(int)
    X_eval = eval_df[FEATURE_COLUMNS].apply(pd.to_numeric)
    y_eval = eval_df[LABEL_COLUMNS].astype(int)

    clf = MultiOutputClassifier(
        RandomForestClassifier(
            n_estimators=160,
            max_depth=10,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
    )
    clf.fit(X_train, y_train)
    pred = pd.DataFrame(clf.predict(X_eval), columns=LABEL_COLUMNS)

    per_label: dict[str, Any] = {}
    for label in LABEL_COLUMNS:
        labels_sorted = sorted(set(y_eval[label].tolist()) | set(pred[label].tolist()))
        per_label[label] = {
            "accuracy": float(accuracy_score(y_eval[label], pred[label])),
            "balanced_accuracy": float(balanced_accuracy_score(y_eval[label], pred[label])),
            "macro_f1": float(f1_score(y_eval[label], pred[label], average="macro", zero_division=0)),
            "mae": float(mean_absolute_error(y_eval[label], pred[label])),
            "confusion_matrix": confusion_matrix(y_eval[label], pred[label], labels=labels_sorted).tolist(),
            "confusion_matrix_labels": labels_sorted,
            "classification_report": classification_report(
                y_eval[label],
                pred[label],
                output_dict=True,
                zero_division=0,
            ),
        }

    metrics = {
        "model": "RandomForest visual baseline over DAiSEE",
        "feature_columns": FEATURE_COLUMNS,
        "label_columns": LABEL_COLUMNS,
        "train_rows": int(len(train_df)),
        "eval_rows": int(len(eval_df)),
        "per_label": per_label,
        "mean_macro_f1": float(np.mean([per_label[label]["macro_f1"] for label in LABEL_COLUMNS])),
        "mean_accuracy": float(np.mean([per_label[label]["accuracy"] for label in LABEL_COLUMNS])),
        "mean_balanced_accuracy": float(np.mean([per_label[label]["balanced_accuracy"] for label in LABEL_COLUMNS])),
        "disclaimer": (
            "Visual-affective DAiSEE baseline. Engagement/frustration/confusion are indirect wellbeing context, "
            "not clinical or trauma labels."
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": clf,
            "feature_columns": FEATURE_COLUMNS,
            "label_columns": LABEL_COLUMNS,
            "metrics": metrics,
        },
        out_dir / "daisee_visual_baseline.joblib",
    )
    (out_dir / "daisee_visual_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pred_out = eval_df[["relative_path", "split", *LABEL_COLUMNS]].reset_index(drop=True)
    for label in LABEL_COLUMNS:
        pred_out[f"pred_{label}"] = pred[label].to_numpy()
    pred_out.to_csv(out_dir / "daisee_visual_predictions.csv", index=False)
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a visual-affective DAiSEE baseline.")
    parser.add_argument("--manifest", default="data/manifests/daisee_manifest.csv")
    parser.add_argument("--out-dir", default="models/daisee_visual_baseline")
    parser.add_argument("--features-cache", default="data/cache/daisee_visual_features.csv")
    parser.add_argument("--max-per-split", type=int, default=650)
    parser.add_argument("--max-frames", type=int, default=24)
    args = parser.parse_args()

    manifest = pd.read_csv(args.manifest)
    selected = _sample_manifest(manifest, int(args.max_per_split))
    print(f"Selected {len(selected)} DAiSEE clips")

    features = build_feature_table(
        selected,
        project_root=Path.cwd(),
        cache_path=Path(args.features_cache),
        max_frames=int(args.max_frames),
    )
    metrics = train_and_evaluate(features, Path(args.out_dir))
    print(
        "mean_accuracy={mean_accuracy:.3f} mean_macro_f1={mean_macro_f1:.3f}".format(
            **metrics
        )
    )
    print(f"Wrote model/metrics -> {Path(args.out_dir).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
