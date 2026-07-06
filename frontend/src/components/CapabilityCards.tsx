import { motion } from "framer-motion";

const cards = [
  { value: "5", label: "Modalidades" },
  { value: "Fusão Tardia", label: "Estratégia", isText: true },
  { value: "Azure", label: "Integração", isText: true },
  { value: "4", label: "Trilhas de Cuidado" },
];

export default function CapabilityCards() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.4 }}
      className="grid grid-cols-4 gap-3 my-4"
    >
      {cards.map((c) => (
        <div
          key={c.label}
          className="bg-sentinela-surface border border-sentinela-border rounded-xl p-4 text-center flex flex-col items-center justify-center shadow-panel backdrop-blur"
        >
          <div
            className={`leading-none mb-1 ${
              c.isText
                ? "font-serif text-[1.15rem] text-sentinela-text"
                : "font-serif text-[2rem] text-sentinela-text"
            }`}
          >
            {c.value}
          </div>
          <div className="text-[0.72rem] uppercase tracking-[1.2px] font-semibold text-sentinela-text-3">
            {c.label}
          </div>
        </div>
      ))}
    </motion.div>
  );
}
