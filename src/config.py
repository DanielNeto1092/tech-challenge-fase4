from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ModelPaths:
    audio_emotion: Path = PROJECT_ROOT / "models" / "audio_emotion_baseline" / "audio_emotion_baseline.joblib"
    visual_wellbeing: Path = PROJECT_ROOT / "models" / "daisee_visual_baseline" / "daisee_visual_baseline.joblib"
    sharp_objects: Path = PROJECT_ROOT / "runs" / "detect" / "sharp_object_detector" / "weights" / "best.pt"


@dataclass(frozen=True)
class FusionWeights:
    video: float = 0.25
    audio: float = 0.20
    text: float = 0.20
    objects: float = 0.15
    clinical: float = 0.20


@dataclass(frozen=True)
class Thresholds:
    alert: float = 0.65
    critical: float = 0.80
    human_review_confidence: float = 0.55
    modality_disagreement: float = 0.55


@dataclass(frozen=True)
class AzureConfig:
    region: str = "brazilsouth"
    cognitive_endpoint: str | None = None
    cognitive_key: str | None = None
    storage_account: str | None = None
    storage_container: str = "sentinela-reports"
    service_bus_namespace: str | None = None
    service_bus_queue: str = "clinical-alerts"
    service_bus_connection_string: str | None = None
    key_vault_name: str | None = None


@dataclass(frozen=True)
class PipelineConfig:
    models: ModelPaths = field(default_factory=ModelPaths)
    weights: FusionWeights = field(default_factory=FusionWeights)
    thresholds: Thresholds = field(default_factory=Thresholds)
    azure: AzureConfig = field(default_factory=AzureConfig)
    min_kpt_conf: float = 0.3
    video_confidence: float = 0.8
    sharp_objects_conf: float = 0.5
    risk_object_classes: tuple[str, ...] = ("Knife", "Cutter", "Scissors", "Ice Pick", "Screwdriver", "Peeler", "Fork")
