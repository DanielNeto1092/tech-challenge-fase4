"""Feature extractors for each modality."""

from .audio import AudioExtractor
from .audio_emotion import predict_audio_emotion
from .clinical import ClinicalExtractor, ClinicalInput
from .text import TextExtractor
from .pose import PoseExtractor
from .motion import MotionExtractor
from .objects import SharpObjectDetector
from .visual_wellbeing import VisualWellbeingExtractor

__all__ = [
    "AudioExtractor",
    "predict_audio_emotion",
    "ClinicalExtractor",
    "ClinicalInput",
    "TextExtractor",
    "PoseExtractor",
    "MotionExtractor",
    "SharpObjectDetector",
    "VisualWellbeingExtractor",
]
