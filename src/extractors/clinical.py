"""Clinical signals extractor for obstetric/maternal health risk assessment.

Processes structured clinical data (Cardiotocography, Maternal Health Risk)
and produces a ModalityScore compatible with Sentinela's fusion engine.
"""
from __future__ import annotations

import csv
import logging
import statistics
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
    # Temperature unit. When omitted, values <= 60 are treated as Celsius and
    # higher values as Fahrenheit to support both UI and public dataset inputs.
    body_temp_unit: str | None = None  # "C" or "F"
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
    _TEMP_HIGH_F = 100.4
    _TEMP_HIGH_C = 38.0
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

        body_temp_fever = self._is_fever(clinical.body_temp, clinical.body_temp_unit)
        if clinical.body_temp is not None:
            evidence["body_temp"] = clinical.body_temp
            evidence["body_temp_unit"] = self._temperature_unit(clinical.body_temp, clinical.body_temp_unit)
            if body_temp_fever:
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
            body_temp_unit="F",
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

    @classmethod
    def from_mapping(cls, data: dict[str, Any], source: str = "api_payload") -> ClinicalInput:
        """Create ClinicalInput from API/UI JSON with permissive field aliases."""
        risk_label = data.get("risk_label") or data.get("riskLabel") or data.get("maternal_risk_label")
        nsp_class = data.get("nsp_class", data.get("nspClass", data.get("NSP")))
        return ClinicalInput(
            age=_safe_float(data.get("age") or data.get("Age")),
            systolic_bp=_safe_float(data.get("systolic_bp") or data.get("systolicBP") or data.get("SystolicBP")),
            diastolic_bp=_safe_float(data.get("diastolic_bp") or data.get("diastolicBP") or data.get("DiastolicBP")),
            blood_sugar=_safe_float(data.get("blood_sugar") or data.get("bloodSugar") or data.get("BS")),
            body_temp=_safe_float(data.get("body_temp") or data.get("bodyTemp") or data.get("BodyTemp")),
            body_temp_unit=(data.get("body_temp_unit") or data.get("bodyTempUnit") or data.get("temp_unit") or None),
            heart_rate=_safe_float(data.get("heart_rate") or data.get("heartRate") or data.get("HeartRate")),
            baseline_fhr=_safe_float(data.get("baseline_fhr") or data.get("baselineFhr") or data.get("LB")),
            accelerations=_safe_float(data.get("accelerations") or data.get("AC")),
            fetal_movement=_safe_float(data.get("fetal_movement") or data.get("fetalMovement") or data.get("FM")),
            uterine_contractions=_safe_float(data.get("uterine_contractions") or data.get("uterineContractions") or data.get("UC")),
            decelerations_light=_safe_float(data.get("decelerations_light") or data.get("decelerationsLight") or data.get("DL")),
            decelerations_severe=_safe_float(data.get("decelerations_severe") or data.get("decelerationsSevere") or data.get("DS")),
            nsp_class=_safe_int(nsp_class),
            risk_label=str(risk_label).strip() if risk_label else None,
            source=str(data.get("source") or source),
        )

    @classmethod
    def _temperature_unit(cls, value: float | None, unit: str | None) -> str | None:
        if value is None:
            return None
        normalized = (unit or "").strip().upper()
        if normalized in {"C", "CELSIUS", "°C"}:
            return "C"
        if normalized in {"F", "FAHRENHEIT", "°F"}:
            return "F"
        return "C" if value <= 60 else "F"

    @classmethod
    def _is_fever(cls, value: float | None, unit: str | None) -> bool:
        if value is None:
            return False
        resolved = cls._temperature_unit(value, unit)
        if resolved == "C":
            return value >= cls._TEMP_HIGH_C
        return value >= cls._TEMP_HIGH_F


class ClinicalTimeSeriesAnomalyDetector:
    """Detect anomalies in vital-sign sequences and prescription evolution."""

    _FIELDS = (
        "systolic_bp",
        "diastolic_bp",
        "blood_sugar",
        "body_temp",
        "heart_rate",
        "baseline_fhr",
    )
    _HIGH_ALERT_MEDICATIONS = {
        "insulin",
        "warfarin",
        "misoprostol",
        "oxytocin",
        "magnesium sulfate",
        "sulfato de magnesio",
        "metildopa",
        "methyldopa",
        "nifedipine",
        "nifedipino",
    }

    def score(
        self,
        readings: list[dict[str, Any]] | None = None,
        prescriptions: list[dict[str, Any]] | None = None,
    ) -> ModalityScore:
        readings = readings or []
        prescriptions = prescriptions or []
        vital_anomalies = self._vital_anomalies(readings)
        prescription_anomalies = self._prescription_anomalies(prescriptions)

        max_vital = max((float(a["severity"]) for a in vital_anomalies), default=0.0)
        max_prescription = max((float(a["severity"]) for a in prescription_anomalies), default=0.0)
        score = clamp01(max(max_vital, max_prescription))
        confidence = 0.0
        if readings:
            confidence = max(confidence, min(0.9, 0.35 + 0.08 * len(readings)))
        if prescriptions:
            confidence = max(confidence, min(0.85, 0.40 + 0.08 * len(prescriptions)))

        return ModalityScore(
            modality="clinical",
            score_0_1=round(score, 3),
            confidence_0_1=round(confidence, 3),
            evidence={
                "method": "temporal_vital_signs_and_prescriptions",
                "available": bool(readings or prescriptions),
                "readings_count": len(readings),
                "prescriptions_count": len(prescriptions),
                "vital_anomalies": vital_anomalies,
                "prescription_anomalies": prescription_anomalies,
                "signals": [a["type"] for a in vital_anomalies + prescription_anomalies],
            },
        )

    def _vital_anomalies(self, readings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(readings) < 3:
            return []
        anomalies: list[dict[str, Any]] = []
        rows = sorted(readings, key=lambda r: str(r.get("timestamp") or r.get("time") or ""))
        for idx in range(2, len(rows)):
            baseline_rows = rows[max(0, idx - 5):idx]
            current = rows[idx]
            for field in self._FIELDS:
                value = _safe_float(current.get(field) or current.get(_camel(field)))
                baseline = [_safe_float(r.get(field) or r.get(_camel(field))) for r in baseline_rows]
                baseline = [v for v in baseline if v is not None]
                if value is None or len(baseline) < 2:
                    continue
                mean = statistics.fmean(baseline)
                stdev = statistics.pstdev(baseline) or 1.0
                z = (value - mean) / stdev
                absolute = self._absolute_vital_severity(field, value)
                z_severity = min(1.0, abs(z) / 4.0) if abs(z) >= 2.0 else 0.0
                severity = max(absolute, z_severity)
                if severity >= 0.45:
                    anomalies.append({
                        "type": "vital_sign_time_series_anomaly",
                        "field": field,
                        "value": value,
                        "baseline_mean": round(mean, 3),
                        "z_score": round(z, 3),
                        "severity": round(severity, 3),
                        "timestamp": current.get("timestamp") or current.get("time") or idx,
                    })
        return anomalies

    def _absolute_vital_severity(self, field: str, value: float) -> float:
        if field == "systolic_bp" and value >= 140:
            return min(1.0, 0.65 + (value - 140) / 80)
        if field == "diastolic_bp" and value >= 90:
            return min(1.0, 0.55 + (value - 90) / 60)
        if field == "blood_sugar" and value >= 11.0:
            return min(1.0, 0.60 + (value - 11.0) / 15)
        if field == "heart_rate" and (value >= 120 or value <= 50):
            return 0.55
        if field == "body_temp" and (value >= 38.0 or value >= 100.4):
            return 0.50
        if field == "baseline_fhr" and (value < 110 or value > 160):
            return 0.60
        return 0.0

    def _prescription_anomalies(self, prescriptions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not prescriptions:
            return []
        anomalies: list[dict[str, Any]] = []
        previous_by_med: dict[str, dict[str, Any]] = {}
        rows = sorted(prescriptions, key=lambda r: str(r.get("timestamp") or r.get("date") or ""))
        for idx, row in enumerate(rows):
            med = str(row.get("medication") or row.get("drug") or row.get("name") or "").strip().lower()
            action = str(row.get("action") or row.get("status") or "active").strip().lower()
            dose = _safe_float(row.get("dose") or row.get("dose_mg") or row.get("doseMg"))
            if not med:
                continue
            high_alert = any(item in med for item in self._HIGH_ALERT_MEDICATIONS)
            prev = previous_by_med.get(med)
            if high_alert and action in {"new", "started", "inicio", "iniciado"}:
                anomalies.append({
                    "type": "prescription_high_alert_started",
                    "medication": med,
                    "action": action,
                    "severity": 0.65,
                    "timestamp": row.get("timestamp") or row.get("date") or idx,
                })
            if prev and dose is not None:
                prev_dose = _safe_float(prev.get("dose") or prev.get("dose_mg") or prev.get("doseMg"))
                if prev_dose and abs(dose - prev_dose) / max(prev_dose, 1e-6) >= 0.5:
                    anomalies.append({
                        "type": "prescription_dose_shift",
                        "medication": med,
                        "previous_dose": prev_dose,
                        "current_dose": dose,
                        "severity": 0.55 if not high_alert else 0.75,
                        "timestamp": row.get("timestamp") or row.get("date") or idx,
                    })
            if high_alert and action in {"stopped", "suspended", "suspenso", "interrompido"}:
                anomalies.append({
                    "type": "prescription_high_alert_stopped",
                    "medication": med,
                    "action": action,
                    "severity": 0.60,
                    "timestamp": row.get("timestamp") or row.get("date") or idx,
                })
            previous_by_med[med] = row
        return anomalies


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


def _camel(snake: str) -> str:
    head, *tail = snake.split("_")
    return head + "".join(part.capitalize() for part in tail)
