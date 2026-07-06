"""Build standardized manifests for all Sentinela AI datasets.

Generates CSV manifests in data/manifests/ with consistent schema:
    file_path, dataset, modality, label_original, label_sentinela, split, source_url, notes
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"
MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

FIELDNAMES = [
    "file_path",
    "dataset",
    "modality",
    "label_original",
    "label_sentinela",
    "split",
    "source_url",
    "notes",
]


def _write_manifest(name: str, rows: list[dict[str, str]]) -> Path:
    out = MANIFESTS_DIR / f"{name}_manifest.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [{name}] {len(rows)} entries -> {out.relative_to(PROJECT_ROOT)}")
    return out


# ---------------------------------------------------------------------------
# 1. RAVDESS
# ---------------------------------------------------------------------------
def build_ravdess_manifest() -> Path:
    """Parse RAVDESS file naming convention into manifest."""
    from src.domain.labels import RAVDESS_CODE_TO_EMOTION, RAVDESS_EMOTION_MAP

    base = PROJECT_ROOT / "The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS)"
    rows: list[dict[str, str]] = []

    # Search both extracted song and speech directories
    for subdir in sorted(base.iterdir()):
        if not subdir.is_dir():
            continue
        for actor_dir in sorted(subdir.iterdir()):
            if not actor_dir.is_dir():
                continue
            for wav in sorted(actor_dir.glob("*.wav")):
                parts = wav.stem.split("-")
                if len(parts) < 7:
                    continue
                emotion_code = parts[2]
                emotion = RAVDESS_CODE_TO_EMOTION.get(emotion_code, "unknown")
                sentinela_label = RAVDESS_EMOTION_MAP.get(emotion, "normal_or_low_risk")
                actor_num = int(parts[6])
                # Split: actors 1-20 train, 21-22 val, 23-24 test
                if actor_num <= 20:
                    split = "train"
                elif actor_num <= 22:
                    split = "val"
                else:
                    split = "test"
                rows.append({
                    "file_path": str(wav.relative_to(PROJECT_ROOT)),
                    "dataset": "RAVDESS",
                    "modality": "audio",
                    "label_original": emotion,
                    "label_sentinela": sentinela_label,
                    "split": split,
                    "source_url": "https://smartlaboratory.org/resources/speech-song-database-ravdess/",
                    "notes": f"intensity={parts[3]}, actor={actor_num}",
                })

    return _write_manifest("ravdess", rows)


# ---------------------------------------------------------------------------
# 2. EATD-Corpus
# ---------------------------------------------------------------------------
def build_eatd_manifest() -> Path:
    """Parse EATD-Corpus folder structure into manifest."""
    from src.domain.labels import eatd_severity_to_sentinela

    base = PROJECT_ROOT / "EATD-Corpus - Automatic Depression Detection" / "EATD-Corpus"
    rows: list[dict[str, str]] = []

    if not base.exists():
        print(f"  [EATD] WARNING: {base} not found")
        return _write_manifest("eatd_corpus", rows)

    for folder in sorted(base.iterdir()):
        if not folder.is_dir():
            continue
        label_file = folder / "new_label.txt"
        if not label_file.exists():
            label_file = folder / "label.txt"
        if not label_file.exists():
            continue

        try:
            sds = float(label_file.read_text(encoding="utf-8").strip())
        except (ValueError, UnicodeDecodeError):
            continue

        sentinela_label = eatd_severity_to_sentinela(sds)
        prefix = folder.name.split("_")[0]  # 't' or 'v'
        modality = "text" if prefix == "t" else "audio"

        # Each folder has positive/neutral/negative wav and txt
        for sentiment in ["positive", "neutral", "negative"]:
            wav = folder / f"{sentiment}.wav"
            txt = folder / f"{sentiment}.txt"
            # Use subject index for split
            try:
                subj_id = int(folder.name.split("_")[1])
            except (IndexError, ValueError):
                subj_id = 0
            split = "train" if subj_id <= 80 else ("val" if subj_id <= 95 else "test")

            if wav.exists():
                rows.append({
                    "file_path": str(wav.relative_to(PROJECT_ROOT)),
                    "dataset": "EATD-Corpus",
                    "modality": "audio",
                    "label_original": f"SDS={sds:.0f}_{sentiment}",
                    "label_sentinela": sentinela_label,
                    "split": split,
                    "source_url": "https://github.com/speechandlanguageprocessing/ICASSP2022-Depression",
                    "notes": f"sentiment={sentiment}, SDS={sds:.1f}",
                })
            if txt.exists():
                rows.append({
                    "file_path": str(txt.relative_to(PROJECT_ROOT)),
                    "dataset": "EATD-Corpus",
                    "modality": "text",
                    "label_original": f"SDS={sds:.0f}_{sentiment}",
                    "label_sentinela": sentinela_label,
                    "split": split,
                    "source_url": "https://github.com/speechandlanguageprocessing/ICASSP2022-Depression",
                    "notes": f"sentiment={sentiment}, SDS={sds:.1f}, lang=Chinese",
                })

    return _write_manifest("eatd_corpus", rows)


# ---------------------------------------------------------------------------
# 3. DAiSEE
# ---------------------------------------------------------------------------
def build_daisee_manifest() -> Path:
    """Parse DAiSEE labels into manifest."""
    base = PROJECT_ROOT / "DAiSEE" / "DAiSEE"
    labels_dir = base / "Labels"
    rows: list[dict[str, str]] = []

    if not labels_dir.exists():
        # Try alternate location
        labels_dir = PROJECT_ROOT / "archive" / "DAiSEE" / "Labels"
    if not labels_dir.exists():
        print(f"  [DAiSEE] WARNING: Labels directory not found")
        return _write_manifest("daisee", rows)

    for label_csv in sorted(labels_dir.glob("*.csv")):
        split_name = label_csv.stem.lower()
        if "train" in split_name:
            split = "train"
        elif "val" in split_name:
            split = "val"
        elif "test" in split_name:
            split = "test"
        else:
            split = "unknown"

        try:
            with open(label_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clip_id = row.get("ClipID", row.get("clipid", ""))
                    boredom = int(row.get("Boredom", row.get("boredom", 0)))
                    engagement = int(row.get("Engagement", row.get("engagement", 0)))
                    confusion = int(row.get("Confusion", row.get("confusion", 0)))
                    frustration = int(row.get("Frustration", row.get("frustration", 0)))

                    # Determine dominant state for Sentinela label
                    if frustration >= 3:
                        sentinela_label = "psychological_distress"
                    elif boredom >= 3 or confusion >= 3:
                        sentinela_label = "visual_discomfort"
                    elif engagement >= 3:
                        sentinela_label = "normal_or_low_risk"
                    else:
                        sentinela_label = "normal_or_low_risk"

                    rows.append({
                        "file_path": clip_id,
                        "dataset": "DAiSEE",
                        "modality": "video",
                        "label_original": f"B={boredom},E={engagement},C={confusion},F={frustration}",
                        "label_sentinela": sentinela_label,
                        "split": split,
                        "source_url": "https://people.iith.ac.in/vineethnb/resources/daisee/",
                        "notes": "",
                    })
        except Exception as e:
            print(f"  [DAiSEE] Error parsing {label_csv}: {e}")

    return _write_manifest("daisee", rows)


# ---------------------------------------------------------------------------
# 4. Maternal Health Risk
# ---------------------------------------------------------------------------
def build_maternal_manifest() -> Path:
    """Parse Maternal Health Risk CSV into manifest."""
    from src.domain.labels import MATERNAL_RISK_MAP

    csv_path = PROJECT_ROOT / "maternal+health+risk" / "Maternal Health Risk Data Set.csv"
    rows: list[dict[str, str]] = []

    if not csv_path.exists():
        print(f"  [Maternal] WARNING: {csv_path} not found")
        return _write_manifest("maternal_health_risk", rows)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    n = len(all_rows)
    for i, row in enumerate(all_rows):
        risk_original = row.get("RiskLevel", "").strip().lower()
        sentinela_label = MATERNAL_RISK_MAP.get(risk_original, "normal_or_low_risk")
        # 70/15/15 split
        if i < int(n * 0.70):
            split = "train"
        elif i < int(n * 0.85):
            split = "val"
        else:
            split = "test"

        rows.append({
            "file_path": f"maternal+health+risk/Maternal Health Risk Data Set.csv:row_{i}",
            "dataset": "Maternal_Health_Risk",
            "modality": "clinical",
            "label_original": risk_original,
            "label_sentinela": sentinela_label,
            "split": split,
            "source_url": "https://archive.ics.uci.edu/dataset/863/maternal+health+risk",
            "notes": f"Age={row.get('Age')}, SBP={row.get('SystolicBP')}, HR={row.get('HeartRate')}",
        })

    return _write_manifest("maternal_health_risk", rows)


# ---------------------------------------------------------------------------
# 5. Cardiotocography (CTG)
# ---------------------------------------------------------------------------
def build_ctg_manifest() -> Path:
    """Parse CTG Excel/CSV into manifest."""
    from src.domain.labels import CTG_NSP_MAP

    xls_path = PROJECT_ROOT / "cardiotocography" / "CTG.xls"
    rows: list[dict[str, str]] = []

    if not xls_path.exists():
        print(f"  [CTG] WARNING: {xls_path} not found")
        return _write_manifest("cardiotocography", rows)

    try:
        import pandas as pd
        # CTG.xls has multiple sheets; data is in 'Raw Data' sheet
        try:
            df = pd.read_excel(xls_path, sheet_name="Raw Data")
        except Exception:
            try:
                df = pd.read_excel(xls_path, sheet_name="Data")
            except Exception:
                df = pd.read_excel(xls_path, sheet_name=0)

        # NSP column: 1=Normal, 2=Suspect, 3=Pathological
        if "NSP" not in df.columns:
            # Try alternate column names
            nsp_col = [c for c in df.columns if "nsp" in c.lower() or "class" in c.lower()]
            if nsp_col:
                df = df.rename(columns={nsp_col[0]: "NSP"})
            else:
                print("  [CTG] WARNING: NSP column not found")
                return _write_manifest("cardiotocography", rows)

        # Drop rows with NaN in NSP
        df = df.dropna(subset=["NSP"])
        n = len(df)
        for i, (_, record) in enumerate(df.iterrows()):
            try:
                nsp = int(float(record["NSP"]))
            except (ValueError, TypeError):
                continue
            sentinela_label = CTG_NSP_MAP.get(nsp, "normal_or_low_risk")
            if i < int(n * 0.70):
                split = "train"
            elif i < int(n * 0.85):
                split = "val"
            else:
                split = "test"

            rows.append({
                "file_path": f"cardiotocography/CTG.xls:row_{i}",
                "dataset": "Cardiotocography",
                "modality": "clinical",
                "label_original": f"NSP={nsp}",
                "label_sentinela": sentinela_label,
                "split": split,
                "source_url": "https://archive.ics.uci.edu/dataset/193/cardiotocography",
                "notes": f"LB={record.get('LB', '')}, AC={record.get('AC', '')}",
            })
    except ImportError:
        print("  [CTG] WARNING: pandas/xlrd not available, skipping CTG")
    except Exception as e:
        print(f"  [CTG] Error: {e}")

    return _write_manifest("cardiotocography", rows)


# ---------------------------------------------------------------------------
# 6. XD-Violence (proxy only)
# ---------------------------------------------------------------------------
def build_xd_violence_manifest() -> Path:
    """Scan XD-Violence example videos into manifest."""
    from src.domain.labels import XD_VIOLENCE_MAP

    base = PROJECT_ROOT / "video" / "xd-violance"
    rows: list[dict[str, str]] = []

    if not base.exists():
        print(f"  [XD-Violence] WARNING: {base} not found")
        return _write_manifest("xd_violence", rows)

    for category_dir in sorted(base.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name.replace("%20", "_").replace(" ", "_").lower()
        sentinela_label = XD_VIOLENCE_MAP.get(category, "safety_anomaly")

        for video in sorted(category_dir.iterdir()):
            if video.suffix.lower() in (".mp4", ".avi", ".mkv", ".webm"):
                rows.append({
                    "file_path": str(video.relative_to(PROJECT_ROOT)),
                    "dataset": "XD-Violence",
                    "modality": "video",
                    "label_original": category,
                    "label_sentinela": sentinela_label,
                    "split": "example",
                    "source_url": "https://roc-ng.github.io/XD-Violence/",
                    "notes": "Proxy only — not clinical data. Used for safety anomaly detection validation.",
                })

    return _write_manifest("xd_violence", rows)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def build_all() -> None:
    print("=" * 60)
    print("Sentinela AI — Building Dataset Manifests")
    print("=" * 60)

    manifests = []
    manifests.append(build_ravdess_manifest())
    manifests.append(build_eatd_manifest())
    manifests.append(build_daisee_manifest())
    manifests.append(build_maternal_manifest())
    manifests.append(build_ctg_manifest())
    manifests.append(build_xd_violence_manifest())

    print("\n" + "=" * 60)
    summary = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "manifests": [str(m.relative_to(PROJECT_ROOT)) for m in manifests],
    }
    summary_path = MANIFESTS_DIR / "manifest_generation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary: {summary_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    build_all()
