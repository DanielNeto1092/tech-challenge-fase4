import { motion } from "framer-motion";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { SentinelaReport } from "@/types/sentinela";
import { MOD_LABELS } from "@/lib/utils";

interface Props {
  report?: SentinelaReport | null;
  demo?: boolean;
}

export default function RadarProfile({ report, demo }: Props) {
  let data: { axis: string; value: number }[];

  if (demo || !report) {
    data = [
      { axis: "Áudio", value: 0.62 },
      { axis: "Texto", value: 0.58 },
      { axis: "Vídeo", value: 0.65 },
      { axis: "Objetos", value: 0.55 },
      { axis: "Clínico", value: 0.48 },
    ];
  } else {
    const ms = report.modality_scores || {};
    const dims = report.care_assessment?.dimensions || {};
    data = [];
    for (const [key, label] of Object.entries(MOD_LABELS)) {
      if (ms[key]) {
        data.push({ axis: label, value: ms[key].score_0_1 || 0 });
      }
    }
    const dimLabels: Record<string, string> = {
      wellbeingIndex: "Bem-Estar",
      safetySignal: "Segurança",
      nonverbalAlert: "Não-Verbal",
      affectiveDistress: "Afeto",
      obstetricRisk: "Obstétrico",
    };
    for (const [key, label] of Object.entries(dimLabels)) {
      if (dims[key] !== undefined) {
        data.push({ axis: label, value: dims[key] });
      }
    }
  }

  if (data.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.4, duration: 0.5 }}
      className="bg-sentinela-surface border border-sentinela-border rounded-xl p-4"
    >
      <h3
        className={
          demo
            ? "font-serif text-[1.1rem] text-sentinela-text mb-1"
            : "text-[0.78rem] uppercase tracking-[1.5px] font-bold text-sentinela-text-3 mb-0.5"
        }
      >
        {demo ? "Cobertura das evidências" : "Perfil Multimodal"}
      </h3>
      <p className="text-[0.85rem] text-sentinela-text-2 mb-2 leading-relaxed">
        {demo
          ? "As modalidades adicionadas aparecerão aqui antes da análise. Após o processamento, o gráfico indicará a contribuição de cada fonte."
          : "Intensidade dos sinais por modalidade — valores maiores indicam maior contribuição para o risco."}
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="rgba(42,37,34,0.08)" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fontSize: 12, fill: "#6F625A", fontFamily: "DM Sans" }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 1]}
            tick={{ fontSize: 10, fill: "#9A8E86" }}
            tickCount={4}
          />
          <Radar
            dataKey="value"
            stroke="#D94A45"
            strokeWidth={2}
            fill="#D94A45"
            fillOpacity={0.08}
            dot={{ r: 4, fill: "#D94A45" }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
