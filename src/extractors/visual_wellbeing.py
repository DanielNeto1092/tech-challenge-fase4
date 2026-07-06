from __future__ import annotations

from pathlib import Path
from typing import Any


FEATURE_COLUMNS = [
    "frame_count_read", "brightness_mean", "brightness_std", "brightness_p10", "brightness_p90",
    "contrast_mean", "contrast_std", "motion_mean", "motion_std", "motion_p90",
    "edge_density_mean", "edge_density_std",
]


class VisualWellbeingExtractor:
    def __init__(self, model_path: Path, max_frames: int = 24):
        self._model_path = model_path
        self._max_frames = max_frames

    def predict(self, video_path: Path) -> dict[str, Any]:
        if not self._model_path.exists():
            return {"available": False, "reason": f"model_not_found: {self._model_path}"}

        import joblib
        bundle = joblib.load(self._model_path)
        model = bundle["model"]
        feature_cols = list(bundle.get("feature_columns", FEATURE_COLUMNS))
        label_cols = list(bundle["label_columns"])

        feats = self._extract(video_path)
        import pandas as pd
        X = pd.DataFrame([[float(feats.get(c, 0.0)) for c in feature_cols]], columns=feature_cols)
        pred = model.predict(X)[0]
        predictions = {label_cols[i]: int(pred[i]) for i in range(len(label_cols))}

        boredom = predictions.get("boredom", 0) / 3.0
        confusion = predictions.get("confusion", 0) / 3.0
        frustration = predictions.get("frustration", 0) / 3.0
        engagement = predictions.get("engagement", 0) / 3.0
        strain = max(0.0, min(1.0, 0.35 * boredom + 0.30 * confusion + 0.25 * frustration + 0.10 * (1.0 - engagement)))

        return {"available": True, "predictions": predictions, "visualStrain": round(strain, 3), "features": feats}

    def _extract(self, video_path: Path) -> dict[str, float]:
        import cv2
        import numpy as np
        cv2.setNumThreads(0)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {c: 0.0 for c in FEATURE_COLUMNS}

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        indices = np.linspace(0, max(0, total - 1), num=min(self._max_frames, max(1, total)), dtype=int) if total > 0 else np.arange(self._max_frames)

        brightness, contrast, edge_density, motion = [], [], [], []
        prev_gray = None

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            frame = cv2.resize(frame, (96, 96))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
            brightness.append(float(np.mean(gray)))
            contrast.append(float(np.std(gray)))
            edge_density.append(float(np.mean(cv2.Canny((gray * 255).astype(np.uint8), 80, 160) > 0)))
            if prev_gray is not None:
                motion.append(float(np.mean(np.abs(gray - prev_gray))))
            prev_gray = gray

        cap.release()
        if not brightness:
            return {c: 0.0 for c in FEATURE_COLUMNS}

        # When only 1 frame is decoded, motion list is empty; default to [0.0] (no motion)
        b, c, e, m = np.array(brightness), np.array(contrast), np.array(edge_density), np.array(motion or [0.0])
        return {
            "frame_count_read": float(len(brightness)), "brightness_mean": float(np.mean(b)),
            "brightness_std": float(np.std(b)), "brightness_p10": float(np.percentile(b, 10)),
            "brightness_p90": float(np.percentile(b, 90)), "contrast_mean": float(np.mean(c)),
            "contrast_std": float(np.std(c)), "motion_mean": float(np.mean(m)),
            "motion_std": float(np.std(m)), "motion_p90": float(np.percentile(m, 90)),
            "edge_density_mean": float(np.mean(e)), "edge_density_std": float(np.std(e)),
        }
