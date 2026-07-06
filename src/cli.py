"""CLI entry point for the Sentinela pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline import SentinelaPipeline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sentinela AI - Local Pipeline")
    p.add_argument("--transcript", default=None)
    p.add_argument("--audio-wav", default=None)
    p.add_argument("--pose-json", default=None)
    p.add_argument("--video-file", default=None)
    p.add_argument("--frames-dir", default=None)
    p.add_argument("--sequence", default=None)
    p.add_argument("--motion-calibration", default=None)
    p.add_argument("--image-for-objects", default=None)
    p.add_argument("--max-frames", type=int, default=None)
    p.add_argument("--out", default="data/results/risk_report.json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    pipe = SentinelaPipeline()

    report = pipe.analyze(
        transcript=args.transcript,
        audio_wav=args.audio_wav,
        pose_json=args.pose_json,
        video_file=args.video_file,
        frames_dir=args.frames_dir,
        sequence=args.sequence,
        motion_calibration=args.motion_calibration,
        image_for_objects=args.image_for_objects,
        max_frames=args.max_frames,
    )

    out = pipe.write_report(report, args.out)
    print(f"level={report['level']} score={report['multimodal_score_0_1']:.3f} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
