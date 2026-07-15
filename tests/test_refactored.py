from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.config import PipelineConfig, FusionWeights
from src.config import AzureConfig
from src.cloud.azure_integration import build_azure_receipt
from src.domain.types import ModalityScore
from src.engines import FusionEngine, RiskEngine, CareEngine
from src.extractors.objects import SharpObjectDetector
from src.extractors.text import TextExtractor
from src.pipeline import SentinelaPipeline


class TestTextExtractor(unittest.TestCase):
    def test_detects_safety_signals(self):
        ext = TextExtractor()
        result = ext.analyze("Tenho medo, sofro ameaca e muita ansiedade.")
        self.assertGreater(result["overall_text_signal"], 0.0)
        self.assertGreater(result["labels"]["safety_concern"]["score"], 0.0)

    def test_detects_womens_health_specific_text_signals(self):
        ext = TextExtractor()
        result = ext.analyze(
            "No pos-parto sinto choro constante, medo do parto e sangramento anormal."
        )
        self.assertGreater(result["labels"]["postpartum_depression"]["score"], 0.0)
        self.assertGreater(result["labels"]["gestational_anxiety"]["score"], 0.0)
        self.assertGreater(result["labels"]["gynecological_risk"]["score"], 0.0)

    def test_empty_text_returns_zero(self):
        ext = TextExtractor()
        result = ext.score("")
        self.assertEqual(result.score_0_1, 0.0)


class TestFusionEngine(unittest.TestCase):
    def test_fuses_all_four_modalities(self):
        engine = FusionEngine()
        report = engine.fuse(
            video=ModalityScore(modality="video", score_0_1=0.6, confidence_0_1=0.8),
            audio=ModalityScore(modality="audio", score_0_1=0.5, confidence_0_1=0.7),
            text=ModalityScore(modality="text", score_0_1=0.4, confidence_0_1=0.9),
            objects=ModalityScore(modality="objects", score_0_1=0.8, confidence_0_1=0.95),
        )
        self.assertGreater(report.multimodal_score_0_1, 0.0)
        self.assertEqual(len(report.modality_scores), 4)

    def test_objects_high_score_triggers_critical(self):
        engine = FusionEngine()
        report = engine.fuse(
            objects=ModalityScore(modality="objects", score_0_1=0.9, confidence_0_1=0.95),
        )
        self.assertEqual(report.level, "critical")

    def test_unavailable_objects_are_not_counted_as_zero_risk(self):
        engine = FusionEngine()
        report = engine.fuse(
            video=ModalityScore(modality="video", score_0_1=0.35, confidence_0_1=0.55),
            objects=ModalityScore(
                modality="objects",
                score_0_1=0.0,
                confidence_0_1=0.0,
                evidence={"available": False, "reason": "model_not_found"},
            ),
        )
        self.assertEqual(report.level, "medium")
        self.assertNotIn("objects", report.modality_scores)
        self.assertIn("objects", report.metadata["missing"])
        self.assertEqual(report.metadata["unavailable"]["objects"], "model_not_found")

    def test_single_modality_coverage_penalty(self):
        engine = FusionEngine()
        report = engine.fuse(text=ModalityScore(modality="text", score_0_1=0.8, confidence_0_1=0.9))
        self.assertLess(report.multimodal_score_0_1, 0.8)


class TestRiskEngine(unittest.TestCase):
    def test_urgente_level(self):
        engine = RiskEngine()
        report = FusionEngine().fuse(
            video=ModalityScore(modality="video", score_0_1=0.9, confidence_0_1=0.9),
            audio=ModalityScore(modality="audio", score_0_1=0.8, confidence_0_1=0.9),
            text=ModalityScore(modality="text", score_0_1=0.7, confidence_0_1=0.9),
        )
        priority = engine.prioritize(report)
        self.assertEqual(priority["riskLevel"], "URGENTE")
        self.assertTrue(priority["humanReviewRequired"])

    def test_unavailable_objects_require_human_review(self):
        report = FusionEngine().fuse(
            video=ModalityScore(modality="video", score_0_1=0.35, confidence_0_1=0.55),
            objects=ModalityScore(
                modality="objects",
                score_0_1=0.0,
                confidence_0_1=0.0,
                evidence={"available": False, "reason": "model_not_found"},
            ),
        )
        priority = RiskEngine().prioritize(report)
        self.assertEqual(priority["riskLevel"], "MONITORAR")
        self.assertLessEqual(priority["confidence"], 0.45)
        self.assertTrue(priority["humanReviewRequired"])
        self.assertIn("low_confidence", priority["anomalyFlags"])
        self.assertIn("object_detection_unavailable", priority["anomalyFlags"])

    def test_detected_object_requires_human_review_even_with_low_fusion_score(self):
        report = FusionEngine().fuse(
            video=ModalityScore(modality="video", score_0_1=0.05, confidence_0_1=0.9),
            objects=ModalityScore(modality="objects", score_0_1=0.25, confidence_0_1=0.8),
        )
        priority = RiskEngine().prioritize(report)
        self.assertEqual(priority["riskLevel"], "MONITORAR")
        self.assertTrue(priority["humanReviewRequired"])
        self.assertIn("sharp_object_detected", priority["anomalyFlags"])


class TestCareEngine(unittest.TestCase):
    def test_objects_in_review_focus(self):
        care = CareEngine()
        report = FusionEngine().fuse(
            objects=ModalityScore(modality="objects", score_0_1=0.7, confidence_0_1=0.9),
        )
        assessment = care.assess(report)
        self.assertTrue(any("cortantes" in f for f in assessment["reviewFocus"]))

    def test_any_detected_object_moves_care_to_monitoring(self):
        care = CareEngine()
        report = FusionEngine().fuse(
            objects=ModalityScore(modality="objects", score_0_1=0.25, confidence_0_1=0.8),
        )
        assessment = care.assess(report)
        self.assertEqual(assessment["carePathway"], "acolhimento_e_monitoramento")


class TestSharpObjectDetector(unittest.TestCase):
    def test_missing_custom_model_can_fall_back_to_coco(self):
        detector = SharpObjectDetector(model_path=Path("missing-best.pt"))
        self.assertEqual(detector._fallback_model, "yolov8n.pt")
        self.assertIn("knife", detector._fallback_risk_classes)
        self.assertIn("scissors", detector._fallback_risk_classes)
        self.assertIn("fork", detector._fallback_risk_classes)
        self.assertEqual(detector._fallback_conf, 0.25)

    def test_can_disable_fallback_for_unavailable_model(self):
        detector = SharpObjectDetector(model_path=Path("missing-best.pt"), fallback_model=None)
        result = detector.score(Path("unused.jpg"))
        self.assertFalse(result.evidence["available"])
        self.assertIn("model_unavailable", result.evidence["reason"])


class TestObjectDetectionBehavior(unittest.TestCase):
    """Tests for object detection integration with risk/care engines."""

    def test_detected_object_never_stays_rotina(self):
        """Any detected sharp object must escalate beyond ROTINA."""
        engine = RiskEngine()
        # Object detected with moderate score
        report = FusionEngine().fuse(
            objects=ModalityScore(modality="objects", score_0_1=0.4, confidence_0_1=0.8),
        )
        priority = engine.prioritize(report)
        self.assertNotEqual(priority["riskLevel"], "ROTINA")
        self.assertTrue(priority["humanReviewRequired"])
        self.assertIn("sharp_object_detected", priority["anomalyFlags"])

    def test_detected_object_low_score_still_escalates(self):
        """Even low-confidence detection escalates to MONITORAR."""
        report = FusionEngine().fuse(
            objects=ModalityScore(modality="objects", score_0_1=0.15, confidence_0_1=0.5),
        )
        priority = RiskEngine().prioritize(report)
        self.assertEqual(priority["riskLevel"], "MONITORAR")
        self.assertTrue(priority["humanReviewRequired"])

    def test_unavailable_detector_is_warning_not_false_low(self):
        """When detector is unavailable, system must not give false 'low risk'."""
        report = FusionEngine().fuse(
            text=ModalityScore(modality="text", score_0_1=0.3, confidence_0_1=0.9),
            objects=ModalityScore(
                modality="objects", score_0_1=0.0, confidence_0_1=0.0,
                evidence={"available": False, "reason": "model_not_found"},
            ),
        )
        # Should escalate to at least medium because objects unavailable
        self.assertEqual(report.level, "medium")
        priority = RiskEngine().prioritize(report)
        self.assertTrue(priority["humanReviewRequired"])
        self.assertIn("object_detection_unavailable", priority["anomalyFlags"])

    def test_high_object_score_triggers_critical(self):
        """Object score >= 0.85 should escalate to critical."""
        report = FusionEngine().fuse(
            objects=ModalityScore(modality="objects", score_0_1=0.9, confidence_0_1=0.95),
        )
        self.assertEqual(report.level, "critical")

    def test_object_in_multimodal_context_escalates_care(self):
        """Object detected alongside text signals goes to monitoring pathway."""
        care = CareEngine()
        report = FusionEngine().fuse(
            text=ModalityScore(modality="text", score_0_1=0.4, confidence_0_1=0.9),
            objects=ModalityScore(modality="objects", score_0_1=0.5, confidence_0_1=0.8),
        )
        assessment = care.assess(report)
        self.assertIn(assessment["carePathway"],
                      ["acolhimento_e_monitoramento", "revisao_prioritaria"])
        self.assertTrue(any("cortantes" in f for f in assessment["reviewFocus"]))

    def test_fusion_continues_with_missing_modalities(self):
        """Pipeline handles graceful degradation when some modalities absent."""
        engine = FusionEngine()
        # Only text available
        report = engine.fuse(
            text=ModalityScore(modality="text", score_0_1=0.5, confidence_0_1=0.9),
        )
        self.assertGreater(report.multimodal_score_0_1, 0)
        self.assertEqual(report.metadata["coverage_penalty"], 0.88)  # single modality


class TestPipeline(unittest.TestCase):
    def test_text_only_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.txt"
            path.write_text("Tenho medo e ansiedade.", encoding="utf-8")
            pipe = SentinelaPipeline()
            report = pipe.analyze(transcript=path)
        self.assertIn("care_assessment", report)
        self.assertIn("priority", report)

    def test_rejects_no_input(self):
        pipe = SentinelaPipeline()
        with self.assertRaises(ValueError):
            pipe.analyze()

    def test_video_subscores_are_combined(self):
        merged = SentinelaPipeline._merge_video_scores(
            ModalityScore(modality="video", score_0_1=0.4, confidence_0_1=0.8, evidence={"mode": "pose"}),
            ModalityScore(modality="video", score_0_1=0.8, confidence_0_1=0.6, evidence={"mode": "motion"}),
            "motion",
        )
        self.assertEqual(merged.evidence["mode"], "specialized_video_fusion")
        self.assertIn("pose", merged.evidence["sub_scores"])
        self.assertIn("motion", merged.evidence["sub_scores"])
        self.assertGreater(merged.score_0_1, 0.4)


class TestAzureIntegration(unittest.TestCase):
    def test_local_receipt_queues_alert_when_human_review_is_required(self):
        receipt = build_azure_receipt(
            report={
                "level": "medium",
                "multimodal_score_0_1": 0.52,
                "priority": {"humanReviewRequired": True},
            },
            provided_modalities=["text", "audio", "video"],
            config=AzureConfig(),
        )

        self.assertEqual(receipt["provider"], "azure")
        self.assertEqual(receipt["mode"], "local_simulation")
        self.assertTrue(receipt["alert"]["required"])
        self.assertEqual(receipt["alert"]["status"], "queued_for_medical_team")
        self.assertIn("audio", receipt["managed_services"])

    def test_configured_receipt_detects_credentials(self):
        receipt = build_azure_receipt(
            report={
                "level": "low",
                "multimodal_score_0_1": 0.12,
                "priority": {"humanReviewRequired": False},
            },
            provided_modalities=["clinical"],
            config=AzureConfig(
                cognitive_endpoint="https://example.cognitiveservices.azure.com/",
                cognitive_key="secret",
            ),
        )

        self.assertEqual(receipt["mode"], "configured")
        self.assertFalse(receipt["alert"]["required"])


if __name__ == "__main__":
    unittest.main()
