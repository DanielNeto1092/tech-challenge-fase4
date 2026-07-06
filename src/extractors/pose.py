from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from src.domain.types import ModalityScore


COCO17_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]


class PoseExtractor:
    def __init__(self, min_conf: float = 0.3, aggregate: str = "p95"):
        self._min_conf = min_conf
        self._aggregate = aggregate

    def score_from_payload(self, payload: dict | list, confidence: float = 0.8) -> ModalityScore:
        if isinstance(payload, dict) and all(isinstance(v, list) for v in payload.values()):
            s, ev = self._score_temporal(payload)
        else:
            s, ev = self._score_single(payload)
        return ModalityScore(modality="video", score_0_1=s, confidence_0_1=confidence, evidence=ev)

    def _score_temporal(self, frames: dict[str, list]) -> tuple[float, dict]:
        scores: list[float] = []
        for _, detections in sorted(frames.items(), key=lambda x: int(x[0])):
            kps = self._best_person(detections)
            if kps is None:
                continue
            s, _ = self._defensive_heuristic(kps)
            scores.append(s)
        if not scores:
            return 0.0, {"reason": "no_person", "mode": "temporal"}
        final = self._percentile(scores, 0.95) if self._aggregate == "p95" else max(scores) if self._aggregate == "max" else sum(scores) / len(scores)
        return float(max(0, min(1, final))), {"mode": "temporal", "frames_scored": len(scores), "p95": self._percentile(scores, 0.95), "mean": sum(scores) / len(scores)}

    def _score_single(self, payload: Any) -> tuple[float, dict]:
        kps = self._best_person(payload if isinstance(payload, list) else [payload])
        if kps is None:
            return 0.0, {"reason": "no_person"}
        return self._defensive_heuristic(kps)

    def _best_person(self, detections: list) -> dict[str, tuple[float, float, float]] | None:
        best = None
        best_conf = -1.0
        for det in detections:
            kpts_raw = det.get("keypoints") if isinstance(det, dict) else det
            if not isinstance(kpts_raw, list) or len(kpts_raw) < 10:
                continue
            kps = {COCO17_NAMES[i]: (float(kpts_raw[i][0]), float(kpts_raw[i][1]), float(kpts_raw[i][2]) if len(kpts_raw[i]) > 2 else 1.0) for i in range(min(17, len(kpts_raw)))}
            mean_c = sum(c for _, _, c in kps.values()) / len(kps)
            if mean_c > best_conf:
                best = kps
                best_conf = mean_c
        return best

    def _defensive_heuristic(self, kps: dict[str, tuple[float, float, float]]) -> tuple[float, dict]:
        required = ["nose", "left_wrist", "right_wrist", "left_elbow", "right_elbow", "left_shoulder", "right_shoulder", "left_hip", "right_hip"]
        if any(k not in kps for k in required) or any(kps[k][2] < self._min_conf for k in required):
            return 0.0, {"low_confidence": True}

        def dist(a: str, b: str) -> float:
            return math.hypot(kps[a][0] - kps[b][0], kps[a][1] - kps[b][1])

        mid_sh = ((kps["left_shoulder"][0] + kps["right_shoulder"][0]) / 2, (kps["left_shoulder"][1] + kps["right_shoulder"][1]) / 2)
        mid_hp = ((kps["left_hip"][0] + kps["right_hip"][0]) / 2, (kps["left_hip"][1] + kps["right_hip"][1]) / 2)
        torso = math.hypot(mid_sh[0] - mid_hp[0], mid_sh[1] - mid_hp[1])
        if torso <= 0:
            return 0.0, {"torso": 0}

        hands_face = max(max(0, 1 - dist("left_wrist", "nose") / torso), max(0, 1 - dist("right_wrist", "nose") / torso))

        def elbow_angle(side: str) -> float:
            s, e, w = kps[f"{side}_shoulder"], kps[f"{side}_elbow"], kps[f"{side}_wrist"]
            ab = (s[0] - e[0], s[1] - e[1])
            cb = (w[0] - e[0], w[1] - e[1])
            dot = ab[0] * cb[0] + ab[1] * cb[1]
            n1, n2 = math.hypot(*ab), math.hypot(*cb)
            if n1 == 0 or n2 == 0:
                return 0.0
            return math.degrees(math.acos(max(-1, min(1, dot / (n1 * n2)))))

        arms_bent = max(max(0, 1 - abs(elbow_angle("left") - 90) / 90), max(0, 1 - abs(elbow_angle("right") - 90) / 90))
        score = 0.65 * hands_face + 0.35 * arms_bent
        return float(max(0, min(1, score))), {"hands_face": hands_face, "arms_bent": arms_bent}

    @staticmethod
    def _percentile(vals: list[float], p: float) -> float:
        if not vals:
            return 0.0
        xs = sorted(vals)
        idx = p * (len(xs) - 1)
        lo, hi = int(math.floor(idx)), int(math.ceil(idx))
        return xs[lo] if lo == hi else xs[lo] * (1 - (idx - lo)) + xs[hi] * (idx - lo)
