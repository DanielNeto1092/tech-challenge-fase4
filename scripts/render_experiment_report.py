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


def render_report(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    daisee_summary: dict[str, Any] | None = None,
    daisee_metrics: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = []
    lines.append("# Relatorio Experimental - Sentinela AI")
    lines.append("")
    lines.append("## Base Emocional Local")
    lines.append("")
    lines.append(f"- Total de videos indexados: {summary.get('total_files', 0)}")
    for dataset, count in (summary.get("by_dataset", {}) or {}).items():
        lines.append(f"- {dataset}: {count}")
    lines.append("")
    lines.append("## Distribuicao por Emocao")
    lines.append("")
    for emotion, count in (summary.get("by_emotion", {}) or {}).items():
        lines.append(f"- {emotion}: {count}")
    lines.append("")
    lines.append("## Split Experimental")
    lines.append("")
    for split, count in (summary.get("by_split", {}) or {}).items():
        lines.append(f"- {split}: {count}")
    lines.append("")
    lines.append("## Baseline Emocional por Audio")
    lines.append("")
    lines.append(f"- Modelo: {metrics.get('model', 'n/a')}")
    lines.append(f"- Linhas de treino: {metrics.get('train_rows', 0)}")
    lines.append(f"- Linhas de avaliacao: {metrics.get('eval_rows', 0)}")
    lines.append(f"- Accuracy: {_pct(metrics.get('accuracy', 0))}")
    lines.append(f"- Macro-F1: {_pct(metrics.get('macro_f1', 0))}")
    lines.append(f"- Weighted-F1: {_pct(metrics.get('weighted_f1', 0))}")
    lines.append("")
    lines.append("## Leitura dos Resultados")
    lines.append("")
    lines.append(
        "O baseline acustico usa features simples e regressao logistica. "
        "Ele e util como ponto de partida auditavel, mas nao deve ser apresentado como modelo final."
    )
    lines.append("")
    report = metrics.get("classification_report", {}) or {}
    for label in metrics.get("labels", []) or []:
        item = report.get(label, {}) or {}
        lines.append(
            f"- `{label}`: precision {_pct(item.get('precision', 0))}, "
            f"recall {_pct(item.get('recall', 0))}, F1 {_pct(item.get('f1-score', 0))}"
        )
    lines.append("")
    lines.append("## Proximos Passos Tecnicos")
    lines.append("")
    lines.append("- Adicionar MFCCs, centroides espectrais e estatisticas temporais.")
    lines.append("- Avaliar um classificador nao linear como RandomForest ou Gradient Boosting.")
    lines.append("- Separar resultados por dataset para medir transferencia RAVDESS -> CREMA-D.")
    lines.append("- Integrar features faciais/posturais ao mesmo protocolo experimental.")
    lines.append("")
    if daisee_summary and daisee_metrics:
        lines.append("## Baseline Visual de Bem-Estar - DAiSEE")
        lines.append("")
        lines.append(f"- Videos indexados: {daisee_summary.get('total_rows', 0)}")
        lines.append(f"- Videos disponiveis: {daisee_summary.get('available_videos', 0)}")
        lines.append(f"- Modelo: {daisee_metrics.get('model', 'n/a')}")
        lines.append(f"- Linhas de treino: {daisee_metrics.get('train_rows', 0)}")
        lines.append(f"- Linhas de avaliacao: {daisee_metrics.get('eval_rows', 0)}")
        lines.append(f"- Acuracia media: {_pct(daisee_metrics.get('mean_accuracy', 0))}")
        lines.append(f"- Balanced accuracy media: {_pct(daisee_metrics.get('mean_balanced_accuracy', 0))}")
        lines.append(f"- Macro-F1 medio: {_pct(daisee_metrics.get('mean_macro_f1', 0))}")
        lines.append("")
        lines.append("Resultados por dimensao DAiSEE:")
        lines.append("")
        per_label = daisee_metrics.get("per_label", {}) or {}
        for label, item in per_label.items():
            lines.append(
                f"- `{label}`: accuracy {_pct(item.get('accuracy', 0))}, "
                f"balanced accuracy {_pct(item.get('balanced_accuracy', 0))}, "
                f"macro-F1 {_pct(item.get('macro_f1', 0))}, MAE {float(item.get('mae', 0)):.3f}"
            )
        lines.append("")
        lines.append(
            "Leitura critica: as acuracias de `confusion` e `frustration` sao infladas pelo desbalanceamento "
            "das classes, por isso o macro-F1 e a medida mais honesta. O baseline visual deve ser usado como "
            "contexto de bem-estar, nao como inferencia clinica."
        )
        lines.append("")
    lines.append("> Este experimento mede reconhecimento emocional em datasets controlados. Ele nao mede violencia domestica diretamente.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a compact experimental report for the project.")
    parser.add_argument("--summary", default="data/manifests/emotion_video_summary.json")
    parser.add_argument("--metrics", default="models/audio_emotion_baseline/audio_emotion_metrics.json")
    parser.add_argument("--daisee-summary", default="data/manifests/daisee_summary.json")
    parser.add_argument("--daisee-metrics", default="models/daisee_visual_baseline/daisee_visual_metrics.json")
    parser.add_argument("--out", default="data/results/experiment_report.md")
    args = parser.parse_args()

    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    daisee_summary = None
    daisee_metrics = None
    if Path(args.daisee_summary).exists() and Path(args.daisee_metrics).exists():
        daisee_summary = json.loads(Path(args.daisee_summary).read_text(encoding="utf-8"))
        daisee_metrics = json.loads(Path(args.daisee_metrics).read_text(encoding="utf-8"))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_report(summary, metrics, daisee_summary, daisee_metrics), encoding="utf-8")
    print(f"Wrote report -> {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
