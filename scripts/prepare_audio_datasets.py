"""Prepare audio emotion datasets (RAVDESS, CREMA-D, IEMOCAP) for Sentinela pipeline.

This script scans local dataset directories, extracts metadata, and generates
standardized manifests in data/manifests/ for training and evaluation.

Usage:
    python -m scripts.prepare_audio_datasets [--ravdess PATH] [--cremad PATH]

If datasets are not yet downloaded, this script prints instructions.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"

# RAVDESS emotion mapping (from filename encoding)
RAVDESS_EMOTIONS = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fearful",
    "07": "disgust",
    "08": "surprised",
}

# CREMA-D emotion mapping (from filename)
CREMAD_EMOTIONS = {
    "ANG": "angry",
    "DIS": "disgust",
    "FEA": "fearful",
    "HAP": "happy",
    "NEU": "neutral",
    "SAD": "sad",
}

# Domain mapping: which emotions are relevant to Sentinela's risk detection
SENTINELA_DOMAIN_MAPPING = {
    "angry": "distress_indicator",
    "fearful": "distress_indicator",
    "sad": "distress_indicator",
    "disgust": "distress_indicator",
    "neutral": "baseline",
    "happy": "baseline",
    "calm": "baseline",
    "surprised": "neutral_context",
}

MANIFEST_COLUMNS = [
    "dataset", "relative_path", "modality", "emotion_original",
    "emotion_mapped", "sentinela_domain_label", "split", "actor_id",
    "license_note",
]


def scan_ravdess(root: Path) -> list[dict]:
    """Scan RAVDESS directory structure: Actor_XX/filename.wav"""
    rows = []
    if not root.exists():
        return rows

    for actor_dir in sorted(root.iterdir()):
        if not actor_dir.is_dir() or not actor_dir.name.startswith("Actor_"):
            continue
        actor_id = actor_dir.name.replace("Actor_", "")
        for f in sorted(actor_dir.glob("*.wav")):
            # RAVDESS filename: MM-VV-EE-EI-SS-RR-AA.wav
            parts = f.stem.split("-")
            if len(parts) < 7:
                continue
            emotion_code = parts[2]
            emotion = RAVDESS_EMOTIONS.get(emotion_code, "unknown")
            # Split by actor: actors 1-20 train, 21-24 test
            split = "test" if int(actor_id) > 20 else "train"
            rows.append({
                "dataset": "ravdess",
                "relative_path": f.relative_to(root.parent).as_posix(),
                "modality": "audio",
                "emotion_original": emotion,
                "emotion_mapped": emotion,
                "sentinela_domain_label": SENTINELA_DOMAIN_MAPPING.get(emotion, "unknown"),
                "split": split,
                "actor_id": actor_id,
                "license_note": "CC BY-NC-SA 4.0; academic use",
            })
    return rows


def scan_cremad(root: Path) -> list[dict]:
    """Scan CREMA-D: flat directory of WAV/MP4 files."""
    rows = []
    if not root.exists():
        return rows

    for f in sorted(root.glob("*.wav")):
        # CREMA-D filename: ACTOR_SENTENCE_EMOTION_INTENSITY.wav
        parts = f.stem.split("_")
        if len(parts) < 4:
            continue
        actor_id = parts[0]
        emotion_code = parts[2]
        emotion = CREMAD_EMOTIONS.get(emotion_code, "unknown")
        # Split by actor hash
        split = "test" if int(actor_id) % 5 == 0 else "train"
        rows.append({
            "dataset": "crema-d",
            "relative_path": f.relative_to(root.parent).as_posix(),
            "modality": "audio",
            "emotion_original": emotion_code,
            "emotion_mapped": emotion,
            "sentinela_domain_label": SENTINELA_DOMAIN_MAPPING.get(emotion, "unknown"),
            "split": split,
            "actor_id": actor_id,
            "license_note": "Open access; academic use (Cao et al. 2014)",
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
║  Audio Dataset Download Instructions                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  RAVDESS (Ryerson Audio-Visual Database):                       ║
║    URL: https://zenodo.org/record/1188976                       ║
║    Place at: github/ravdess/                                    ║
║    Structure: Actor_XX/*.wav                                    ║
║    License: CC BY-NC-SA 4.0                                     ║
║                                                                  ║
║  CREMA-D (Crowd-sourced Emotional Multimodal Actors):           ║
║    URL: https://github.com/ChesapeakeComputerScience/CREMA-D   ║
║    Place at: github/crema-d/                                    ║
║    Structure: *.wav (flat)                                      ║
║    License: Open access                                          ║
║                                                                  ║
║  IEMOCAP (requires USC license):                                ║
║    URL: https://sail.usc.edu/iemocap/                           ║
║    Requires: formal access request                              ║
║    Note: ~12h audio-visual, excellent for multimodal            ║
║                                                                  ║
║  MSP-Podcast (requires UT Dallas license):                      ║
║    URL: https://ecs.utdallas.edu/research/researchlabs/         ║
║         msp-lab/MSP-Podcast.html                                ║
║    Note: Large naturalistic dataset for robustness              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description="Prepare audio datasets for Sentinela")
    parser.add_argument("--ravdess", type=Path, default=PROJECT_ROOT / "github" / "ravdess")
    parser.add_argument("--cremad", type=Path, default=PROJECT_ROOT / "github" / "crema-d")
    args = parser.parse_args()

    print("=" * 60)
    print("Sentinela AI — Audio Dataset Preparation")
    print("=" * 60)

    all_rows = []

    # RAVDESS
    print(f"\nScanning RAVDESS at: {args.ravdess}")
    ravdess_rows = scan_ravdess(args.ravdess)
    if ravdess_rows:
        write_manifest("ravdess_audio", ravdess_rows)
        all_rows.extend(ravdess_rows)
    else:
        print(f"  [NOT FOUND] Place RAVDESS audio at: {args.ravdess}/")

    # CREMA-D
    print(f"\nScanning CREMA-D at: {args.cremad}")
    cremad_rows = scan_cremad(args.cremad)
    if cremad_rows:
        write_manifest("cremad_audio", cremad_rows)
        all_rows.extend(cremad_rows)
    else:
        print(f"  [NOT FOUND] Place CREMA-D audio at: {args.cremad}/")

    # Combined manifest
    if all_rows:
        write_manifest("audio_combined", all_rows)
        print(f"\n  Total audio entries: {len(all_rows)}")
        # Stats
        by_dataset = {}
        for r in all_rows:
            by_dataset.setdefault(r["dataset"], 0)
            by_dataset[r["dataset"]] += 1
        for ds, count in by_dataset.items():
            print(f"    {ds}: {count}")
    else:
        print("\nNo datasets found locally.")
        print_download_instructions()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
