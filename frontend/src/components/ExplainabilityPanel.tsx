import { motion } from "framer-motion";
import type { SentinelaReport } from "@/types/sentinela";
import { buildSignals, scoreColor } from "@/lib/utils";

interface Props {
  report: SentinelaReport;
}

export default function ExplainabilityPanel({ report }: Props) {
  const signals = buildSignals(report);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.4 }}
      className="bg-sentinela-surface border border-sentinela-border rounded-xl p-5"
    >
      <h3 className="font-serif text-[1.05rem] text-sentinela-text mb-0.5">
        Explicabilidade
      </h3>
      <p className="text-[0.82rem] text-sentinela-text-3 mb-4">
        Sinais que contribuíram para a classificação, ordenados por impacto:
      </p>

      {signals.length === 0 ? (
        <p className="text-[0.85rem] text-sentinela-text-3 italic">
          Nenhum sinal significativo detectado.
        </p>
      ) : (
        <div className="space-y-2">
          {signals.slice(0, 6).map((s, i) => {
            const color = scoreColor(s.value / 0.3);
            const pct = Math.max(
              3,
              Math.min(Math.round((s.value / 0.3) * 100), 100),
            );
            return (
              <motion.div
                key={s.signal}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * i }}
                className="flex items-center gap-3 py-2 border-b border-sentinela-border last:border-0"
              >
                <span className="flex-[2] text-[0.85rem] font-medium text-sentinela-text-2 truncate">
                  {s.signal}
                </span>
                <div className="flex-[3] h-1 rounded-full bg-sentinela-border overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                  />
                </div>
                <span
                  className="min-w-[52px] text-right text-[0.78rem] font-mono"
                  style={{ color }}
                >
                  +{s.value.toFixed(3)}
                </span>
              </motion.div>
            );
          })}
        </div>
      )}

      {signals.length > 0 && signals[0].detail && (
        <p className="mt-3 text-[0.78rem] text-sentinela-text-3">
          Detalhe principal: {signals[0].detail}
        </p>
      )}
    </motion.div>
  );
}
