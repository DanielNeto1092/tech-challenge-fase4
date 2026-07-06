import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { SentinelaReport, Signal, TimelineEvent } from "@/types/sentinela";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const LEVEL_LABELS: Record<string, string> = {
  low: "Baixo",
  medium: "Moderado",
  high: "Elevado",
  critical: "Crítico",
};

export const LEVEL_COLORS: Record<string, string> = {
  low: "#2F7D4C",
  medium: "#B97818",
  high: "#A83232",
  critical: "#A83232",
};

export const PATHWAY_LABELS: Record<string, string> = {
  acompanhamento_rotina: "Acompanhamento de Rotina",
  coleta_adicional: "Coleta Adicional de Dados",
  acolhimento_e_monitoramento: "Acolhimento e Monitoramento",
  revisao_prioritaria: "Revisão Prioritária",
};

export const PATHWAY_SHORT: Record<string, string> = {
  acompanhamento_rotina: "Rotina",
  coleta_adicional: "Coleta",
  acolhimento_e_monitoramento: "Acolhimento",
  revisao_prioritaria: "Prioritária",
};

export const PATHWAY_ORDER = [
  "acompanhamento_rotina",
  "coleta_adicional",
  "acolhimento_e_monitoramento",
  "revisao_prioritaria",
];

export const MOD_LABELS: Record<string, string> = {
  audio: "Áudio",
  text: "Texto",
  video: "Vídeo",
  objects: "Objetos",
  clinical: "Clínico",
};

export const MOD_COLORS: Record<string, string> = {
  audio: "#D94A45",
  text: "#7C5CBF",
  video: "#1E7FB8",
  objects: "#B97818",
  clinical: "#2A8C6A",
};

export function scoreColor(s: number): string {
  if (s > 0.6) return "#A83232";
  if (s > 0.3) return "#B97818";
  return "#2F7D4C";
}

export function buildSignals(report: SentinelaReport): Signal[] {
  const signals: Signal[] = [];
  const ms = report.modality_scores || {};
  const weights = report.weights || {};

  const audio = ms.audio;
  if (audio) {
    const score = audio.score_0_1 || 0;
    const ev = (audio.evidence || {}) as Record<string, unknown>;
    const comps = (ev.components || {}) as Record<string, number>;
    const emo = (ev.emotion_baseline || {}) as Record<string, unknown>;
    if (score > 0) {
      signals.push({
        signal: "Distress vocal",
        value: Math.round(score * (weights.audio || 0) * 1000) / 1000,
        detail: `variabilidade=${(comps.variability || 0).toFixed(2)}`,
      });
    }
    if (emo.available) {
      signals.push({
        signal: `Emoção: ${emo.predictedEmotion || "?"}`,
        value:
          Math.round(((emo.confidence as number) || 0) * 0.15 * 1000) / 1000,
        detail: `confiança=${((emo.confidence as number) || 0).toFixed(2)}`,
      });
    }
  }

  const text = ms.text;
  if (text) {
    const ev = (text.evidence || {}) as Record<string, unknown>;
    const labels = (ev.labels || {}) as Record<string, Record<string, unknown>>;
    const labelPt: Record<string, string> = {
      safety_concern: "segurança",
      coercion: "coerção",
      isolation: "isolamento",
      hopelessness: "desesperança",
      psychological_distress: "distress psicológico",
    };
    Object.entries(labels)
      .filter(([, v]) => typeof v === "object" && (v?.score as number) > 0)
      .sort(
        (a, b) =>
          ((b[1]?.score as number) || 0) - ((a[1]?.score as number) || 0),
      )
      .forEach(([lbl, data]) => {
        signals.push({
          signal: `Texto: ${labelPt[lbl] || lbl.replace(/_/g, " ")}`,
          value:
            Math.round(
              ((data.score as number) || 0) * (weights.text || 0) * 1000,
            ) / 1000,
          detail: ((data.hits as string[]) || []).slice(0, 3).join(", "),
        });
      });
  }

  const video = ms.video;
  if (video && video.score_0_1 > 0) {
    const ev = (video.evidence || {}) as Record<string, unknown>;
    signals.push({
      signal: `Vídeo: ${ev.mode || "análise"}`,
      value: Math.round(video.score_0_1 * (weights.video || 0) * 1000) / 1000,
      detail: `modo=${ev.mode || "?"}`,
    });
  }

  const objects = ms.objects;
  if (objects && objects.score_0_1 > 0) {
    const ev = (objects.evidence || {}) as Record<string, unknown>;
    signals.push({
      signal: "Objeto cortante",
      value:
        Math.round(objects.score_0_1 * (weights.objects || 0) * 1000) / 1000,
      detail: `detecções=${ev.risk_detections || 0}`,
    });
  }

  const clinical = ms.clinical;
  if (clinical && clinical.score_0_1 > 0) {
    const ev = (clinical.evidence || {}) as Record<string, unknown>;
    const source = (ev.source as string) || "clínico";
    signals.push({
      signal: `Risco clínico (${source})`,
      value:
        Math.round(clinical.score_0_1 * (weights.clinical || 0) * 1000) / 1000,
      detail: `score=${clinical.score_0_1.toFixed(2)}`,
    });
  }

  return signals.sort((a, b) => b.value - a.value);
}

export function buildTimeline(report: SentinelaReport): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  const trace = report._trace;
  const ms = report.modality_scores || {};
  if (!trace?.stages) return events;

  let cumulative = 0;
  for (const s of trace.stages) {
    cumulative += s.elapsed_ms || 0;
    const ts = `${(cumulative / 1000).toFixed(2)}s`;
    const name = s.stage;

    if (name === "text_extraction" && (ms.text?.score_0_1 || 0) > 0.3) {
      const sc = ms.text!.score_0_1;
      events.push({
        time: ts,
        text: `Sinais textuais detectados (score ${sc.toFixed(2)})`,
        severity: sc > 0.5 ? "warning" : "info",
      });
    } else if (
      name === "audio_extraction" &&
      (ms.audio?.score_0_1 || 0) > 0.2
    ) {
      const sc = ms.audio!.score_0_1;
      events.push({
        time: ts,
        text: `Indicador de distress vocal (score ${sc.toFixed(2)})`,
        severity: sc > 0.5 ? "warning" : "info",
      });
    } else if (name === "audio_emotion") {
      const emo = ((ms.audio?.evidence || {}) as Record<string, unknown>)
        .emotion_baseline as Record<string, unknown> | undefined;
      if (emo?.available) {
        events.push({
          time: ts,
          text: `Emoção classificada: ${emo.predictedEmotion}`,
          severity: "info",
        });
      }
    } else if (
      name === "object_detection" &&
      (ms.objects?.score_0_1 || 0) > 0
    ) {
      const sc = ms.objects!.score_0_1;
      events.push({
        time: ts,
        text: `Objeto cortante detectado (score ${sc.toFixed(2)})`,
        severity: sc > 0.7 ? "critical" : "warning",
      });
    } else if (name === "clinical_extraction") {
      const sc = ms.clinical?.score_0_1 || 0;
      if (sc > 0) {
        events.push({
          time: ts,
          text: `Risco clínico/obstétrico avaliado (score ${sc.toFixed(2)})`,
          severity: sc >= 0.7 ? "critical" : sc >= 0.4 ? "warning" : "info",
        });
      }
    } else if (name === "fusion_engine") {
      events.push({
        time: ts,
        text: `Fusão multimodal concluída — nível: ${LEVEL_LABELS[report.level] || report.level}`,
        severity: "info",
      });
    } else if (name === "care_engine") {
      const pw = report.care_assessment?.carePathway || "?";
      events.push({
        time: ts,
        text: `Trilha recomendada: ${PATHWAY_LABELS[pw] || pw}`,
        severity: "info",
      });
    }
  }
  return events;
}
