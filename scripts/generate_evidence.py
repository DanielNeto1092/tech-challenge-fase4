"""Generate concrete evidence results for Tech Challenge evaluation.

This script runs the Sentinela pipeline on real test inputs to produce
demonstrable results in data/results/.

Usage:
    python -m scripts.generate_evidence
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import SentinelaPipeline
from src.config import PipelineConfig

RESULTS_DIR = PROJECT_ROOT / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _save(name: str, data: dict) -> Path:
    out = RESULTS_DIR / f"{name}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> Saved: {out.relative_to(PROJECT_ROOT)}")
    return out


def evidence_object_detection():
    """Run object detection on an image where COCO YOLOv8 detects a fork."""
    print("\n=== Evidence: Object Detection (fork image — COCO detectable) ===")
    # Use image known to be detectable by COCO YOLOv8n as 'fork' (conf ~0.89)
    test_image = PROJECT_ROOT / "Sharp Objects Detection.yolov8" / "train" / "images" / "fork_00_jpg.rf.ZQtObiTd116CaXJ7v2Oh.jpg"
    if not test_image.exists():
        # Fallback: search for any fork image
        images_dir = PROJECT_ROOT / "Sharp Objects Detection.yolov8" / "train" / "images"
        fork_images = sorted(images_dir.glob("fork_*"))
        if not fork_images:
            print("  [SKIP] No fork images found in dataset.")
            return
        test_image = fork_images[0]
    print(f"  Input: {test_image.name}")

    pipe = SentinelaPipeline()
    report = pipe.analyze(image_for_objects=str(test_image))
    _save("evidence_object_fork_detected", report)

    score = report.get("modality_scores", {}).get("objects", {}).get("score_0_1", 0)
    risk_level = report.get("priority", {}).get("riskLevel", "?")
    review = report.get("priority", {}).get("humanReviewRequired", False)
    print(f"  Objects score: {score}")
    print(f"  Risk level: {risk_level}")
    print(f"  Human review: {review}")


def evidence_scissors_detection():
    """Run object detection on a scissors image."""
    print("\n=== Evidence: Object Detection (scissors image) ===")
    images_dir = PROJECT_ROOT / "Sharp Objects Detection.yolov8" / "train" / "images"
    scissors_images = sorted(images_dir.glob("scissors_*"))
    if not scissors_images:
        print("  [SKIP] No scissors images found in dataset.")
        return
    test_image = scissors_images[0]
    print(f"  Input: {test_image.name}")

    pipe = SentinelaPipeline()
    report = pipe.analyze(image_for_objects=str(test_image))
    _save("evidence_object_scissors_detected", report)

    score = report.get("modality_scores", {}).get("objects", {}).get("score_0_1", 0)
    print(f"  Objects score: {score}")


def evidence_pose_defensive():
    """Run pose analysis with synthetic defensive posture data."""
    print("\n=== Evidence: Pose Defensive Posture ===")
    # Synthetic pose JSON with hands near face (defensive posture)
    # COCO17 keypoints: nose, left_eye, right_eye, left_ear, right_ear,
    # left_shoulder, right_shoulder, left_elbow, right_elbow,
    # left_wrist, right_wrist, left_hip, right_hip,
    # left_knee, right_knee, left_ankle, right_ankle
    defensive_pose = {
        "1": [
            {
                "keypoints": [
                    [320, 100, 0.95],  # nose
                    [310, 90, 0.90],   # left_eye
                    [330, 90, 0.90],   # right_eye
                    [300, 100, 0.85],  # left_ear
                    [340, 100, 0.85],  # right_ear
                    [280, 200, 0.92],  # left_shoulder
                    [360, 200, 0.92],  # right_shoulder
                    [290, 160, 0.88],  # left_elbow (bent up)
                    [350, 160, 0.88],  # right_elbow (bent up)
                    [310, 110, 0.90],  # left_wrist (near face!)
                    [330, 110, 0.90],  # right_wrist (near face!)
                    [290, 350, 0.90],  # left_hip
                    [350, 350, 0.90],  # right_hip
                    [290, 500, 0.85],  # left_knee
                    [350, 500, 0.85],  # right_knee
                    [290, 650, 0.80],  # left_ankle
                    [350, 650, 0.80],  # right_ankle
                ]
            }
        ],
        "2": [
            {
                "keypoints": [
                    [320, 100, 0.95],
                    [310, 90, 0.90],
                    [330, 90, 0.90],
                    [300, 100, 0.85],
                    [340, 100, 0.85],
                    [280, 200, 0.92],
                    [360, 200, 0.92],
                    [295, 155, 0.88],
                    [345, 155, 0.88],
                    [315, 108, 0.90],  # wrists very near nose
                    [325, 108, 0.90],
                    [290, 350, 0.90],
                    [350, 350, 0.90],
                    [290, 500, 0.85],
                    [350, 500, 0.85],
                    [290, 650, 0.80],
                    [350, 650, 0.80],
                ]
            }
        ],
        "3": [
            {
                "keypoints": [
                    [320, 100, 0.95],
                    [310, 90, 0.90],
                    [330, 90, 0.90],
                    [300, 100, 0.85],
                    [340, 100, 0.85],
                    [280, 200, 0.92],
                    [360, 200, 0.92],
                    [288, 158, 0.88],
                    [352, 158, 0.88],
                    [312, 112, 0.90],
                    [328, 112, 0.90],
                    [290, 350, 0.90],
                    [350, 350, 0.90],
                    [290, 500, 0.85],
                    [350, 500, 0.85],
                    [290, 650, 0.80],
                    [350, 650, 0.80],
                ]
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmp:
        pose_path = Path(tmp) / "defensive_pose.json"
        pose_path.write_text(json.dumps(defensive_pose), encoding="utf-8")

        pipe = SentinelaPipeline()
        report = pipe.analyze(pose_json=str(pose_path))

    _save("evidence_pose_defensive", report)
    score = report.get("modality_scores", {}).get("video", {}).get("score_0_1", 0)
    evidence = report.get("modality_scores", {}).get("video", {}).get("evidence", {})
    print(f"  Video (pose) score: {score}")
    print(f"  Hands near face: {evidence.get('hands_face', 'N/A')}")
    print(f"  Arms bent: {evidence.get('arms_bent', 'N/A')}")


def evidence_multimodal_text_audio_image():
    """Run full multimodal analysis with text + image (knife)."""
    print("\n=== Evidence: Multimodal (text + image with knife) ===")
    images_dir = PROJECT_ROOT / "Sharp Objects Detection.yolov8" / "train" / "images"
    knife_images = sorted(images_dir.glob("knife_*"))
    if not knife_images:
        print("  [SKIP] No knife images found.")
        return

    text_content = (
        "Estou com muito medo, ele me ameacou de novo. "
        "Sinto ansiedade e panico, nao tenho com quem falar. "
        "Ele controla meu celular e me proibe de ver minha familia."
    )

    with tempfile.TemporaryDirectory() as tmp:
        txt_path = Path(tmp) / "relato.txt"
        txt_path.write_text(text_content, encoding="utf-8")

        pipe = SentinelaPipeline()
        report = pipe.analyze(
            transcript=str(txt_path),
            image_for_objects=str(knife_images[0]),
        )

    _save("evidence_multimodal_text_objects", report)
    score = report.get("multimodal_score_0_1", 0)
    level = report.get("level", "?")
    risk_level = report.get("priority", {}).get("riskLevel", "?")
    modalities = list(report.get("modality_scores", {}).keys())
    print(f"  Modalities: {modalities}")
    print(f"  Multimodal score: {score:.3f}")
    print(f"  Level: {level}")
    print(f"  Risk level: {risk_level}")


def evidence_text_only_high_risk():
    """Run text-only with strong violence indicators."""
    print("\n=== Evidence: Text with strong risk signals ===")
    text_content = (
        "Ele me bate constantemente e me ameaca de morte. "
        "Estou isolada, sem apoio, sem familia e sem amigos. "
        "Sinto desesperanca, nao aguento mais essa situacao. "
        "Tenho medo de violencia, me sinto presa e controlada. "
        "Ele me proibe de sair, vigiar meu celular e me obriga a ficar em casa."
    )

    with tempfile.TemporaryDirectory() as tmp:
        txt_path = Path(tmp) / "relato_grave.txt"
        txt_path.write_text(text_content, encoding="utf-8")

        pipe = SentinelaPipeline()
        report = pipe.analyze(transcript=str(txt_path))

    _save("evidence_text_high_risk", report)
    score = report.get("multimodal_score_0_1", 0)
    level = report.get("level", "?")
    care_pathway = report.get("care_assessment", {}).get("carePathway", "?")
    print(f"  Text score: {score:.3f}")
    print(f"  Level: {level}")
    print(f"  Care pathway: {care_pathway}")


def main():
    print("=" * 60)
    print("Sentinela AI — Evidence Generation")
    print("=" * 60)

    # Always run pose evidence (no external deps)
    evidence_pose_defensive()
    evidence_text_only_high_risk()

    # Object detection requires ultralytics
    try:
        import ultralytics  # noqa: F401
        evidence_object_detection()
        evidence_scissors_detection()
        evidence_multimodal_text_audio_image()
    except ImportError:
        print("\n[WARN] ultralytics not installed — skipping object detection evidence.")
        print("       Install with: pip install ultralytics")

    print("\n" + "=" * 60)
    print("Evidence generation complete. Check data/results/evidence_*.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
