"""Pipeline orchestrator: central entry point for multimodal analysis."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.cloud.azure_integration import AzureCognitiveAdapter, config_from_env
from src.config import PipelineConfig
from src.domain.types import ModalityScore
from src.engines import CareEngine, FusionEngine, RiskEngine
from src.extractors import AudioExtractor, MotionExtractor, PoseExtractor, SharpObjectDetector, VisualWellbeingExtractor
from src.extractors.audio_emotion import predict_audio_emotion
from src.extractors.clinical import ClinicalExtractor, ClinicalInput, ClinicalTimeSeriesAnomalyDetector
from src.extractors.text import TextExtractor
from src.logging_config import PipelineTracer

logger = logging.getLogger("sentinela.pipeline")


class SentinelaPipeline:
    def __init__(self, config: PipelineConfig | None = None):
        self._cfg = config or PipelineConfig()
        self._audio = AudioExtractor()
        self._text = TextExtractor()
        self._pose = PoseExtractor(min_conf=self._cfg.min_kpt_conf)
        self._objects = SharpObjectDetector(
            model_path=self._cfg.models.sharp_objects,
            conf_threshold=self._cfg.sharp_objects_conf,
            risk_classes=self._cfg.risk_object_classes,
        )
        self._visual = VisualWellbeingExtractor(model_path=self._cfg.models.visual_wellbeing)
        self._clinical = ClinicalExtractor()
        self._clinical_temporal = ClinicalTimeSeriesAnomalyDetector()
        self._fusion = FusionEngine(weights=self._cfg.weights, thresholds=self._cfg.thresholds)
        self._risk = RiskEngine()
        self._care = CareEngine()
        self._azure = AzureCognitiveAdapter(config_from_env(self._cfg.azure))

    def analyze(
        self,
        *,
        transcript: str | Path | None = None,
        audio_wav: str | Path | None = None,
        pose_json: str | Path | None = None,
        frames_dir: str | Path | None = None,
        sequence: str | None = None,
        video_file: str | Path | None = None,
        image_for_objects: str | Path | None = None,
        motion_calibration: str | Path | None = None,
        max_frames: int | None = None,
        clinical_data: ClinicalInput | None = None,
        clinical_series_data: list[dict[str, Any]] | None = None,
        prescriptions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not any([transcript, audio_wav, pose_json, frames_dir, video_file, image_for_objects, clinical_data, clinical_series_data, prescriptions]):
            raise ValueError("Provide at least one input source.")

        tracer = PipelineTracer()
        text_ms: ModalityScore | None = None
        audio_ms: ModalityScore | None = None
        video_ms: ModalityScore | None = None
        objects_ms: ModalityScore | None = None
        _warnings: list[str] = []
        transcript_text: str | None = None
        azure_speech: dict[str, Any] | None = None

        # --- TEXT ---
        if transcript:
            try:
                with tracer.stage("text_extraction"):
                    path = self._resolve(transcript, "transcript")
                    transcript_text = path.read_text(encoding="utf-8", errors="replace")
                    text_ms = self._text.score(transcript_text)
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Text extraction failed: %s", exc)
                _warnings.append(f"text: {exc}")

        # --- AUDIO ---
        if audio_wav:
            try:
                with tracer.stage("audio_extraction"):
                    path = self._resolve(audio_wav, "audio_wav")
                    audio_ms = self._audio.score(path)
                with tracer.stage("audio_emotion"):
                    emotion = predict_audio_emotion(path, self._cfg.models.audio_emotion)
                    if emotion.get("available"):
                        audio_ms = ModalityScore(
                            modality=audio_ms.modality,
                            score_0_1=audio_ms.score_0_1,
                            confidence_0_1=audio_ms.confidence_0_1,
                            evidence={**audio_ms.evidence, "emotion_baseline": emotion},
                        )
                if self._azure.enabled:
                    with tracer.stage("azure_speech_to_text"):
                        azure_speech = self._azure.speech_to_text(path)
                        if audio_ms is not None:
                            audio_ms = ModalityScore(
                                modality=audio_ms.modality,
                                score_0_1=audio_ms.score_0_1,
                                confidence_0_1=audio_ms.confidence_0_1,
                                evidence={**audio_ms.evidence, "azure_speech_to_text": azure_speech},
                            )
                        if azure_speech.get("available") and azure_speech.get("transcript"):
                            transcript_text = str(azure_speech["transcript"])
                            if text_ms is None:
                                text_ms = self._text.score(transcript_text)
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Audio extraction failed: %s", exc)
                _warnings.append(f"audio: {exc}")
                audio_ms = None

        # --- AZURE LANGUAGE (sentiment + key phrases) ---
        if transcript_text and text_ms is not None and self._azure.enabled:
            try:
                with tracer.stage("azure_language_analysis"):
                    language = self._azure.analyze_text(transcript_text)
                    if language.get("available"):
                        azure_risk = float(language.get("risk_score", 0.0))
                        text_ms = ModalityScore(
                            modality=text_ms.modality,
                            score_0_1=round(max(text_ms.score_0_1, azure_risk), 3),
                            confidence_0_1=round(max(text_ms.confidence_0_1, 0.80), 3),
                            evidence={**text_ms.evidence, "azure_language": language},
                        )
                    else:
                        text_ms = ModalityScore(
                            modality=text_ms.modality,
                            score_0_1=text_ms.score_0_1,
                            confidence_0_1=text_ms.confidence_0_1,
                            evidence={**text_ms.evidence, "azure_language": language},
                        )
            except Exception as exc:
                logger.warning("Azure Language analysis failed: %s", exc)
                _warnings.append(f"azure_language: {exc}")

        # --- VIDEO (pose) ---
        if pose_json:
            try:
                with tracer.stage("pose_extraction"):
                    path = self._resolve(pose_json, "pose_json")
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    video_ms = self._pose.score_from_payload(payload, confidence=self._cfg.video_confidence)
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Pose extraction failed: %s", exc)
                _warnings.append(f"pose: {exc}")

        # --- VIDEO (motion) ---
        if frames_dir and sequence:
            try:
                with tracer.stage("motion_extraction"):
                    fdir = Path(frames_dir)
                    if not fdir.is_dir():
                        raise ValueError(f"frames_dir not a directory: {fdir}")
                    motion = MotionExtractor()
                    if motion_calibration:
                        calib = json.loads(self._resolve(motion_calibration, "calibration").read_text(encoding="utf-8"))
                        motion = MotionExtractor(
                            baseline_raw=float(calib.get("motion_baseline_raw", 0)),
                            scale=float(calib.get("motion_scale", 6.0)),
                            risk_direction=str(calib.get("direction", "high_motion_risk")),
                        )
                    motion_ms = motion.score(fdir, sequence, max_frames=max_frames, confidence=self._cfg.video_confidence)
                    video_ms = self._merge_video_scores(video_ms, motion_ms, "motion")
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Motion extraction failed: %s", exc)
                _warnings.append(f"motion: {exc}")

        # --- VIDEO (visual wellbeing) ---
        if video_file:
            try:
                with tracer.stage("visual_wellbeing"):
                    path = self._resolve(video_file, "video_file")
                    wb = self._visual.predict(path)
                    strain = float(wb.get("visualStrain", 0.0))
                    wb_ms = ModalityScore(
                        modality="video",
                        score_0_1=strain,
                        confidence_0_1=0.55 if wb.get("available") else 0.0,
                        evidence={"mode": "visual_wellbeing", **wb},
                    )
                    if video_ms is None:
                        video_ms = wb_ms
                    else:
                        video_ms = self._merge_video_scores(video_ms, wb_ms, "visual_wellbeing")
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Visual wellbeing failed: %s", exc)
                _warnings.append(f"visual_wellbeing: {exc}")

        # --- OBJECTS (sharp objects) ---
        # Always attempt object detection when image or video is provided.
        # The detector handles fallback to COCO pretrained model internally.
        _object_source: str | Path | None = None
        if image_for_objects:
            _object_source = image_for_objects
        elif video_file:
            _object_source = video_file

        if _object_source:
            try:
                with tracer.stage("object_detection"):
                    resolved_src = self._resolve(_object_source, "image/video for objects")
                    objects_ms = self._objects.score(str(resolved_src))
                if (objects_ms.evidence or {}).get("available") is False:
                    _warnings.append(f"objects: {objects_ms.evidence.get('reason', 'unavailable')}")
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Object detection failed: %s", exc)
                _warnings.append(f"objects: {exc}")

        # --- CLINICAL (obstetric/maternal) ---
        clinical_ms: ModalityScore | None = None
        if clinical_data:
            try:
                with tracer.stage("clinical_extraction"):
                    clinical_ms = self._clinical.score(clinical_data)
            except Exception as exc:
                logger.warning("Clinical extraction failed: %s", exc)
                _warnings.append(f"clinical: {exc}")

        if clinical_series_data or prescriptions:
            try:
                with tracer.stage("clinical_time_series_anomaly"):
                    temporal_ms = self._clinical_temporal.score(clinical_series_data, prescriptions)
                    clinical_ms = self._merge_clinical_scores(clinical_ms, temporal_ms, "time_series")
            except Exception as exc:
                logger.warning("Clinical time-series anomaly detection failed: %s", exc)
                _warnings.append(f"clinical_time_series: {exc}")

        # Check at least one modality produced a result
        if not any([text_ms, audio_ms, video_ms, objects_ms, clinical_ms]):
            raise RuntimeError(
                "Nenhuma modalidade pôde ser processada. "
                + (" | ".join(_warnings) if _warnings else "Verifique as entradas.")
            )

        # --- FUSION ---
        with tracer.stage("fusion_engine"):
            report = self._fusion.fuse(video=video_ms, audio=audio_ms, text=text_ms, objects=objects_ms, clinical=clinical_ms)
            out = self._fusion.to_dict(report)

        with tracer.stage("risk_engine"):
            out["priority"] = self._risk.prioritize(report)

        with tracer.stage("care_engine"):
            out["care_assessment"] = self._care.assess(report)

        out["_trace"] = tracer.summary(
            modalities=list(report.modality_scores.keys()),
            score=report.multimodal_score_0_1,
            level=report.level,
        )
        if _warnings:
            out["_warnings"] = _warnings
        return out

    @staticmethod
    def _resolve(value: str | Path, label: str) -> Path:
        p = Path(value)
        if not p.exists():
            raise ValueError(f"{label} not found: {p}")
        return p

    @staticmethod
    def _merge_video_scores(current: ModalityScore | None, incoming: ModalityScore, label: str) -> ModalityScore:
        if current is None:
            return incoming

        sub_scores = dict((current.evidence or {}).get("sub_scores") or {})
        current_mode = str((current.evidence or {}).get("mode") or "pose")
        if current_mode not in sub_scores:
            sub_scores[current_mode] = {
                "score": current.score_0_1,
                "confidence": current.confidence_0_1,
            }
        sub_scores[label] = {
            "score": incoming.score_0_1,
            "confidence": incoming.confidence_0_1,
        }

        weighted_total = sum(float(v["score"]) * float(v["confidence"]) for v in sub_scores.values())
        confidence_total = sum(float(v["confidence"]) for v in sub_scores.values())
        combined = weighted_total / confidence_total if confidence_total else max(float(v["score"]) for v in sub_scores.values())
        confidence = min(1.0, confidence_total / max(1, len(sub_scores)))

        evidence = {
            **(current.evidence or {}),
            label: incoming.evidence,
            "mode": "specialized_video_fusion",
            "sub_scores": sub_scores,
        }
        return ModalityScore(
            modality="video",
            score_0_1=round(max(0.0, min(1.0, combined)), 3),
            confidence_0_1=round(max(0.0, min(1.0, confidence)), 3),
            evidence=evidence,
        )

    @staticmethod
    def _merge_clinical_scores(current: ModalityScore | None, incoming: ModalityScore, label: str) -> ModalityScore:
        if current is None:
            return incoming
        sub_scores = dict((current.evidence or {}).get("sub_scores") or {})
        current_method = str((current.evidence or {}).get("method") or "snapshot_rules")
        if current_method not in sub_scores:
            sub_scores[current_method] = {
                "score": current.score_0_1,
                "confidence": current.confidence_0_1,
            }
        sub_scores[label] = {
            "score": incoming.score_0_1,
            "confidence": incoming.confidence_0_1,
        }
        combined = max(float(v["score"]) for v in sub_scores.values())
        confidence = min(1.0, max(float(v["confidence"]) for v in sub_scores.values()))
        evidence = {
            **(current.evidence or {}),
            label: incoming.evidence,
            "method": "clinical_snapshot_and_temporal_fusion",
            "sub_scores": sub_scores,
        }
        return ModalityScore(
            modality="clinical",
            score_0_1=round(max(0.0, min(1.0, combined)), 3),
            confidence_0_1=round(max(0.0, min(1.0, confidence)), 3),
            evidence=evidence,
        )

    @staticmethod
    def write_report(report: dict[str, Any], out: str | Path) -> Path:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
