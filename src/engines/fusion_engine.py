from __future__ import annotations

from dataclasses import asdict
from typing import Any

from src.config import FusionWeights, Thresholds
from src.domain.types import ModalityScore, RiskReport, clamp01


class FusionEngine:
    """Late fusion ponderada com 5 modalidades: video, audio, text, objects, clinical.

    Regras de negócio:
    - Pesos normalizados apenas sobre modalidades presentes.
    - Coverage penalty reduz score quando há poucas modalidades.
    - Level 'critical' se video+audio ambos >= critical_threshold.
    - Objetos cortantes elevam diretamente o score de risco se detectados.
    - Clinical data (obstetric/fetal) contribui diretamente ao risco.
    """

    def __init__(self, weights: FusionWeights | None = None, thresholds: Thresholds | None = None):
        self._w = weights or FusionWeights()
        self._t = thresholds or Thresholds()

    def fuse(
        self,
        *,
        video: ModalityScore | None = None,
        audio: ModalityScore | None = None,
        text: ModalityScore | None = None,
        objects: ModalityScore | None = None,
        clinical: ModalityScore | None = None,
    ) -> RiskReport:
        present: dict[str, ModalityScore] = {}
        unavailable: dict[str, str] = {}

        def add_if_available(name: str, score: ModalityScore | None) -> None:
            if score is None:
                return
            evidence = score.evidence or {}
            if evidence.get("available") is False:
                unavailable[name] = str(evidence.get("reason") or "unavailable")
                return
            present[name] = score

        add_if_available("video", video)
        add_if_available("audio", audio)
        add_if_available("text", text)
        add_if_available("objects", objects)
        add_if_available("clinical", clinical)

        base = {
            "video": self._w.video,
            "audio": self._w.audio,
            "text": self._w.text,
            "objects": self._w.objects,
            "clinical": self._w.clinical,
        }

        # Pesos raw = base * confiança da modalidade
        raw_weights = {k: base[k] * clamp01(present[k].confidence_0_1) if k in present else 0.0 for k in base}
        total_w = sum(raw_weights.values())
        norm_weights = {k: (v / total_w if total_w > 0 else 0.0) for k, v in raw_weights.items()}

        s_mm = sum(norm_weights[k] * clamp01(present[k].score_0_1) for k in present)
        s_mm *= self._coverage_penalty(len(present))
        s_mm = clamp01(s_mm)

        # Determinar nível
        level = "low"
        if s_mm >= self._t.alert:
            level = "high"
        elif s_mm >= 0.40:
            level = "medium"

        if (video and audio and clamp01(video.score_0_1) >= self._t.critical and clamp01(audio.score_0_1) >= self._t.critical):
            level = "critical"

        # Objetos cortantes podem escalar para critical independentemente
        if objects and clamp01(objects.score_0_1) >= 0.85:
            level = "critical"

        # Clinical data >= 0.80 escalates to critical (pathological CTG / high maternal risk)
        if clinical and clamp01(clinical.score_0_1) >= 0.80:
            level = "critical"

        if "objects" in unavailable and level == "low":
            level = "medium"

        reasons = [f"{k}={clamp01(ms.score_0_1):.3f}" for k, ms in present.items()]
        missing = [k for k in base if k not in present]
        if unavailable:
            reasons.extend([f"{k}=unavailable" for k in unavailable])

        return RiskReport(
            multimodal_score_0_1=round(s_mm, 3),
            level=level,
            weights=norm_weights,
            modality_scores=present,
            reasons=reasons,
            metadata={
                "base_weights": base,
                "raw_weights": raw_weights,
                "missing": missing,
                "unavailable": unavailable,
                "coverage_penalty": self._coverage_penalty(len(present)),
            },
        )

    def to_dict(self, report: RiskReport) -> dict[str, Any]:
        d = asdict(report)
        d["modality_scores"] = {k: asdict(v) for k, v in report.modality_scores.items()}
        return d

    @staticmethod
    def _coverage_penalty(n: int) -> float:
        return {0: 0.0, 1: 0.88, 2: 0.94, 3: 0.97, 4: 0.99}.get(n, 1.0)



