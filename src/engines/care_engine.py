from __future__ import annotations

from typing import Any

from src.domain.types import RiskReport, clamp01



def _ms(report: RiskReport, name: str) -> float:
    item = report.modality_scores.get(name)
    return clamp01(item.score_0_1) if item else 0.0


def _conf(report: RiskReport, name: str) -> float:
    item = report.modality_scores.get(name)
    return clamp01(item.confidence_0_1) if item else 0.0


def _label_score(report: RiskReport, label: str) -> float:
    item = report.modality_scores.get("text")
    if item is None:
        return 0.0
    labels = (item.evidence or {}).get("labels", {})
    return clamp01(float((labels.get(label) or {}).get("score", 0.0)))


class CareEngine:
    """Trauma-informed care assessment layer."""

    def assess(self, report: RiskReport) -> dict[str, Any]:
        audio = _ms(report, "audio")
        text = _ms(report, "text")
        video = _ms(report, "video")
        objects = _ms(report, "objects")
        clinical = _ms(report, "clinical")
        text_safety = _label_score(report, "safety_concern")
        text_control = _label_score(report, "control_or_coercion")
        text_hopelessness = _label_score(report, "hopelessness")

        # Emotion distress from audio baseline (sad+fearful+angry)
        audio_item = report.modality_scores.get("audio")
        emo = ((audio_item.evidence or {}).get("emotion_baseline", {}) or {}).get("probabilities", {}) if audio_item else {}
        audio_emotion_distress = clamp01(0.45 * float(emo.get("sad", 0)) + 0.35 * float(emo.get("fearful", 0)) + 0.20 * float(emo.get("angry", 0)))

        present = list(report.modality_scores.keys())
        data_quality = sum(_conf(report, n) for n in present) / max(1, len(present))

        safety_signal = clamp01(0.25 * text + 0.25 * text_safety + 0.15 * text_control + 0.10 * text_hopelessness + 0.10 * video + 0.15 * objects)
        affective_distress = clamp01(0.35 * audio + 0.15 * audio_emotion_distress + 0.20 * text + 0.10 * video + 0.10 * text_hopelessness + 0.10 * objects)
        nonverbal_alert = clamp01(0.55 * video + 0.30 * audio + 0.15 * objects)
        obstetric_risk = clamp01(clinical)  # Direct clinical signal
        uncertainty = clamp01(1.0 - data_quality)
        wellbeing = clamp01(1.0 - (0.40 * affective_distress + 0.30 * safety_signal + 0.15 * objects + 0.15 * obstetric_risk))

        fusion_score = clamp01(report.multimodal_score_0_1)
        if safety_signal >= 0.72 or fusion_score >= 0.78 or objects >= 0.85 or clinical >= 0.80:
            pathway = "revisao_prioritaria"
        elif objects > 0 or affective_distress >= 0.55 or safety_signal >= 0.45 or fusion_score >= 0.70 or clinical >= 0.50:
            pathway = "acolhimento_e_monitoramento"
        elif uncertainty >= 0.55:
            pathway = "coleta_adicional"
        else:
            pathway = "acompanhamento_rotina"

        review_focus: list[str] = []
        if safety_signal >= 0.45:
            review_focus.append("conversar sobre seguranca percebida")
        if affective_distress >= 0.55:
            review_focus.append("avaliar sofrimento psicologico e rede de apoio")
        if nonverbal_alert >= 0.55:
            review_focus.append("revisar sinais nao verbais")
        if objects >= 0.3:
            review_focus.append("verificar presenca de objetos cortantes no ambiente")
        if clinical >= 0.50:
            review_focus.append("avaliar risco obstetrico e encaminhar equipe clinica")
        if not review_focus:
            review_focus.append("manter acompanhamento e observar mudancas")

        return {
            "carePathway": pathway,
            "dimensions": {
                "wellbeingIndex": round(wellbeing, 3),
                "affectiveDistress": round(affective_distress, 3),
                "audioEmotionDistress": round(audio_emotion_distress, 3),
                "safetySignal": round(safety_signal, 3),
                "nonverbalAlert": round(nonverbal_alert, 3),
                "objectThreat": round(objects, 3),
                "obstetricRisk": round(obstetric_risk, 3),
                "dataQuality": round(data_quality, 3),
                "uncertainty": round(uncertainty, 3),
            },
            "availableModalities": present,
            "reviewFocus": review_focus,
            "guardrails": [
                "nao diagnosticar violencia domestica automaticamente",
                "priorizar revisao humana",
                "considerar falso positivo e contexto",
                "dados clinicos nao substituem avaliacao medica presencial",
            ],
        }
