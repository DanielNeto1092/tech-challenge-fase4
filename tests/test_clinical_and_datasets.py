"""Tests for clinical modality, label mapping, manifests, and multimodal fusion."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from src.config import PipelineConfig, FusionWeights
from src.domain.labels import (
    SENTINELA_LABELS,
    RAVDESS_CODE_TO_EMOTION,
    RAVDESS_EMOTION_MAP,
    MATERNAL_RISK_MAP,
    CTG_NSP_MAP,
    eatd_severity_to_sentinela,
)
from src.domain.types import ModalityScore
from src.engines import FusionEngine, RiskEngine, CareEngine
from src.extractors.clinical import ClinicalExtractor, ClinicalInput
from src.pipeline import SentinelaPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ======================================================================
# LABEL MAPPING TESTS
# ======================================================================
class TestLabelMapping(unittest.TestCase):
    """Verify Sentinela label taxonomy and dataset-to-domain mappings."""

    def test_sentinela_labels_are_valid(self):
        self.assertEqual(len(SENTINELA_LABELS), 8)
        self.assertIn("psychological_distress", SENTINELA_LABELS)
        self.assertIn("obstetric_risk", SENTINELA_LABELS)
        self.assertIn("fetal_risk", SENTINELA_LABELS)
        self.assertIn("normal_or_low_risk", SENTINELA_LABELS)

    def test_ravdess_all_emotions_mapped(self):
        for code in ["01", "02", "03", "04", "05", "06", "07", "08"]:
            emotion = RAVDESS_CODE_TO_EMOTION[code]
            self.assertIn(emotion, RAVDESS_EMOTION_MAP)
            self.assertIn(RAVDESS_EMOTION_MAP[emotion], SENTINELA_LABELS)

    def test_maternal_risk_mapping(self):
        self.assertEqual(MATERNAL_RISK_MAP["low risk"], "normal_or_low_risk")
        self.assertEqual(MATERNAL_RISK_MAP["mid risk"], "obstetric_risk")
        self.assertEqual(MATERNAL_RISK_MAP["high risk"], "fetal_risk")

    def test_ctg_nsp_mapping(self):
        self.assertEqual(CTG_NSP_MAP[1], "normal_or_low_risk")
        self.assertEqual(CTG_NSP_MAP[2], "obstetric_risk")
        self.assertEqual(CTG_NSP_MAP[3], "fetal_risk")

    def test_eatd_severity_to_sentinela(self):
        self.assertEqual(eatd_severity_to_sentinela(30), "normal_or_low_risk")
        self.assertEqual(eatd_severity_to_sentinela(45), "anxiety_or_fear")
        self.assertEqual(eatd_severity_to_sentinela(55), "psychological_distress")
        self.assertEqual(eatd_severity_to_sentinela(70), "depression_signal")


# ======================================================================
# MANIFEST TESTS
# ======================================================================
class TestManifests(unittest.TestCase):
    """Verify manifest files exist and have correct structure."""

    MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"
    EXPECTED_MANIFESTS = [
        "ravdess_manifest.csv",
        "eatd_corpus_manifest.csv",
        "daisee_manifest.csv",
        "maternal_health_risk_manifest.csv",
        "cardiotocography_manifest.csv",
        "xd_violence_manifest.csv",
    ]
    REQUIRED_COLUMNS = [
        "file_path", "dataset", "modality", "label_original",
        "label_sentinela", "split", "source_url", "notes",
    ]

    def test_all_manifests_exist(self):
        for name in self.EXPECTED_MANIFESTS:
            path = self.MANIFESTS_DIR / name
            self.assertTrue(path.exists(), f"Missing manifest: {name}")

    def test_manifests_have_correct_columns(self):
        for name in self.EXPECTED_MANIFESTS:
            path = self.MANIFESTS_DIR / name
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    for col in self.REQUIRED_COLUMNS:
                        self.assertIn(col, reader.fieldnames, f"{name} missing column: {col}")

    def test_maternal_manifest_has_rows(self):
        path = self.MANIFESTS_DIR / "maternal_health_risk_manifest.csv"
        with open(path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertGreater(len(rows), 100)
        # All sentinela labels should be valid
        for row in rows[:10]:
            self.assertIn(row["label_sentinela"], SENTINELA_LABELS)
            self.assertEqual(row["modality"], "clinical")

    def test_ravdess_manifest_has_audio(self):
        path = self.MANIFESTS_DIR / "ravdess_manifest.csv"
        with open(path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertGreater(len(rows), 100)
        for row in rows[:10]:
            self.assertEqual(row["modality"], "audio")
            self.assertIn(row["label_sentinela"], SENTINELA_LABELS)


# ======================================================================
# CLINICAL EXTRACTOR TESTS
# ======================================================================
class TestClinicalExtractor(unittest.TestCase):
    """Test clinical/obstetric risk scoring."""

    def setUp(self):
        self.extractor = ClinicalExtractor()

    def test_maternal_high_risk(self):
        clinical = ClinicalInput(risk_label="high risk", source="test")
        ms = self.extractor.score(clinical)
        self.assertEqual(ms.modality, "clinical")
        self.assertGreater(ms.score_0_1, 0.7)
        self.assertGreater(ms.confidence_0_1, 0.8)
        self.assertEqual(ms.evidence["sentinela_label"], "fetal_risk")

    def test_maternal_low_risk(self):
        clinical = ClinicalInput(risk_label="low risk", source="test")
        ms = self.extractor.score(clinical)
        self.assertLess(ms.score_0_1, 0.2)
        self.assertEqual(ms.evidence["sentinela_label"], "normal_or_low_risk")

    def test_ctg_pathological(self):
        clinical = ClinicalInput(nsp_class=3, source="test")
        ms = self.extractor.score(clinical)
        self.assertGreater(ms.score_0_1, 0.8)
        self.assertEqual(ms.evidence["sentinela_label"], "fetal_risk")
        self.assertEqual(ms.evidence["risk_level"], "URGENTE")

    def test_ctg_normal(self):
        clinical = ClinicalInput(nsp_class=1, source="test")
        ms = self.extractor.score(clinical)
        self.assertLess(ms.score_0_1, 0.2)
        self.assertEqual(ms.evidence["risk_level"], "ROTINA")

    def test_ctg_suspect(self):
        clinical = ClinicalInput(nsp_class=2, source="test")
        ms = self.extractor.score(clinical)
        self.assertGreater(ms.score_0_1, 0.4)
        self.assertLess(ms.score_0_1, 0.7)
        self.assertEqual(ms.evidence["risk_level"], "MONITORAR")

    def test_vital_signs_hypertension(self):
        clinical = ClinicalInput(systolic_bp=150, heart_rate=105, source="test")
        ms = self.extractor.score(clinical)
        self.assertGreater(ms.score_0_1, 0.3)
        self.assertIn("hypertension", ms.evidence["signals"])
        self.assertIn("tachycardia", ms.evidence["signals"])

    def test_body_temperature_celsius_detects_fever(self):
        clinical = ClinicalInput(body_temp=38.2, body_temp_unit="C", source="test")
        ms = self.extractor.score(clinical)
        self.assertIn("fever", ms.evidence["signals"])
        self.assertEqual(ms.evidence["body_temp_unit"], "C")

    def test_from_mapping_accepts_ctg_and_maternal_risk_fields(self):
        clinical = ClinicalExtractor.from_mapping({
            "risk_label": "high risk",
            "nsp_class": 3,
            "baseline_fhr": 175,
            "body_temp": 38.1,
            "body_temp_unit": "C",
        })
        self.assertEqual(clinical.risk_label, "high risk")
        self.assertEqual(clinical.nsp_class, 3)
        self.assertEqual(clinical.baseline_fhr, 175.0)
        self.assertEqual(clinical.body_temp_unit, "C")

    def test_from_maternal_csv_row(self):
        row = {"Age": "35", "SystolicBP": "140", "DiastolicBP": "90",
               "BS": "13", "BodyTemp": "98", "HeartRate": "70", "RiskLevel": "high risk"}
        clinical = ClinicalExtractor.from_maternal_csv_row(row)
        self.assertEqual(clinical.age, 35.0)
        self.assertEqual(clinical.risk_label, "high risk")
        ms = self.extractor.score(clinical)
        self.assertGreater(ms.score_0_1, 0.7)


# ======================================================================
# FUSION WITH CLINICAL MODALITY
# ======================================================================
class TestClinicalFusion(unittest.TestCase):
    """Test fusion engine accepts and processes clinical modality."""

    def test_clinical_only(self):
        engine = FusionEngine()
        report = engine.fuse(
            clinical=ModalityScore(modality="clinical", score_0_1=0.85, confidence_0_1=0.9),
        )
        self.assertGreater(report.multimodal_score_0_1, 0.0)
        self.assertIn("clinical", report.modality_scores)
        self.assertEqual(report.level, "critical")

    def test_clinical_plus_text(self):
        engine = FusionEngine()
        report = engine.fuse(
            text=ModalityScore(modality="text", score_0_1=0.5, confidence_0_1=0.9),
            clinical=ModalityScore(modality="clinical", score_0_1=0.55, confidence_0_1=0.85),
        )
        self.assertGreater(report.multimodal_score_0_1, 0.3)
        self.assertEqual(len(report.modality_scores), 2)
        self.assertEqual(report.level, "medium")

    def test_five_modalities_full_coverage(self):
        engine = FusionEngine()
        report = engine.fuse(
            video=ModalityScore(modality="video", score_0_1=0.3, confidence_0_1=0.8),
            audio=ModalityScore(modality="audio", score_0_1=0.4, confidence_0_1=0.7),
            text=ModalityScore(modality="text", score_0_1=0.5, confidence_0_1=0.9),
            objects=ModalityScore(modality="objects", score_0_1=0.2, confidence_0_1=0.8),
            clinical=ModalityScore(modality="clinical", score_0_1=0.6, confidence_0_1=0.85),
        )
        self.assertEqual(len(report.modality_scores), 5)
        self.assertEqual(report.metadata["coverage_penalty"], 1.0)

    def test_clinical_high_triggers_critical(self):
        engine = FusionEngine()
        report = engine.fuse(
            clinical=ModalityScore(modality="clinical", score_0_1=0.85, confidence_0_1=0.9),
        )
        self.assertEqual(report.level, "critical")

    def test_clinical_does_not_break_existing_modalities(self):
        """Original 4-modality fusion still works without clinical."""
        engine = FusionEngine()
        report = engine.fuse(
            video=ModalityScore(modality="video", score_0_1=0.6, confidence_0_1=0.8),
            audio=ModalityScore(modality="audio", score_0_1=0.5, confidence_0_1=0.7),
            text=ModalityScore(modality="text", score_0_1=0.4, confidence_0_1=0.9),
            objects=ModalityScore(modality="objects", score_0_1=0.3, confidence_0_1=0.85),
        )
        self.assertEqual(len(report.modality_scores), 4)
        self.assertGreater(report.multimodal_score_0_1, 0.0)
        self.assertNotIn("clinical", report.modality_scores)


# ======================================================================
# CARE ENGINE WITH CLINICAL
# ======================================================================
class TestCareEngineWithClinical(unittest.TestCase):
    """Test care engine handles obstetric risk pathway."""

    def test_clinical_high_triggers_review(self):
        care = CareEngine()
        report = FusionEngine().fuse(
            clinical=ModalityScore(modality="clinical", score_0_1=0.85, confidence_0_1=0.9),
        )
        assessment = care.assess(report)
        self.assertEqual(assessment["carePathway"], "revisao_prioritaria")
        self.assertTrue(any("obstetrico" in f or "clinica" in f for f in assessment["reviewFocus"]))

    def test_clinical_mid_triggers_monitoring(self):
        care = CareEngine()
        report = FusionEngine().fuse(
            clinical=ModalityScore(modality="clinical", score_0_1=0.55, confidence_0_1=0.85),
        )
        assessment = care.assess(report)
        self.assertEqual(assessment["carePathway"], "acolhimento_e_monitoramento")

    def test_obstetric_risk_dimension_present(self):
        care = CareEngine()
        report = FusionEngine().fuse(
            clinical=ModalityScore(modality="clinical", score_0_1=0.7, confidence_0_1=0.9),
        )
        assessment = care.assess(report)
        self.assertIn("obstetricRisk", assessment["dimensions"])
        self.assertGreater(assessment["dimensions"]["obstetricRisk"], 0.5)


# ======================================================================
# PIPELINE INTEGRATION WITH CLINICAL
# ======================================================================
class TestPipelineClinical(unittest.TestCase):
    """Test full pipeline with clinical data input."""

    def test_clinical_data_only(self):
        pipe = SentinelaPipeline()
        report = pipe.analyze(clinical_data=ClinicalInput(risk_label="high risk", source="test"))
        self.assertIn("priority", report)
        self.assertIn("care_assessment", report)
        self.assertEqual(report["priority"]["riskLevel"], "URGENTE")

    def test_text_plus_clinical(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.txt"
            path.write_text("Tenho medo e muita ansiedade.", encoding="utf-8")
            pipe = SentinelaPipeline()
            report = pipe.analyze(
                transcript=path,
                clinical_data=ClinicalInput(risk_label="mid risk", source="test"),
            )
        self.assertIn("care_assessment", report)
        modalities = report["care_assessment"]["availableModalities"]
        self.assertIn("text", modalities)
        self.assertIn("clinical", modalities)

    def test_clinical_ctg_through_pipeline(self):
        pipe = SentinelaPipeline()
        report = pipe.analyze(
            clinical_data=ClinicalInput(nsp_class=3, baseline_fhr=180, source="CTG")
        )
        self.assertEqual(report["priority"]["riskLevel"], "URGENTE")
        self.assertTrue(report["priority"]["humanReviewRequired"])


if __name__ == "__main__":
    unittest.main()
