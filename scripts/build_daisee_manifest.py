from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def _read_labels(path: Path, split: str) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean = {str(k).strip(): str(v).strip() for k, v in row.items()}
            clip = clean.get("ClipID")
            if not clip:
                continue
            rows.append(
                {
                    "dataset": "daisee",
                    "split": split,
                    "clip_id": clip,
                    "subject_id": clip[:6],
                    "boredom": int(clean.get("Boredom", 0)),
                    "engagement": int(clean.get("Engagement", 0)),
                    "confusion": int(clean.get("Confusion", 0)),
                    "frustration": int(clean.get("Frustration", 0)),
                }
            )
    return rows


def _find_video(dataset_dir: Path, split: str, subject_id: str, clip_id: str) -> Path | None:
    candidate = dataset_dir / split / subject_id / Path(clip_id).stem / clip_id
    if candidate.exists():
        return candidate
    matches = list((dataset_dir / split).glob(f"*/{Path(clip_id).stem}/{clip_id}"))
    return matches[0] if matches else None


def build_manifest(root: Path) -> tuple[list[dict], dict]:
    labels_dir = root / "Labels"
    dataset_dir = root / "DataSet"
    split_files = {
        "train": labels_dir / "TrainLabels.csv",
        "validation": labels_dir / "ValidationLabels.csv",
        "test": labels_dir / "TestLabels.csv",
    }

    rows: list[dict] = []
    for split, labels_path in split_files.items():
        if not labels_path.exists():
            continue
        for row in _read_labels(labels_path, split):
            video_path = _find_video(dataset_dir, split.capitalize() if split != "train" else "Train", row["subject_id"], row["clip_id"])
            row["path"] = video_path.as_posix() if video_path else ""
            row["relative_path"] = video_path.relative_to(root.parent).as_posix() if video_path else ""
            row["available"] = bool(video_path)
            rows.append(row)

    summary = {
        "total_rows": len(rows),
        "available_videos": sum(1 for row in rows if row["available"]),
        "by_split": dict(sorted(Counter(row["split"] for row in rows).items())),
        "label_distributions": {
            label: dict(sorted(Counter(row[label] for row in rows).items()))
            for label in ("boredom", "engagement", "confusion", "frustration")
        },
        "recommended_use": (
            "Public visual-affective baseline for engagement, boredom, confusion and frustration. "
            "Use as indirect wellbeing/attention context, not as trauma or abuse labels."
        ),
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a DAiSEE manifest from local labels/videos.")
    parser.add_argument("--root", default="archive/DAiSEE")
    parser.add_argument("--out", default="data/manifests/daisee_manifest.csv")
    parser.add_argument("--summary-out", default="data/manifests/daisee_summary.json")
    args = parser.parse_args()

    root = Path(args.root)
    rows, summary = build_manifest(root)
    if not rows:
        raise SystemExit(f"ERROR: no DAiSEE rows found under {root}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(rows)} rows -> {out_path.as_posix()}")
    print(f"Wrote summary -> {summary_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
