from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


def clamp01(x: float) -> float:
    """Clamp a value to [0.0, 1.0]."""
    return max(0.0, min(1.0, float(x)))


@dataclass(frozen=True)
class ModalityScore:
    modality: Literal["video", "audio", "text", "objects", "clinical"]
    score_0_1: float
    confidence_0_1: float = 1.0
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ObjectDetection:
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    is_risk_object: bool = False


@dataclass(frozen=True)
class RiskReport:
    multimodal_score_0_1: float
    level: Literal["low", "medium", "high", "critical"]
    weights: dict[str, float]
    modality_scores: dict[str, ModalityScore]
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
