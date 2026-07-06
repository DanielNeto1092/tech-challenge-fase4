import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

const STAGES = [
  "Preparando evidências",
  "Enviando arquivos",
  "Processando modalidades",
  "Extraindo sinais relevantes",
  "Aplicando fusão multimodal",
  "Calculando risco",
  "Gerando explicabilidade",
  "Definindo trilha de cuidado",
];

interface Props {
  stage?: number;
}

export default function ProcessingState({ stage = 0 }: Props) {
  const currentIdx = Math.min(stage, STAGES.length - 1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-md mx-auto my-16 text-center"
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="inline-block mb-5"
      >
        <Loader2 size={36} className="text-sentinela-primary" />
      </motion.div>
      <h2 className="font-serif text-[1.6rem] text-sentinela-text mb-4">
        Analisando evidências
      </h2>
      <div className="space-y-2">
        {STAGES.map((label, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: i <= currentIdx ? 1 : 0.3, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center gap-3 text-left"
          >
            <span
              className={`w-2 h-2 rounded-full flex-shrink-0 ${
                i < currentIdx
                  ? "bg-sentinela-success"
                  : i === currentIdx
                    ? "bg-sentinela-primary animate-pulse"
                    : "bg-sentinela-border-med"
              }`}
            />
            <span
              className={`text-[0.85rem] ${
                i <= currentIdx ? "text-sentinela-text-2" : "text-sentinela-text-3"
              }`}
            >
              {label}
            </span>
            {i < currentIdx && (
              <span className="text-[0.72rem] text-sentinela-success ml-auto font-medium">
                ✓
              </span>
            )}
          </motion.div>
        ))}
      </div>
      <div className="mt-6">
        <div className="h-1 bg-sentinela-border rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-sentinela-primary rounded-full"
            initial={{ width: "0%" }}
            animate={{ width: `${((currentIdx + 1) / STAGES.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>
    </motion.div>
  );
}
