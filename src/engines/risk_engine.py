from __future__ import annotations

from typing import Any

from src.domain.types import RiskReport


class RiskEngine:
    """Deterministic priority triage from fused multimodal report."""

    def prioritize(self, report: RiskReport) -> dict[str, Any]:
        score = max(0.0, min(1.0, report.multimodal_score_0_1))
        risk_level = "URGENTE" if score >= 0.70 else "MONITORAR" if score >= 0.40 else "ROTINA"
        unavailable = report.metadata.get("unavailable") or {}
        objects_unavailable = "objects" in unavailable
        object_score = max(0.0, min(1.0, report.modality_scores.get("objects").score_0_1)) if "objects" in report.modality_scores else 0.0
        sharp_object_detected = object_score > 0.0

        if objects_unavailable and risk_level == "ROTINA":
            risk_level = "MONITORAR"
        if sharp_object_detected and risk_level == "ROTINA":
            risk_level = "MONITORAR"

        boundaries = [0.40, 0.70]
        confidence = max(0.0, min(1.0, 0.45 + min(abs(score - b) for b in boundaries) / 0.30))
        if objects_unavailable:
            confidence = min(confidence, 0.45)

        vals = [max(0.0, min(1.0, ms.score_0_1)) for ms in report.modality_scores.values()]
        disagreement = (max(vals) - min(vals)) if len(vals) >= 2 else 0.0

        human_review = (
            risk_level == "URGENTE"
            or (risk_level == "MONITORAR" and confidence < 0.75)
            or confidence < 0.55
            or disagreement >= 0.55
            or objects_unavailable
            or sharp_object_detected
        )

        flags: list[str] = []
        if confidence < 0.55:
            flags.append("low_confidence")
        if disagreement >= 0.55:
            flags.append("modality_disagreement")
        if risk_level == "URGENTE":
            flags.append("urgent_priority")
        if sharp_object_detected:
            flags.append("sharp_object_detected")
        if objects_unavailable:
            flags.append("object_detection_unavailable")

        return {
            "riskLevel": risk_level,
            "confidence": round(confidence, 3),
            "humanReviewRequired": human_review,
            "topSignals": sorted(
                [{"label": k, "score": round(ms.score_0_1, 3)} for k, ms in report.modality_scores.items()],
                key=lambda x: x["score"],
                reverse=True,
            ),
            "anomalyFlags": flags,
        }
