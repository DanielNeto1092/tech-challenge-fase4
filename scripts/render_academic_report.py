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


def _load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def render_report(
    *,
    emotion_summary: dict[str, Any],
    audio_metrics: dict[str, Any],
    daisee_summary: dict[str, Any],
    daisee_metrics: dict[str, Any],
) -> str:
    lines: list[str] = []
    lines.append("# Sentinela AI - Relatorio Final")
    lines.append("")
    lines.append("## Abstract")
    lines.append("")
    lines.append(
        "This work presents Sentinela AI, a multimodal and trauma-informed architecture for preventive "
        "inference of emotional vulnerability, psychological distress and behavioral risk in women. "
        "The system combines public affective-computing datasets, interpretable baselines and human review "
        "to support triage without claiming automatic diagnosis of abuse or mental-health conditions."
    )
    lines.append("")
    lines.append("## Resumo")
    lines.append("")
    lines.append(
        "A Sentinela AI e uma arquitetura multimodal para inferencia preventiva de "
        "vulnerabilidade emocional, sofrimento psicologico e risco comportamental feminino. "
        "O sistema nao diagnostica violencia domestica, depressao ou trauma; ele organiza sinais "
        "de audio, texto e video para apoiar acolhimento, revisao humana e monitoramento responsavel."
    )
    lines.append("")
    lines.append("## Problema e Reposicionamento")
    lines.append("")
    lines.append(
        "Datasets reais de violencia domestica multimodal sao raros por razoes eticas, legais e de "
        "privacidade. Por isso, o projeto foi reposicionado de um detector direto de violencia para "
        "um sistema de inferencia indireta de vulnerabilidade e sofrimento, combinando bases publicas "
        "de emocao, comportamento, anomalia e perspectiva de genero."
    )
    lines.append("")
    lines.append("## Arquitetura")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append("    A[Entrada multimodal] --> B1[Audio]")
    lines.append("    A --> B2[Texto]")
    lines.append("    A --> B3[Video]")
    lines.append("    B1 --> C1[Features acusticas + emocao vocal]")
    lines.append("    B2 --> C2[Sinais textuais multi-label]")
    lines.append("    B3 --> C3[Pose, movimento, DAiSEE visual]")
    lines.append("    C1 --> D[Late fusion ponderada por confianca]")
    lines.append("    C2 --> D")
    lines.append("    C3 --> D")
    lines.append("    D --> E[Prioridade operacional]")
    lines.append("    D --> F[Care Assessment trauma-informado]")
    lines.append("    E --> G[Revisao humana]")
    lines.append("    F --> G")
    lines.append("```")
    lines.append("")
    lines.append("A arquitetura usa late fusion ponderada por confianca no MVP:")
    lines.append("")
    lines.append("- Audio: energia, pausas, ZCR, variabilidade e baseline emocional acustico.")
    lines.append("- Texto: sinais multi-label auditaveis em portugues.")
    lines.append("- Video: movimento, pose e baseline visual DAiSEE.")
    lines.append("- Care Assessment: trilha de cuidado, privacidade, comunicacao trauma-informada e revisao humana.")
    lines.append("")
    lines.append("A evolucao proposta e attention fusion com backbones modernos: Video Swin, TimeSformer, ViViT, wav2vec2, HuBERT, OpenSMILE e BERTimbau.")
    lines.append("")
    lines.append("## Bases Publicas e Controladas")
    lines.append("")
    lines.append("| Camada | Bases | Papel |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| Core emocional | RAVDESS, CREMA-D | {emotion_summary.get('total_files', 0)} videos indexados para baseline emocional |")
    lines.append(f"| Bem-estar visual | DAiSEE | {daisee_summary.get('total_rows', 0)} videos para boredom, engagement, confusion e frustration |")
    lines.append("| Anomalia visual | UCF-Crime | apenas motion anomaly pretraining e temporal anomaly learning |")
    lines.append("| Conversacao e generalizacao | MELD, IEMOCAP, CMU-MOSEI, SEWA | roadmap para dialogo emocional e in-the-wild |")
    lines.append("| Saude mental/distress | DAIC-WOZ, AVEC, MuSe | roadmap para entrevistas clinicas, depressao, stress e distress |")
    lines.append("| Perspectiva feminina | WEMAC, UC3M4Safety | fundamentacao e especializacao com genero |")
    lines.append("")
    lines.append("## Experimentos")
    lines.append("")
    lines.append("### Baseline Emocional por Audio")
    lines.append("")
    lines.append(f"- Modelo: {audio_metrics.get('model', 'n/a')}")
    lines.append(f"- Treino: {audio_metrics.get('train_rows', 0)} amostras.")
    lines.append(f"- Avaliacao: {audio_metrics.get('eval_rows', 0)} amostras.")
    lines.append(f"- Accuracy: {_pct(audio_metrics.get('accuracy', 0))}.")
    lines.append(f"- Macro-F1: {_pct(audio_metrics.get('macro_f1', 0))}.")
    lines.append("")
    lines.append("### Baseline Visual DAiSEE")
    lines.append("")
    lines.append(f"- Modelo: {daisee_metrics.get('model', 'n/a')}")
    lines.append(f"- Treino: {daisee_metrics.get('train_rows', 0)} amostras.")
    lines.append(f"- Avaliacao: {daisee_metrics.get('eval_rows', 0)} amostras.")
    lines.append(f"- Acuracia media: {_pct(daisee_metrics.get('mean_accuracy', 0))}.")
    lines.append(f"- Balanced accuracy media: {_pct(daisee_metrics.get('mean_balanced_accuracy', 0))}.")
    lines.append(f"- Macro-F1 medio: {_pct(daisee_metrics.get('mean_macro_f1', 0))}.")
    lines.append("")
    per_label = daisee_metrics.get("per_label", {}) or {}
    for label, item in per_label.items():
        lines.append(f"- `{label}`: accuracy {_pct(item.get('accuracy', 0))}, macro-F1 {_pct(item.get('macro_f1', 0))}, MAE {float(item.get('mae', 0)):.3f}.")
    lines.append("")
    lines.append("## Leitura Critica")
    lines.append("")
    lines.append(
        "Os resultados iniciais sao baselines, nao estado da arte. O macro-F1 baixo no DAiSEE evidencia "
        "desbalanceamento e limita a interpretacao de acuracia. Esse ponto e tratado como achado metodologico: "
        "a Sentinela privilegia transparencia, incerteza e revisao humana em vez de mascarar limitacoes."
    )
    lines.append("")
    lines.append("## Governanca e Trauma-Informed Design")
    lines.append("")
    lines.append("- A saida evita linguagem diagnostica.")
    lines.append("- Casos sensiveis exigem revisao humana.")
    lines.append("- O sistema sugere perguntas cuidadosas e nao acusatorias.")
    lines.append("- O dashboard reforca privacidade, consentimento e comunicacao sem julgamento.")
    lines.append("- O relatorio inclui avisos de fora de dominio e qualidade dos dados.")
    lines.append("")
    lines.append("## Limitacoes")
    lines.append("")
    lines.append("- RAVDESS/CREMA-D sao bases atuadas e controladas.")
    lines.append("- DAiSEE nao e base clinica; serve apenas como contexto visual de bem-estar.")
    lines.append("- UCF-Crime nao deve ser usado como proxy de violencia domestica.")
    lines.append("- O NLP atual e auditavel, mas ainda nao usa embeddings contextuais.")
    lines.append("- O sistema nao substitui avaliacao profissional.")
    lines.append("")
    lines.append("## Trabalhos Futuros")
    lines.append("")
    lines.append("- Integrar BERTimbau para leitura contextual em PT-BR.")
    lines.append("- Substituir features acusticas manuais por wav2vec2, HuBERT ou OpenSMILE.")
    lines.append("- Avaliar Video Swin/TimeSformer/ViViT para comportamento visual temporal.")
    lines.append("- Incorporar UCA para video-language understanding em vigilancia.")
    lines.append("- Comparar late fusion com attention fusion quando houver dados multimodais alinhados.")
    lines.append("")
    lines.append("## Referencias Essenciais")
    lines.append("")
    lines.append("- RAVDESS: Livingstone & Russo, 2018.")
    lines.append("- CREMA-D: Cao et al., 2014.")
    lines.append("- DAiSEE: Gupta et al., 2016.")
    lines.append("- UCF-Crime: Sultani, Chen & Shah, 2018.")
    lines.append("- UCA: Yuan et al., CVPR 2024.")
    lines.append("- WEMAC/UC3M4Safety: Miranda et al. e projeto EMPATIA-CM.")
    lines.append("")
    lines.append("## Conclusao")
    lines.append("")
    lines.append(
        "A Sentinela AI demonstra uma arquitetura madura de IA multimodal aplicada a saude e seguranca "
        "da mulher: tecnicamente auditavel, metodologicamente honesta, sensivel a trauma e preparada para "
        "evolucao com datasets e backbones de pesquisa."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the final academic report from current metrics.")
    parser.add_argument("--out", default="data/results/final_academic_report.md")
    parser.add_argument("--emotion-summary", default="data/manifests/emotion_video_summary.json")
    parser.add_argument("--audio-metrics", default="models/audio_emotion_baseline/audio_emotion_metrics.json")
    parser.add_argument("--daisee-summary", default="data/manifests/daisee_summary.json")
    parser.add_argument("--daisee-metrics", default="models/daisee_visual_baseline/daisee_visual_metrics.json")
    args = parser.parse_args()

    report = render_report(
        emotion_summary=_load_json(args.emotion_summary),
        audio_metrics=_load_json(args.audio_metrics),
        daisee_summary=_load_json(args.daisee_summary),
        daisee_metrics=_load_json(args.daisee_metrics),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Wrote report -> {out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
