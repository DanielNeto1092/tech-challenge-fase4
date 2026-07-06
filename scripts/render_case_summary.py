from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _pct(x: Any) -> str:
    try:
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return "n/a"


def render_summary(report: dict[str, Any]) -> str:
    priority = report.get("priority", {}) or {}
    care = report.get("care_assessment", {}) or {}
    dims = care.get("dimensions", {}) or {}
    modality_scores = report.get("modality_scores", {}) or {}

    lines: list[str] = []
    lines.append("# Resumo do Caso - Sentinela AI")
    lines.append("")
    lines.append("## Resultado Geral")
    lines.append("")
    lines.append(f"- Score multimodal: {_pct(report.get('multimodal_score_0_1', 0))}")
    lines.append(f"- Nivel de fusao: `{report.get('level', 'n/a')}`")
    lines.append(f"- Prioridade operacional: `{priority.get('riskLevel', 'n/a')}`")
    lines.append(f"- Confianca da prioridade: {_pct(priority.get('confidence', 0))}")
    lines.append(f"- Revisao humana requerida: `{priority.get('humanReviewRequired', False)}`")
    lines.append(f"- Trilha de cuidado: `{care.get('carePathwayLabel', care.get('carePathway', 'n/a'))}`")
    lines.append("")

    lines.append("## Dimensoes de Cuidado")
    lines.append("")
    dimension_labels = {
        "wellbeingIndex": "Indice de bem-estar",
        "affectiveDistress": "Sofrimento afetivo",
        "safetySignal": "Sinal de seguranca/vulnerabilidade",
        "nonverbalAlert": "Alerta nao verbal",
        "audioEmotionDistress": "Sofrimento por emocao vocal",
        "visualWellbeingStrain": "Carga visual de bem-estar",
        "textSafetyConcern": "Sinal textual de seguranca",
        "textControlOrCoercion": "Sinal textual de controle/coercao",
        "textHopelessness": "Sinal textual de desesperanca",
        "textPsychologicalDistress": "Sofrimento psicologico textual",
        "dataQuality": "Qualidade dos dados",
        "uncertainty": "Incerteza",
    }
    for key, label in dimension_labels.items():
        lines.append(f"- {label}: {_pct(dims.get(key, 0))}")
    lines.append("")

    lines.append("## Evidencias por Modalidade")
    lines.append("")
    for name in ("audio", "text", "video"):
        item = modality_scores.get(name)
        if not item:
            continue
        lines.append(
            f"- `{name}`: score {_pct(item.get('score_0_1', 0))}, "
            f"confianca {_pct(item.get('confidence_0_1', 0))}"
        )
        if name == "audio":
            emotion = ((item.get("evidence", {}) or {}).get("emotion_baseline", {}) or {})
            if emotion.get("available"):
                lines.append(
                    f"  Emocao vocal estimada: `{emotion.get('predictedEmotion')}` "
                    f"({_pct(emotion.get('confidence', 0))})"
                )
                warnings = emotion.get("domainWarnings", []) or []
                for warning in warnings:
                    lines.append(f"  Aviso do modelo emocional: `{warning}`")
        if name == "video":
            visual = ((item.get("evidence", {}) or {}).get("visual_wellbeing", {}) or {})
            if visual.get("available"):
                preds = visual.get("predictions", {}) or {}
                lines.append(
                    "  Bem-estar visual DAiSEE: "
                    + ", ".join(f"{key}={value}" for key, value in preds.items())
                    + f"; strain {_pct(visual.get('visualStrain', 0))}"
                )
    lines.append("")

    top_signals = priority.get("topSignals", []) or []
    if top_signals:
        lines.append("## Sinais Mais Relevantes")
        lines.append("")
        for signal in top_signals:
            lines.append(f"- `{signal.get('label', 'n/a')}`: {_pct(signal.get('score', 0))}")
        lines.append("")

    focus = care.get("reviewFocus", []) or []
    if focus:
        lines.append("## Foco Para Revisao Humana")
        lines.append("")
        for item in focus:
            lines.append(f"- {item}")
        lines.append("")

    next_steps = care.get("nextSteps", []) or []
    if next_steps:
        lines.append("## Proximos Passos de Acolhimento")
        lines.append("")
        for item in next_steps:
            lines.append(f"- {item}")
        lines.append("")

    questions = care.get("suggestedQuestions", []) or []
    if questions:
        lines.append("## Perguntas Sugeridas")
        lines.append("")
        for question in questions:
            lines.append(f"- {question}")
        lines.append("")

    guidance = care.get("communicationGuidance", []) or []
    if guidance:
        lines.append("## Orientacao de Comunicacao")
        lines.append("")
        for item in guidance:
            lines.append(f"- {item}")
        lines.append("")

    privacy = care.get("privacyChecklist", []) or []
    if privacy:
        lines.append("## Privacidade e Seguranca")
        lines.append("")
        for item in privacy:
            lines.append(f"- {item}")
        lines.append("")

    flags = priority.get("anomalyFlags", []) or []
    if flags:
        lines.append("## Alertas de Incerteza/Anomalia")
        lines.append("")
        for flag in flags:
            lines.append(f"- `{flag}`")
        lines.append("")

    lines.append("## Guardrails")
    lines.append("")
    for guardrail in care.get("guardrails", []) or []:
        lines.append(f"- {guardrail}")
    lines.append("")
    lines.append("> Este resumo apoia triagem e revisao humana. Ele nao diagnostica violencia domestica, depressao ou qualquer condicao clinica.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a human-readable case summary from a risk report JSON.")
    parser.add_argument("--report", default="data/results/risk_report_text_audio.json")
    parser.add_argument("--out", default="data/results/case_summary.md")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        raise SystemExit(f"ERROR: report not found: {report_path}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = render_summary(report)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(summary, encoding="utf-8")
    print(f"Wrote summary -> {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
