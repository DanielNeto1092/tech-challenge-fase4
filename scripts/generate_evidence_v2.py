"""Generate evidence results for Sentinela AI evaluation.

Produces JSON evidence files in data/results/ demonstrating:
1. Obstetric/clinical risk (Maternal Health Risk data)
2. Obstetric/CTG risk  
3. Psychological text+audio (EATD-Corpus)
4. Multimodal fusion (text + clinical)
5. Sharp objects (if available)
"""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import SentinelaPipeline
from src.extractors.clinical import ClinicalExtractor, ClinicalInput


def _save(name: str, report: dict) -> None:
    out = RESULTS_DIR / f"{name}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    score = report.get("multimodal_score_0_1", "?")
    level = report.get("level", "?")
    priority = report.get("priority", {}).get("riskLevel", "?")
    care = report.get("care_assessment", {}).get("carePathway", "?")
    print(f"  -> {out.name}: score={score}, level={level}, priority={priority}, care={care}")


def evidence_maternal_high_risk():
    """Run pipeline with high-risk maternal health data."""
    print("\n=== Evidence: Maternal Health — High Risk ===")
    clinical = ClinicalInput(
        age=35,
        systolic_bp=140,
        diastolic_bp=90,
        blood_sugar=13.0,
        body_temp=98,
        heart_rate=70,
        risk_label="high risk",
        source="Maternal_Health_Risk",
    )
    pipe = SentinelaPipeline()
    report = pipe.analyze(clinical_data=clinical)
    _save("evidence_maternal_high_risk", report)


def evidence_maternal_low_risk():
    """Run pipeline with low-risk maternal health data."""
    print("\n=== Evidence: Maternal Health — Low Risk ===")
    clinical = ClinicalInput(
        age=25,
        systolic_bp=120,
        diastolic_bp=70,
        blood_sugar=6.0,
        body_temp=98,
        heart_rate=76,
        risk_label="low risk",
        source="Maternal_Health_Risk",
    )
    pipe = SentinelaPipeline()
    report = pipe.analyze(clinical_data=clinical)
    _save("evidence_maternal_low_risk", report)


def evidence_ctg_pathological():
    """Run pipeline with pathological CTG data."""
    print("\n=== Evidence: CTG — Pathological (NSP=3) ===")
    clinical = ClinicalInput(
        baseline_fhr=160,
        accelerations=0,
        fetal_movement=0,
        uterine_contractions=5,
        decelerations_light=3,
        decelerations_severe=2,
        nsp_class=3,
        source="Cardiotocography",
    )
    pipe = SentinelaPipeline()
    report = pipe.analyze(clinical_data=clinical)
    _save("evidence_ctg_pathological", report)


def evidence_ctg_normal():
    """Run pipeline with normal CTG data."""
    print("\n=== Evidence: CTG — Normal (NSP=1) ===")
    clinical = ClinicalInput(
        baseline_fhr=132,
        accelerations=6,
        fetal_movement=5,
        uterine_contractions=2,
        decelerations_light=0,
        decelerations_severe=0,
        nsp_class=1,
        source="Cardiotocography",
    )
    pipe = SentinelaPipeline()
    report = pipe.analyze(clinical_data=clinical)
    _save("evidence_ctg_normal", report)


def evidence_text_psychological():
    """Run pipeline with psychological distress text."""
    print("\n=== Evidence: Text — Psychological Distress ===")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(
            "Estou muito cansada de tudo, sinto medo constante e ansiedade. "
            "Nao consigo dormir, tenho insonia e fadiga todos os dias. "
            "Me sinto sozinha e isolada, sem apoio de ninguem."
        )
        f.flush()
        pipe = SentinelaPipeline()
        report = pipe.analyze(transcript=f.name)
    _save("evidence_text_psychological", report)


def evidence_multimodal_text_clinical():
    """Run pipeline with text + clinical data (multimodal fusion)."""
    print("\n=== Evidence: Multimodal — Text + Clinical ===")
    clinical = ClinicalInput(
        age=30,
        systolic_bp=140,
        diastolic_bp=85,
        blood_sugar=7.0,
        body_temp=98,
        heart_rate=70,
        risk_label="mid risk",
        source="Maternal_Health_Risk",
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(
            "Tenho medo de perder o bebe, sinto muita ansiedade e tristeza. "
            "Dor de cabeca constante e falta de ar."
        )
        f.flush()
        pipe = SentinelaPipeline()
        report = pipe.analyze(transcript=f.name, clinical_data=clinical)
    _save("evidence_multimodal_text_clinical", report)


def evidence_eatd_audio():
    """Try to run pipeline on an EATD-Corpus audio file."""
    print("\n=== Evidence: EATD-Corpus Audio ===")
    base = PROJECT_ROOT / "EATD-Corpus - Automatic Depression Detection" / "EATD-Corpus"
    # Find a high-depression subject
    candidates = []
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
        if sds >= 53:  # moderate-to-severe depression
            wav = folder / "negative.wav"
            if wav.exists():
                candidates.append((sds, wav))
    
    if not candidates:
        print("  [SKIP] No high-SDS EATD audio files found.")
        return
    
    # Pick the highest SDS
    candidates.sort(reverse=True)
    sds, wav_path = candidates[0]
    print(f"  Input: {wav_path.name} (SDS={sds})")
    
    pipe = SentinelaPipeline()
    try:
        report = pipe.analyze(audio_wav=str(wav_path))
        _save("evidence_eatd_audio", report)
    except Exception as e:
        print(f"  [ERROR] {e}")


def evidence_object_detection():
    """Run object detection on a test image."""
    print("\n=== Evidence: Object Detection (Roboflow fork) ===")
    test_image = PROJECT_ROOT / "Sharp Objects Detection.yolov8" / "train" / "images" / "fork_00_jpg.rf.ZQtObiTd116CaXJ7v2Oh.jpg"
    if not test_image.exists():
        images_dir = PROJECT_ROOT / "Sharp Objects Detection.yolov8" / "train" / "images"
        fork_images = sorted(images_dir.glob("fork_*"))
        if not fork_images:
            print("  [SKIP] No fork images found.")
            return
        test_image = fork_images[0]
    
    print(f"  Input: {test_image.name}")
    pipe = SentinelaPipeline()
    report = pipe.analyze(image_for_objects=str(test_image))
    _save("evidence_object_fork", report)


def evidence_ravdess_audio():
    """Run pipeline on a RAVDESS audio file (fearful emotion)."""
    print("\n=== Evidence: RAVDESS Audio (fearful) ===")
    base = PROJECT_ROOT / "The Ryerson Audio-Visual Database of Emotional Speech and Song (RAVDESS)"
    # Find a fearful audio file (emotion code = 06)
    target = None
    for subdir in sorted(base.iterdir()):
        if not subdir.is_dir():
            continue
        for actor_dir in sorted(subdir.iterdir()):
            if not actor_dir.is_dir():
                continue
            for wav in sorted(actor_dir.glob("*-06-*-*.wav")):
                target = wav
                break
            if target:
                break
        if target:
            break
    
    if not target:
        print("  [SKIP] No fearful RAVDESS audio found.")
        return
    
    print(f"  Input: {target.name}")
    pipe = SentinelaPipeline()
    try:
        report = pipe.analyze(audio_wav=str(target))
        _save("evidence_ravdess_fearful", report)
    except Exception as e:
        print(f"  [ERROR] {e}")


def main():
    print("=" * 60)
    print("Sentinela AI — Generating Evidence Results")
    print("=" * 60)
    
    evidence_maternal_high_risk()
    evidence_maternal_low_risk()
    evidence_ctg_pathological()
    evidence_ctg_normal()
    evidence_text_psychological()
    evidence_multimodal_text_clinical()
    evidence_eatd_audio()
    evidence_ravdess_audio()
    evidence_object_detection()
    
    print("\n" + "=" * 60)
    print("Evidence generation complete.")
    print(f"Results in: {RESULTS_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
