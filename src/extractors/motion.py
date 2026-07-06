from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.domain.types import ModalityScore

_FRAME_RX = re.compile(r"^(?P<prefix>.+?)_(?P<num>\d+)\.(?P<ext>png|jpg|jpeg)$", re.IGNORECASE)


class MotionExtractor:
    def __init__(self, aggregate: str = "p95", scale: float = 6.0, baseline_raw: float = 0.0, risk_direction: str = "high_motion_risk"):
        self._aggregate = aggregate
        self._scale = scale
        self._baseline = baseline_raw
        self._direction = risk_direction

    def score(self, frames_dir: Path, sequence: str, *, max_frames: int | None = None, confidence: float = 0.8) -> ModalityScore:
        import numpy as np
        frames = self._load_frames(frames_dir, sequence, max_frames)
        if len(frames) < 2:
            return ModalityScore(modality="video", score_0_1=0.0, confidence_0_1=0.0, evidence={"frames": len(frames)})

        diffs: list[float] = []
        prev = self._to_gray(frames[0][1])
        for _, path in frames[1:]:
            cur = self._to_gray(path)
            diffs.append(float(np.mean(np.abs(cur.astype(np.float32) - prev.astype(np.float32))) / 255.0))
            prev = cur

        agg_val = np.percentile(diffs, 95) if self._aggregate == "p95" else max(diffs) if self._aggregate == "max" else float(np.mean(diffs))
        delta = (self._baseline - agg_val) if self._direction == "low_motion_risk" else (agg_val - self._baseline)
        final = max(0.0, min(1.0, delta * self._scale))

        return ModalityScore(
            modality="video",
            score_0_1=round(final, 3),
            confidence_0_1=confidence,
            evidence={"mode": "motion", "sequence": sequence, "frames": len(frames), "raw_agg": float(agg_val), "direction": self._direction},
        )

    def _load_frames(self, root: Path, sequence: str, max_frames: int | None) -> list[tuple[int, Path]]:
        results: list[tuple[int, Path]] = []
        for p in root.iterdir():
            if not p.is_file():
                continue
            m = _FRAME_RX.match(p.name)
            if m and m.group("prefix") == sequence:
                results.append((int(m.group("num")), p))
        results.sort(key=lambda t: t[0])
        return results[:max_frames] if max_frames else results

    @staticmethod
    def _to_gray(path: Path):
        import numpy as np
        from PIL import Image
        with Image.open(path) as im:
            return np.array(im.convert("L"))
