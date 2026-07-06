import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";

export default function Limitations() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="bg-sentinela-surface border border-sentinela-border border-l-[3px] border-l-sentinela-warning rounded-xl p-5"
    >
      <h4 className="flex items-center gap-2 text-[0.78rem] uppercase tracking-[1.2px] font-bold text-sentinela-text-3 mb-2">
        <AlertTriangle size={14} className="text-sentinela-warning" />
        Limitações e Responsabilidade
      </h4>
      <ul className="space-y-1.5 text-[0.82rem] text-sentinela-text-3 leading-relaxed list-disc list-inside">
        <li>
          Esta análise é{" "}
          <strong className="text-sentinela-text-2">indicativa</strong> e não
          constitui diagnóstico clínico.
        </li>
        <li>Não substitui avaliação por profissional qualificado.</li>
        <li>
          A precisão depende da qualidade e representatividade dos dados de
          entrada.
        </li>
        <li>
          Casos com indicação de risco elevado exigem revisão humana
          obrigatória.
        </li>
        <li>
          Sistema projetado como ferramenta de apoio à decisão responsável.
        </li>
      </ul>
    </motion.div>
  );
}
