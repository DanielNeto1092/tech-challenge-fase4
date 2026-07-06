import { motion } from "framer-motion";
import type { SentinelaReport } from "@/types/sentinela";
import { MOD_LABELS, MOD_COLORS, scoreColor } from "@/lib/utils";

interface Props {
  report: SentinelaReport;
}

export default function ModalityCards({ report }: Props) {
  const ms = report.modality_scores || {};
  const keys = Object.keys(ms).filter((k) => k in MOD_LABELS);

  if (keys.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="grid grid-cols-2 gap-3"
    >
      {keys.map((key, i) => {
        const score = ms[key].score_0_1 || 0;
        const pct = Math.max(1, Math.round(score * 100));
        const modColor = MOD_COLORS[key] || "#D94A45";
        const sc = scoreColor(score);
        const detail = getModalityDetail(key, ms[key]);

        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i }}
            className="bg-sentinela-elevated border border-sentinela-border rounded-xl p-4 hover:border-sentinela-border-med transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span
                className="text-[0.78rem] uppercase tracking-[0.5px] font-bold"
                style={{ color: modColor }}
              >
                {MOD_LABELS[key] || key}
              </span>
              <span
                className="text-[1.05rem] font-extrabold font-mono"
                style={{ color: sc }}
              >
                {score.toFixed(3)}
              </span>
            </div>
            <div className="h-[3px] bg-sentinela-border rounded-full overflow-hidden mb-2">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${pct}%`, backgroundColor: modColor }}
              />
            </div>
            <p className="text-[0.78rem] text-sentinela-text-3">{detail}</p>
          </motion.div>
        );
      })}
    </motion.div>
  );
}

function getModalityDetail(
  key: string,
  data: { score_0_1: number; evidence?: Record<string, unknown> },
): string {
  const ev = data.evidence || {};
  if (key === "text") {
    const labels = (ev.labels || {}) as Record<string, Record<string, unknown>>;
    const active = Object.entries(labels)
      .filter(([, v]) => typeof v === "object" && (v?.score as number) > 0)
      .map(([k]) => k.replace(/_/g, " "));
    return active.slice(0, 3).join(", ") || "sem sinais";
  }
  if (key === "audio") {
    const emo = (ev.emotion_baseline || {}) as Record<string, unknown>;
    if (emo.available) return `emoção: ${emo.predictedEmotion || "?"}`;
    return "análise acústica";
  }
  if (key === "video") {
    const mode = (ev.mode as string) || "";
    const wb = ev.visual_wellbeing as Record<string, unknown> | undefined;
    const parts: string[] = [];
    if (mode) parts.push(mode === "temporal" ? "postura" : mode);
    if (wb && (wb as Record<string, unknown>).available) {
      const preds = (wb as Record<string, unknown>).predictions as Record<string, number> | undefined;
      if (preds) {
        const strain = wb.visualStrain as number;
        if (strain > 0) parts.push(`strain ${strain.toFixed(2)}`);
        else parts.push("visual estável");
      }
    }
    return parts.join(" · ") || "análise visual";
  }  if (key === "objects") {
    const det = (ev.risk_detections as number) || 0;
    return det ? `${det} detecção(ões)` : "nenhuma detecção";
  }
  if (key === "clinical") {
    const source = (ev.source as string) || "";
    if (source) return `fonte: ${source}`;
    return "sinais vitais avaliados";
  }
  return "";
}
