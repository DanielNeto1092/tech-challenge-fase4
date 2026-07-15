from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.domain.types import ModalityScore


SIGNAL_LEXICON: dict[str, dict[str, Any]] = {
    "safety_concern": {"weight": 1.0, "terms": ["agressao", "ameaca", "machucou", "medo", "perigo", "violencia", "trancar", "prender", "bater", "empurrar"]},
    "control_or_coercion": {"weight": 0.85, "terms": ["controle", "controla", "proibir", "impedir", "obrigar", "vigiar", "celular", "senha", "ciumes", "mandar"]},
    "isolation": {"weight": 0.75, "terms": ["sozinha", "isolada", "isolamento", "afastar", "familia", "amigos", "ninguem", "sem apoio"]},
    "hopelessness": {"weight": 0.85, "terms": ["desesperanca", "sem saida", "nao aguento", "cansada de tudo", "sumir", "desistir", "vazio"]},
    "physical_symptom": {"weight": 0.60, "terms": ["dor", "cabeca", "peito", "falta de ar", "enjoo", "tremor", "insonia", "cansaco", "fadiga"]},
    "psychological_distress": {"weight": 0.90, "terms": ["ansiedade", "tristeza", "panico", "choro", "angustia", "nervosa", "culpa", "vergonha", "medo"]},
    "support_network_absent": {"weight": 0.65, "terms": ["sem apoio", "nao tenho com quem falar", "ninguem acredita", "nao posso contar", "sem familia", "sem amigos"]},
    "postpartum_depression": {"weight": 0.90, "terms": ["pos-parto", "puerperio", "baby blues", "depressao pos-parto", "nao consigo cuidar", "rejeicao ao bebe", "sem vinculo", "culpa com o bebe"]},
    "gestational_anxiety": {"weight": 0.80, "terms": ["pre-natal", "gestacao", "gravidez", "ansiedade gestacional", "medo do parto", "batimentos fetais", "pressao alta", "pre-eclampsia"]},
    "gynecological_risk": {"weight": 0.70, "terms": ["sangramento anormal", "sangramento intenso", "dor pelvica", "corrimento", "cirurgia ginecologica", "mama", "utero", "ovario"]},
}
INTENSIFIERS = {"sempre", "constantemente", "frequentemente", "repetidamente", "muito", "grave", "extremo"}
HEDGES = {"talvez", "acho", "parece", "supostamente"}
NEGATIONS = {"nao", "nunca", "jamais", "nem"}


def normalize_text_pt(text: str) -> str:
    t = text.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", t).strip()


def _term_count(text: str, term: str) -> int:
    if " " in term:
        return text.count(term)
    return len(re.findall(rf"\b{re.escape(term)}\b", text))


def _sentences(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?<=[.!?;])\s+|\n+", text) if p.strip()]


def _negated_in_sentence(sentence: str, term: str) -> int:
    if " " in term:
        positions = [m.start() for m in re.finditer(re.escape(term), sentence)]
    else:
        positions = [m.start() for m in re.finditer(rf"\b{re.escape(term)}\b", sentence)]
    if not positions:
        return 0
    tokens = list(re.finditer(r"\b\w+\b", sentence))
    negated = 0
    for pos in positions:
        idx = next((i for i, tok in enumerate(tokens) if tok.start() <= pos <= tok.end()), 0)
        left = [tok.group(0) for tok in tokens[max(0, idx - 3):idx]]
        if any(w in NEGATIONS for w in left):
            negated += 1
    return negated


class TextExtractor:
    def analyze(self, text: str) -> dict[str, Any]:
        if not text:
            return {"empty": True, "labels": {}, "overall_text_signal": 0.0, "confidence": 0.0}

        normalized = normalize_text_pt(text)
        sents = _sentences(normalized)
        words = re.findall(r"\b\w+\b", normalized)
        intens_count = sum(1 for w in words if w in INTENSIFIERS)
        hedge_count = sum(1 for w in words if w in HEDGES)
        intens_mult = 1.0 + 0.12 * min(intens_count, 4)
        hedge_mult = max(0.45, 1.0 - 0.18 * min(hedge_count, 3))

        labels: dict[str, Any] = {}
        weighted_sum = 0.0
        weight_total = 0.0
        total_hits = 0

        for label, cfg in SIGNAL_LEXICON.items():
            raw_hits = negated_hits = 0
            hits: list[str] = []
            for term in cfg["terms"]:
                count = _term_count(normalized, term)
                if count > 0:
                    hits.append(term)
                    raw_hits += count
                    for s in sents:
                        negated_hits += _negated_in_sentence(s, term)
            effective = max(0, raw_hits - negated_hits)
            score = min(1.0, (effective / 3.0) * intens_mult * hedge_mult)
            w = float(cfg["weight"])
            weighted_sum += score * w
            weight_total += w
            total_hits += effective
            labels[label] = {"score": round(score, 3), "hit_count": raw_hits, "effective_hit_count": effective, "hits": sorted(set(hits))}

        overall = weighted_sum / weight_total if weight_total else 0.0
        confidence = min(1.0, total_hits / 8.0) * hedge_mult

        return {"empty": False, "labels": labels, "overall_text_signal": round(overall, 3), "confidence": round(confidence, 3), "total_hit_count": total_hits}

    def score(self, text: str) -> ModalityScore:
        analysis = self.analyze(text)
        if analysis.get("empty"):
            return ModalityScore(modality="text", score_0_1=0.0, confidence_0_1=0.0, evidence={"empty": True})
        return ModalityScore(
            modality="text",
            score_0_1=float(analysis["overall_text_signal"]),
            confidence_0_1=float(analysis["confidence"]),
            evidence=analysis,
        )
