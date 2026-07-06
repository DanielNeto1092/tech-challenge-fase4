"""Clinical signals extractor for obstetric/maternal health risk assessment.

Processes structured clinical data (Cardiotocography, Maternal Health Risk)
and produces a ModalityScore compatible with Sentinela's fusion engine.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.domain.labels import CTG_NSP_MAP, CTG_RISK_LEVEL_MAP, MATERNAL_RISK_MAP, MATERNAL_RISK_LEVEL_MAP
from src.domain.types import ModalityScore, clamp01

logger = logging.getLogger("sentinela.extractors.clinical")


@dataclass
class ClinicalInput:
    """Structured clinical input for risk scoring."""
    # Maternal Health Risk fields
    age: float | None = None
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    blood_sugar: float | None = None
    body_temp: float | None = None
    heart_rate: float | None = None
    # CTG fields
    baseline_fhr: float | None = None  # LB - baseline fetal heart rate
    accelerations: float | None = None  # AC
    fetal_movement: float | None = None  # FM
    uterine_contractions: float | None = None  # UC
    decelerations_light: float | None = None  # DL
    decelerations_severe: float | None = None  # DS
    nsp_class: int | None = None  # 1=Normal, 2=Suspect, 3=Pathological
    # Direct risk label (if known)
    risk_label: str | None = None  # "low risk", "mid risk", "high risk"
    # Source
    source: str = "unknown"


class ClinicalExtractor:
    """Score clinical/obstetric data for the Sentinela pipeline.

    Uses rule-based scoring aligned with medical guidelines:
    - Maternal: WHO risk thresholds for BP, blood sugar, temperature
    - CTG: NSP classification (Normal/Suspect/Pathological)

    When a pre-classified risk_label or nsp_class is provided, uses that directly.
    Otherwise applies threshold-based rules on vital signs.
    """

    # Maternal health risk thresholds (WHO guidelines)
    _BP_HIGH = 140  # systolic
    _BP_ELEVATED = 130
    _BS_HIGH = 11.0  # mmol/L fasting
    _BS_ELEVATED = 7.8
    _TEMP_HIGH = 100.4  # Fahrenheit
    _HR_HIGH = 100
    _HR_LOW = 60

    def score(self, clinical: ClinicalInput) -> ModalityScore:
        """Produce a clinical ModalityScore from structured health data."""
        evidence: dict[str, Any] = {"source": clinical.source, "available": True}
        signals: list[str] = []

        # --- CTG path ---
        if clinical.nsp_class is not None:
            nsp = int(clinical.nsp_class)
            sentinela_label = CTG_NSP_MAP.get(nsp, "normal_or_low_risk")
            risk_level = CTG_RISK_LEVEL_MAP.get(nsp, "ROTINA")
            # Map to score: Normal=0.1, Suspect=0.55, Pathological=0.85
            score_map = {1: 0.10, 2: 0.55, 3: 0.85}
            score = score_map.get(nsp, 0.1)
            confidence = 0.90  # CTG classification is reliable
            evidence.update({
                "method": "CTG_NSP",
                "nsp_class": nsp,
                "sentinela_label": sentinela_label,
                "risk_level": risk_level,
            })
            if clinical.baseline_fhr is not None:
                evidence["baseline_fhr"] = clinical.baseline_fhr
            if clinical.decelerations_severe and clinical.decelerations_severe > 0:
                signals.append("severe_decelerations")
                score = max(score, 0.80)
            evidence["signals"] = signals
            return ModalityScore(
                modality="clinical",
                score_0_1=clamp01(score),
                confidence_0_1=clamp01(confidence),
                evidence=evidence,
            )

        # --- Maternal Health Risk path (pre-classified) ---
        if clinical.risk_label is not None:
            label = clinical.risk_label.strip().lower()
            sentinela_label = MATERNAL_RISK_MAP.get(label, "normal_or_low_risk")
            risk_level = MATERNAL_RISK_LEVEL_MAP.get(label, "ROTINA")
            score_map = {"low risk": 0.12, "mid risk": 0.52, "high risk": 0.82}
            score = score_map.get(label, 0.12)
            confidence = 0.85
            evidence.update({
                "method": "maternal_risk_label",
                "risk_label": label,
                "sentinela_label": sentinela_label,
                "risk_level": risk_level,
            })
            evidence["signals"] = signals
            return ModalityScore(
                modality="clinical",
                score_0_1=clamp01(score),
                confidence_0_1=clamp01(confidence),
                evidence=evidence,
            )

        # --- Rule-based scoring from vital signs ---
        score = 0.0
        confidence = 0.70  # Lower confidence for rule-based
        risk_factors = 0

        if clinical.systolic_bp is not None:
            if clinical.systolic_bp >= self._BP_HIGH:
                score += 0.30
                signals.append("hypertension")
                risk_factors += 1
            elif clinical.systolic_bp >= self._BP_ELEVATED:
                score += 0.15
                signals.append("elevated_bp")
                risk_factors += 1

        if clinical.blood_sugar is not None:
            if clinical.blood_sugar >= self._BS_HIGH:
                score += 0.25
                signals.append("hyperglycemia")
                risk_factors += 1
            elif clinical.blood_sugar >= self._BS_ELEVATED:
                score += 0.12
                signals.append("elevated_blood_sugar")
                risk_factors += 1

        if clinical.body_temp is not None:
            if clinical.body_temp >= self._TEMP_HIGH:
                score += 0.20
                signals.append("fever")
                risk_factors += 1

        if clinical.heart_rate is not None:
            if clinical.heart_rate >= self._HR_HIGH:
                score += 0.15
                signals.append("tachycardia")
                risk_factors += 1
            elif clinical.heart_rate <= self._HR_LOW:
                score += 0.10
                signals.append("bradycardia")
                risk_factors += 1

        if clinical.age is not None:
            if clinical.age >= 35 or clinical.age <= 17:
                score += 0.10
                signals.append("age_risk_factor")
                risk_factors += 1

        # Confidence increases with more data points
        data_points = sum(1 for v in [
            clinical.systolic_bp, clinical.diastolic_bp, clinical.blood_sugar,
            clinical.body_temp, clinical.heart_rate, clinical.age,
        ] if v is not None)
        confidence = min(0.90, 0.50 + 0.07 * data_points)

        evidence.update({
            "method": "vital_signs_rules",
            "risk_factors": risk_factors,
            "signals": signals,
            "data_points": data_points,
        })

        return ModalityScore(
            modality="clinical",
            score_0_1=clamp01(score),
            confidence_0_1=clamp01(confidence),
            evidence=evidence,
        )

    @classmethod
    def from_maternal_csv_row(cls, row: dict[str, str]) -> ClinicalInput:
        """Create ClinicalInput from a Maternal Health Risk CSV row."""
        return ClinicalInput(
            age=_safe_float(row.get("Age")),
            systolic_bp=_safe_float(row.get("SystolicBP")),
            diastolic_bp=_safe_float(row.get("DiastolicBP")),
            blood_sugar=_safe_float(row.get("BS")),
            body_temp=_safe_float(row.get("BodyTemp")),
            heart_rate=_safe_float(row.get("HeartRate")),
            risk_label=row.get("RiskLevel", "").strip() or None,
            source="Maternal_Health_Risk",
        )

    @classmethod
    def from_ctg_row(cls, row: dict[str, Any]) -> ClinicalInput:
        """Create ClinicalInput from a Cardiotocography row."""
        return ClinicalInput(
            baseline_fhr=_safe_float(row.get("LB")),
            accelerations=_safe_float(row.get("AC")),
            fetal_movement=_safe_float(row.get("FM")),
            uterine_contractions=_safe_float(row.get("UC")),
            decelerations_light=_safe_float(row.get("DL")),
            decelerations_severe=_safe_float(row.get("DS")),
            nsp_class=_safe_int(row.get("NSP")),
            source="Cardiotocography",
        )


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _safe_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None
