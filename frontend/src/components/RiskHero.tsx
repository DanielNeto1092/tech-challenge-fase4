import { motion } from "framer-motion";
import { AlertTriangle, Shield } from "lucide-react";
import type { SentinelaReport } from "@/types/sentinela";
import { LEVEL_LABELS, LEVEL_COLORS } from "@/lib/utils";

interface Props {
  report: SentinelaReport;
}

export default function RiskHero({ report }: Props) {
  const level = report.level || "low";
  const score = report.multimodal_score_0_1 || 0;
  const score100 = Math.round(score * 100);
  const confidence = report.priority?.confidence || 0;
  const review = report.priority?.humanReviewRequired || false;
  const modCount = Object.keys(report.modality_scores || {}).length;
  const color = LEVEL_COLORS[level] || "#6F625A";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative bg-sentinela-surface border border-sentinela-border rounded-2xl p-8 text-center overflow-hidden shadow-panel backdrop-blur"
    >
      <div className="absolute inset-x-8 top-10 h-px bg-gradient-to-r from-transparent via-sentinela-primary/40 to-transparent" />
      <div className="absolute inset-x-8 bottom-10 h-px bg-gradient-to-r from-transparent via-sentinela-primary/20 to-transparent" />

      {/* Top accent bar */}
      <div
        className="absolute top-0 left-0 right-0 h-[3px]"
        style={{
          background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
        }}
      />

      <p
        className="text-[0.8rem] uppercase tracking-[2px] font-bold mb-1"
        style={{ color }}
      >
        Risco {LEVEL_LABELS[level] || level}
      </p>

      <p
        className="font-serif text-[4.5rem] leading-none tracking-normal drop-shadow-[0_0_22px_rgba(56,232,255,0.22)]"
        style={{ color }}
      >
        {score100}
      </p>

      <p className="text-[0.88rem] text-sentinela-text-2 mt-2">
        {(confidence * 100).toFixed(0)}% confiança · {modCount} modalidade
        {modCount > 1 ? "s" : ""}
      </p>

      <p className="text-[0.9rem] text-sentinela-text-2 mt-3 max-w-[520px] mx-auto leading-relaxed">
        {generateSummary(report)}
      </p>

      {review && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="inline-flex items-center gap-1.5 mt-4 px-4 py-1.5 rounded-full text-[0.8rem] font-semibold
                     bg-sentinela-danger/8 text-sentinela-danger border border-sentinela-danger/15"
        >
          <AlertTriangle size={14} />
          Revisão profissional recomendada
        </motion.div>
      )}

      {!review && level === "low" && (
        <div
          className="inline-flex items-center gap-1.5 mt-4 px-4 py-1.5 rounded-full text-[0.8rem] font-semibold
                        bg-sentinela-success/8 text-sentinela-success border border-sentinela-success/15"
        >
          <Shield size={14} />
          Monitoramento de rotina
        </div>
      )}
    </motion.div>
  );
}

function generateSummary(report: SentinelaReport): string {
  const level = report.level || "low";
  const mods = Object.keys(report.modality_scores || {});
  const unavailable = report.metadata?.unavailable || {};
  if (unavailable.objects) {
    const modLabel = mods.length === 1 ? "modalidade processada" : "modalidades processadas";
    return `Análise inconclusiva: a evidência de imagem foi enviada, mas o detector de objetos não está disponível. Resultado baseado em ${mods.length} ${modLabel}.`;
  }
  const desc: Record<string, string> = {
    low: "Perfil de baixo risco",
    medium: "Indicadores moderados de distress",
    high: "Indicadores elevados de risco",
    critical: "Perfil de risco crítico",
  };
  const modLabel = mods.length === 1 ? "modalidade" : "modalidades";
  return `${desc[level] || "Desconhecido"} detectado em ${mods.length} ${modLabel} (score: ${report.multimodal_score_0_1.toFixed(3)}).`;
}
