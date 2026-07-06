"""End-to-end video analysis demo: YOLOv8n-Pose → keypoints → PoseExtractor → evidence.

Demonstrates the full pipeline:
1. Load a video file (.avi/.mp4)
2. Run YOLOv8n-Pose to extract keypoints per frame
3. Feed extracted keypoints to PoseExtractor (defensive posture heuristic)
4. Run VisualWellbeingExtractor on same video
5. Fuse with pipeline and generate evidence JSON
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def extract_keypoints_from_video(video_path: Path, model_path: Path, max_frames: int = 10) -> dict[str, list]:
    """Run YOLOv8n-Pose on video frames and extract COCO17 keypoints."""
    from ultralytics import YOLO
    import cv2
    import numpy as np

    model = YOLO(str(model_path))
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    indices = np.linspace(0, max(0, total_frames - 1), num=min(max_frames, max(1, total_frames)), dtype=int)

    all_keypoints: dict[str, list] = {}

    for i, frame_idx in enumerate(indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        results = model.predict(source=frame, conf=0.3, verbose=False)
        frame_detections = []

        for r in results:
            if r.keypoints is None:
                continue
            for person_idx in range(len(r.keypoints)):
                kpts = r.keypoints[person_idx].data[0]  # shape: (17, 3)
                keypoints_list = [[float(kpts[j][0]), float(kpts[j][1]), float(kpts[j][2])] for j in range(17)]
                frame_detections.append({"keypoints": keypoints_list})

        if frame_detections:
            all_keypoints[str(i)] = frame_detections

    cap.release()
    return all_keypoints


def main():
    # Find a sample video
    video_path = Path(PROJECT_ROOT / "archive" / "DAiSEE" / "DataSet" / "Test" / "500044" / "5000441001" / "5000441001.avi")
    if not video_path.exists():
        # Fallback: find any .avi in archive
        for p in (PROJECT_ROOT / "archive" / "DAiSEE").rglob("*.avi"):
            video_path = p
            break
    
    if not video_path.exists():
        print("ERROR: No video file found for demo")
        return 1

    model_path = PROJECT_ROOT / "models" / "yolov8n-pose.pt"
    if not model_path.exists():
        print(f"ERROR: Pose model not found: {model_path}")
        return 1

    print(f"=== End-to-End Video Analysis Demo ===")
    print(f"Video: {video_path.name} ({video_path.stat().st_size / 1024:.0f} KB)")
    print(f"Model: {model_path.name}")
    print()

    # Step 1: Extract keypoints with YOLOv8n-Pose
    print("[1/4] Extracting keypoints with YOLOv8n-Pose...")
    keypoints = extract_keypoints_from_video(video_path, model_path, max_frames=10)
    print(f"      → {len(keypoints)} frames with person detected")

    # Save intermediate keypoints
    kp_path = RESULTS_DIR / "evidence_video_keypoints_extracted.json"
    kp_path.write_text(json.dumps({
        "source_video": video_path.name,
        "model": "yolov8n-pose.pt",
        "frames_processed": 10,
        "frames_with_person": len(keypoints),
        "keypoints": keypoints,
    }, indent=2), encoding="utf-8")
    print(f"      → Keypoints saved: {kp_path.name}")

    # Step 2: Run PoseExtractor on keypoints
    print("[2/4] Running PoseExtractor (defensive posture heuristic)...")
    from src.extractors.pose import PoseExtractor
    pose_ext = PoseExtractor(min_conf=0.3)
    pose_score = pose_ext.score_from_payload(keypoints, confidence=0.8)
    print(f"      → Pose score: {pose_score.score_0_1:.3f} (confidence: {pose_score.confidence_0_1:.3f})")
    print(f"      → Evidence: {pose_score.evidence}")

    # Step 3: Run VisualWellbeingExtractor
    print("[3/4] Running VisualWellbeingExtractor (DAiSEE baseline)...")
    import gc
    gc.collect()  # Free YOLO memory before loading next model
    from src.extractors.visual_wellbeing import VisualWellbeingExtractor
    vis_ext = VisualWellbeingExtractor(model_path=PROJECT_ROOT / "models" / "daisee_visual_baseline" / "daisee_visual_baseline.joblib", max_frames=10)
    vis_result = vis_ext.predict(video_path)
    print(f"      → Visual strain: {vis_result.get('visualStrain', 'N/A')}")
    print(f"      → Predictions: {vis_result.get('predictions', {})}")
    sys.stdout.flush()

    # Step 4: Run full pipeline with video
    print("[4/4] Running full SentinelaPipeline with video...")
    from src.pipeline import SentinelaPipeline

    # Save keypoints as temp JSON for pipeline
    import tempfile
    tmp_kp = Path(tempfile.mkdtemp()) / "pose_keypoints.json"
    tmp_kp.write_text(json.dumps(keypoints), encoding="utf-8")

    pipeline = SentinelaPipeline()
    report = pipeline.analyze(
        pose_json=tmp_kp,
        video_file=video_path,
    )

    # Save full evidence
    evidence = {
        "demo": "end_to_end_video_analysis",
        "source_video": video_path.name,
        "pipeline_steps": [
            "YOLOv8n-Pose keypoint extraction",
            "PoseExtractor defensive posture heuristic",
            "VisualWellbeingExtractor (DAiSEE baseline)",
            "FusionEngine + RiskEngine + CareEngine",
        ],
        "pose_extraction": {
            "model": "yolov8n-pose.pt",
            "frames_analyzed": 10,
            "frames_with_person": len(keypoints),
            "pose_score": pose_score.score_0_1,
            "pose_confidence": pose_score.confidence_0_1,
            "pose_evidence": pose_score.evidence,
        },
        "visual_wellbeing": vis_result,
        "full_pipeline_report": report,
    }

    out_path = RESULTS_DIR / "evidence_video_end_to_end.json"
    out_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    print()
    print(f"=== Results ===")
    print(f"Multimodal score: {report['multimodal_score_0_1']}")
    print(f"Risk level: {report['level']}")
    print(f"Priority: {report.get('priority', {}).get('riskLevel', 'N/A')}")
    print(f"Care pathway: {report.get('care_assessment', {}).get('carePathway', 'N/A')}")
    print(f"Evidence saved: {out_path.name}")
    print()
    print("✓ End-to-end video analysis completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
