from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


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

RAVDESS_MODALITIES = {
    "01": "audio_video",
    "02": "video_only",
    "03": "audio_only",
}

RAVDESS_VOCAL_CHANNELS = {
    "01": "speech",
    "02": "song",
}

RAVDESS_INTENSITIES = {
    "01": "normal",
    "02": "strong",
}

CREMAD_EMOTIONS = {
    "ANG": "angry",
    "DIS": "disgust",
    "FEA": "fearful",
    "HAP": "happy",
    "NEU": "neutral",
    "SAD": "sad",
}

CREMAD_INTENSITIES = {
    "LO": "low",
    "MD": "medium",
    "HI": "high",
    "XX": "unspecified",
}


def _actor_from_parent(path: Path) -> str:
    return path.parent.name.replace("Actor_", "")


def _split_for_actor(dataset: str, actor_folder: str) -> str:
    key = f"{dataset}:{actor_folder}".encode("utf-8")
    bucket = int(hashlib.sha1(key).hexdigest()[:8], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"


def parse_ravdess(path: Path, root: Path) -> dict | None:
    stem = path.stem
    parts = stem.split("-")
    if len(parts) != 7:
        return None

    modality, vocal_channel, emotion, intensity, statement, repetition, actor = parts
    actor_id = int(actor)
    return {
        "dataset": "ravdess",
        "path": path.as_posix(),
        "relative_path": path.relative_to(root).as_posix(),
        "file_name": path.name,
        "actor_id": actor_id,
        "actor_folder": path.parent.name,
        "split": _split_for_actor("ravdess", path.parent.name),
        "inferred_gender": "female" if actor_id % 2 == 0 else "male",
        "emotion_code": emotion,
        "emotion": RAVDESS_EMOTIONS.get(emotion, "unknown"),
        "modality": RAVDESS_MODALITIES.get(modality, "unknown"),
        "vocal_channel": RAVDESS_VOCAL_CHANNELS.get(vocal_channel, "unknown"),
        "intensity": RAVDESS_INTENSITIES.get(intensity, "unknown"),
        "statement": statement,
        "repetition": repetition,
        "size_bytes": path.stat().st_size,
    }


def parse_cremad(path: Path, root: Path) -> dict | None:
    stem = path.stem
    parts = stem.split("_")
    if len(parts) != 5:
        return None

    actor, sentence, emotion, intensity, take = parts
    actor_folder = _actor_from_parent(path)
    return {
        "dataset": "crema-d",
        "path": path.as_posix(),
        "relative_path": path.relative_to(root).as_posix(),
        "file_name": path.name,
        "actor_id": int(actor) if actor.isdigit() else actor_folder,
        "actor_folder": path.parent.name,
        "split": _split_for_actor("crema-d", path.parent.name),
        "inferred_gender": "unknown",
        "emotion_code": emotion,
        "emotion": CREMAD_EMOTIONS.get(emotion, "unknown"),
        "modality": "audio_video",
        "vocal_channel": "speech",
        "intensity": CREMAD_INTENSITIES.get(intensity, "unknown"),
        "statement": sentence,
        "repetition": take,
        "size_bytes": path.stat().st_size,
    }


def build_manifest(github_dir: Path) -> tuple[list[dict], dict]:
    rows: list[dict] = []

    ravdess_dir = github_dir / "ravdess"
    if ravdess_dir.exists():
        for path in sorted(ravdess_dir.rglob("*.mp4")):
            row = parse_ravdess(path, github_dir)
            if row is not None:
                rows.append(row)

    cremad_dir = github_dir / "crema-d"
    if cremad_dir.exists():
        for path in sorted(cremad_dir.rglob("*.mp4")):
            row = parse_cremad(path, github_dir)
            if row is not None:
                rows.append(row)

    by_dataset = Counter(row["dataset"] for row in rows)
    by_emotion = Counter(row["emotion"] for row in rows)
    by_split = Counter(row["split"] for row in rows)
    by_dataset_emotion: dict[str, dict[str, int]] = defaultdict(dict)
    for dataset in sorted(by_dataset):
        counts = Counter(row["emotion"] for row in rows if row["dataset"] == dataset)
        by_dataset_emotion[dataset] = dict(sorted(counts.items()))

    female_rows = [row for row in rows if row.get("inferred_gender") == "female"]
    summary = {
        "total_files": len(rows),
        "by_dataset": dict(sorted(by_dataset.items())),
        "by_split": dict(sorted(by_split.items())),
        "by_emotion": dict(sorted(by_emotion.items())),
        "by_dataset_emotion": dict(by_dataset_emotion),
        "ravdess_female_files": len(female_rows),
        "notes": [
            "RAVDESS gender is inferred from the official actor id convention: odd=male, even=female.",
            "CREMA-D gender is left unknown because this folder does not include demographic metadata.",
        ],
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a CSV manifest for local RAVDESS/CREMA-D videos.")
    parser.add_argument("--github-dir", default="github", help="Path containing ravdess/ and crema-d/")
    parser.add_argument("--out", default="data/manifests/emotion_video_manifest.csv")
    parser.add_argument("--summary-out", default="data/manifests/emotion_video_summary.json")
    args = parser.parse_args()

    github_dir = Path(args.github_dir)
    if not github_dir.exists():
        raise SystemExit(f"ERROR: github-dir not found: {github_dir}")

    rows, summary = build_manifest(github_dir)
    if not rows:
        raise SystemExit("ERROR: no videos found for manifest")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
