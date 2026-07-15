from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.api.app import AnalyzeRequest, analyze, health, reports
from src.pipeline import SentinelaPipeline
from src.extractors.text import TextExtractor


class SentinelaCoreTests(unittest.TestCase):
    def test_text_multilabel_detects_safety_and_distress(self) -> None:
        text = "Tenho medo, sofro ameaca e muita ansiedade. Nao aguento essa situacao."
        ext = TextExtractor()
        signals = ext.analyze(text)
        labels = signals["labels"]
        self.assertGreater(labels["safety_concern"]["score"], 0.0)
        self.assertGreater(labels["psychological_distress"]["score"], 0.0)
        self.assertGreater(signals["overall_text_signal"], 0.0)

    def test_analyze_case_text_only_returns_care_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.txt"
            path.write_text("Tenho medo e estou muito ansiosa.", encoding="utf-8")
            pipe = SentinelaPipeline()
            report = pipe.analyze(transcript=path)
        self.assertIn("care_assessment", report)
        self.assertIn("priority", report)

    def test_api_health_and_reports(self) -> None:
        self.assertEqual(health()["status"], "ok")
        self.assertIn("reports", reports())

    def test_api_json_accepts_clinical_data_and_returns_azure_receipt(self) -> None:
        payload = analyze(
            AnalyzeRequest(
                clinical_data={
                    "risk_label": "high risk",
                    "body_temp": 38.2,
                    "body_temp_unit": "C",
                    "source": "test",
                },
                save_as="api_clinical_test",
            )
        )
        self.assertIn("clinical", payload["modality_scores"])
        self.assertIn("_azure_integration", payload)
        self.assertEqual(payload["_azure_integration"]["provider"], "azure")

    def test_analyze_rejects_missing_transcript(self) -> None:
        pipe = SentinelaPipeline()
        with self.assertRaises(ValueError):
            pipe.analyze(transcript="does_not_exist.txt")

    def test_analyze_rejects_missing_audio(self) -> None:
        pipe = SentinelaPipeline()
        with self.assertRaises(ValueError):
            pipe.analyze(audio_wav="missing.wav")

    def test_analyze_rejects_missing_pose_json(self) -> None:
        pipe = SentinelaPipeline()
        with self.assertRaises(ValueError):
            pipe.analyze(pose_json="missing_pose.json")

    def test_analyze_rejects_frames_dir_not_valid(self) -> None:
        pipe = SentinelaPipeline()
        with self.assertRaises(ValueError):
            pipe.analyze(frames_dir="nonexistent_dir", sequence="Seq001")

    def test_analyze_rejects_missing_video_file(self) -> None:
        pipe = SentinelaPipeline()
        with self.assertRaises(ValueError):
            pipe.analyze(video_file="missing_video.mp4")


if __name__ == "__main__":
    unittest.main()
