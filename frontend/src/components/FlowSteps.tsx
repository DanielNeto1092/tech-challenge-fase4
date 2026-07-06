import { motion } from "framer-motion";

const steps = [
  { num: 1, label: "Evidências" },
  { num: 2, label: "Análise" },
  { num: 3, label: "Risco" },
  { num: 4, label: "Alerta Azure" },
];

export default function FlowSteps() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2, duration: 0.4 }}
      className="flex justify-center gap-2 flex-wrap my-5"
    >
      {steps.map((s) => (
        <div
          key={s.num}
          className="flex items-center gap-2 px-4 py-2 bg-sentinela-surface border border-sentinela-border shadow-glow backdrop-blur"
        >
          <span className="w-5 h-5 rounded-full bg-sentinela-primary text-white text-[0.65rem] font-bold flex items-center justify-center">
            {s.num}
          </span>
          <span className="text-[0.8rem] text-sentinela-text-2">{s.label}</span>
        </div>
      ))}
    </motion.div>
  );
}
