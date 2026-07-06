import { motion } from "framer-motion";

export default function Hero() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative text-center pt-7 pb-3"
    >
      <div className="mx-auto mb-3 inline-flex items-center gap-2 border border-sentinela-border-med bg-sentinela-elevated/70 px-3 py-1 text-[0.72rem] uppercase tracking-[2px] text-sentinela-primary shadow-glow">
        Proteção multimodal
      </div>
      <h1 className="font-serif text-[3.35rem] leading-[1.05] tracking-normal text-sentinela-text">
        Sentinela<span className="text-sentinela-primary"> AI</span>
      </h1>
      <p className="mt-3 text-[0.95rem] text-sentinela-text-2 max-w-[580px] mx-auto leading-relaxed">
        Sentinela combina relatos, áudio, vídeo, imagem e dados clínicos para
        análise multimodal de sinais de risco e vulnerabilidade, apoiando a
        segurança pública e a proteção integral da mulher.
      </p>
    </motion.div>
  );
}
