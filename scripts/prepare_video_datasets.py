"""Prepare video/visual datasets (DAiSEE, XD-Violence, UCF-Crime) for Sentinela pipeline.

This script scans local dataset directories, extracts metadata, and generates
standardized manifests in data/manifests/ for training and evaluation.

Usage:
    python -m scripts.prepare_video_datasets [--daisee PATH] [--xdviolence PATH]

If datasets are not yet downloaded, this script prints instructions.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"

# DAiSEE label columns
DAISEE_LABELS = ["boredom", "engagement", "confusion", "frustration"]

# Sentinela domain mapping for video signals
VIDEO_DOMAIN_MAPPING = {
    "boredom_high": "disengagement_signal",
    "confusion_high": "distress_indicator",
    "frustration_high": "distress_indicator",
    "engagement_low": "disengagement_signal",
    "violence": "risk_critical",
    "abuse": "risk_critical",
    "normal": "baseline",
}

MANIFEST_COLUMNS = [
    "dataset", "relative_path", "modality", "label_original",
    "label_mapped", "sentinela_domain_label", "split", "subject_id",
    "license_note",
]


def scan_daisee(root: Path) -> list[dict]:
    """Scan DAiSEE directory: Train/Test/Validation splits with CSV labels."""
    rows = []
    if not root.exists():
        return rows

    # DAiSEE structure: {split}/{subject}/{clip}.avi + Labels/{split}.csv
    for split_name in ["Train", "Test", "Validation"]:
        split_dir = root / split_name
        if not split_dir.is_dir():
            continue
        split_mapped = {"Train": "train", "Test": "test", "Validation": "val"}.get(split_name, "train")

        for subject_dir in sorted(split_dir.iterdir()):
            if not subject_dir.is_dir():
                continue
            for clip_dir in sorted(subject_dir.iterdir()):
                if not clip_dir.is_dir():
                    continue
                for video in sorted(clip_dir.glob("*.avi")):
                    rows.append({
                        "dataset": "daisee",
                        "relative_path": video.relative_to(root.parent).as_posix(),
                        "modality": "video",
                        "label_original": "engagement_labels",
                        "label_mapped": "visual_wellbeing",
                        "sentinela_domain_label": "wellbeing_signal",
                        "split": split_mapped,
                        "subject_id": subject_dir.name,
                        "license_note": "Research use; IIT-D (Gupta et al. 2016)",
                    })
    return rows


def scan_xd_violence(root: Path) -> list[dict]:
    """Scan XD-Violence dataset: videos with violence/normal labels."""
    rows = []
    if not root.exists():
        return rows

    # XD-Violence typical structure: videos/ + annotations
    video_dir = root / "videos" if (root / "videos").exists() else root
    for video in sorted(video_dir.glob("*.mp4")):
        # Label from filename pattern (v=violence prefix convention)
        is_violence = video.stem.startswith("v") or "violence" in video.stem.lower()
        label = "violence" if is_violence else "normal"
        rows.append({
            "dataset": "xd-violence",
            "relative_path": video.relative_to(root.parent).as_posix(),
            "modality": "video_audio",
            "label_original": label,
            "label_mapped": label,
            "sentinela_domain_label": VIDEO_DOMAIN_MAPPING.get(label, "unknown"),
            "split": "train",  # actual split from annotation file
            "subject_id": "",
            "license_note": "Research use; Wu et al. 2020 (ECCV)",
        })
    return rows


def scan_ucf_crime(root: Path) -> list[dict]:
    """Scan UCF-Crime: Anomaly-Detection-Dataset structure."""
    rows = []
    if not root.exists():
        return rows

    for split in ["Training", "Testing"]:
        split_dir = root / split
        if not split_dir.is_dir():
            # Try alternate names
            split_dir = root / split.lower()
            if not split_dir.is_dir():
                continue
        split_mapped = "train" if "train" in split.lower() else "test"

        for category_dir in sorted(split_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            for video in sorted(category_dir.glob("*.mp4")):
                sentinela_label = "risk_critical" if category.lower() in ("abuse", "assault", "fighting") else "anomaly_generic"
                rows.append({
                    "dataset": "ucf-crime",
                    "relative_path": video.relative_to(root.parent).as_posix(),
                    "modality": "video",
                    "label_original": category,
                    "label_mapped": category.lower(),
                    "sentinela_domain_label": sentinela_label,
                    "split": split_mapped,
                    "subject_id": "",
                    "license_note": "Research use; UCF (Sultani et al. 2018, CVPR)",
                })
    return rows


def write_manifest(name: str, rows: list[dict]) -> Path:
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    out = MANIFESTS_DIR / f"{name}_manifest.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {out.relative_to(PROJECT_ROOT)} ({len(rows)} entries)")
    return out


def print_download_instructions():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  Video Dataset Download Instructions                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  DAiSEE (Dataset for Affective States in E-Learning):           ║
║    Paper: https://arxiv.org/abs/1609.01885                      ║
║    Access: IIT Delhi (request form)                             ║
║    Place at: archive/DAiSEE/DataSet/                            ║
║    Labels: archive/DAiSEE/Labels/                               ║
║    License: Research use                                         ║
║                                                                  ║
║  XD-Violence (multimodal violence detection):                   ║
║    Paper: https://arxiv.org/abs/2007.04687                      ║
║    GitHub: https://roc-ng.github.io/XD-Violence/                ║
║    Note: Video + audio, good for safety signal training         ║
║    License: Research use (ECCV 2020)                            ║
║                                                                  ║
║  UCF-Crime (anomaly detection):                                 ║
║    URL: https://www.crcv.ucf.edu/projects/                      ║
║         real-world/                                              ║
║    Note: Proxy for anomaly, NOT clinical. Document limitations. ║
║    License: Research use (CVPR 2018)                            ║
║                                                                  ║
║  RAVDESS / CREMA-D (audio-visual emotion):                      ║
║    Also usable for video emotion — see prepare_audio_datasets   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description="Prepare video datasets for Sentinela")
    parser.add_argument("--daisee", type=Path, default=PROJECT_ROOT / "archive" / "DAiSEE" / "DataSet")
    parser.add_argument("--xdviolence", type=Path, default=PROJECT_ROOT / "data" / "external" / "xd-violence")
    parser.add_argument("--ucf-crime", type=Path, default=PROJECT_ROOT / "data" / "external" / "ucf-crime")
    args = parser.parse_args()

    print("=" * 60)
    print("Sentinela AI — Video Dataset Preparation")
    print("=" * 60)

    all_rows = []

    # DAiSEE
    print(f"\nScanning DAiSEE at: {args.daisee}")
    daisee_rows = scan_daisee(args.daisee)
    if daisee_rows:
        write_manifest("daisee_video", daisee_rows)
        all_rows.extend(daisee_rows)
    else:
        print(f"  [NOT FOUND] Place DAiSEE videos at: {args.daisee}/")

    # XD-Violence
    print(f"\nScanning XD-Violence at: {args.xdviolence}")
    xd_rows = scan_xd_violence(args.xdviolence)
    if xd_rows:
        write_manifest("xdviolence_video", xd_rows)
        all_rows.extend(xd_rows)
    else:
        print(f"  [NOT FOUND] Place XD-Violence at: {args.xdviolence}/")

    # UCF-Crime
    ucf_path = getattr(args, "ucf_crime", PROJECT_ROOT / "data" / "external" / "ucf-crime")
    print(f"\nScanning UCF-Crime at: {ucf_path}")
    ucf_rows = scan_ucf_crime(ucf_path)
    if ucf_rows:
        write_manifest("ucf_crime_video", ucf_rows)
        all_rows.extend(ucf_rows)
    else:
        print(f"  [NOT FOUND] Place UCF-Crime at: {ucf_path}/")

    # Combined
    if all_rows:
        write_manifest("video_combined", all_rows)
        print(f"\n  Total video entries: {len(all_rows)}")
    else:
        print("\nNo video datasets found locally.")
        print_download_instructions()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
