import { useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Mic,
  Video,
  Image,
  Sparkles,
  Info,
  Heart,
} from "lucide-react";
import type { ClinicalData } from "@/types/sentinela";

interface SidebarProps {
  transcript: string;
  setTranscript: (v: string) => void;
  audio: File | null;
  setAudio: (f: File | null) => void;
  video: File | null;
  setVideo: (f: File | null) => void;
  image: File | null;
  setImage: (f: File | null) => void;
  clinical: ClinicalData;
  setClinical: (c: ClinicalData) => void;
  onAnalyze: () => void;
  isProcessing: boolean;
}

export default function Sidebar({
  transcript,
  setTranscript,
  audio,
  setAudio,
  video,
  setVideo,
  image,
  setImage,
  clinical,
  setClinical,
  onAnalyze,
  isProcessing,
}: SidebarProps) {
  const audioRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLInputElement>(null);
  const imageRef = useRef<HTMLInputElement>(null);
  const [showClinical, setShowClinical] = useState(false);

  const hasClinical = Object.values(clinical).some(
    (v) => v != null && v !== "",
  );
  const hasInput = transcript.trim() || audio || video || image || hasClinical;

  const uploads = [
    {
      key: "audio",
      file: audio,
      icon: <Mic size={16} />,
      label: "Áudio",
      accept: ".wav,.mp3,.m4a,.ogg,.flac",
      hint: "WAV, MP3, M4A",
      ref: audioRef as React.RefObject<HTMLInputElement>,
      setter: setAudio,
      cta: "Adicionar áudio",
    },
    {
      key: "video",
      file: video,
      icon: <Video size={16} />,
      label: "Vídeo",
      accept: ".mp4,.avi,.mov",
      hint: "MP4, AVI, MOV",
      ref: videoRef as React.RefObject<HTMLInputElement>,
      setter: setVideo,
      cta: "Adicionar vídeo",
    },
    {
      key: "image",
      file: image,
      icon: <Image size={16} />,
      label: "Imagem",
      accept: ".jpg,.jpeg,.png",
      hint: "JPG, PNG",
      ref: imageRef as React.RefObject<HTMLInputElement>,
      setter: setImage,
      cta: "Adicionar imagem",
    },
  ];

  return (
    <aside className="w-[300px] min-h-screen bg-sentinela-surface/90 border-r border-sentinela-border flex flex-col shadow-panel backdrop-blur-xl">
      {/* Evidence Inputs */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        <h3 className="font-serif text-[1.1rem] text-sentinela-text mb-1 pb-2 border-b border-sentinela-border">
          Evidências do caso
        </h3>

        {/* Transcript */}
        <div>
          <label className="flex items-center gap-1.5 text-[0.8rem] font-semibold text-sentinela-text-2 mb-1">
            <FileText size={14} /> Relato ou transcrição
          </label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Cole um relato, transcrição ou observação relevante do caso."
            className="w-full h-20 px-3 py-2.5 text-[0.85rem] bg-sentinela-elevated border border-sentinela-border rounded-xl
                       resize-y placeholder:text-sentinela-text-3 focus:outline-none focus:border-sentinela-primary/40
                       focus:ring-2 focus:ring-sentinela-primary/10 transition-all"
          />
        </div>

        {/* File Uploads */}
        {uploads.map((u) => (
          <div key={u.key}>
            <label className="flex items-center gap-1.5 text-[0.8rem] font-semibold text-sentinela-text-2 mb-1">
              {u.icon} {u.label}
              <span className="ml-auto text-[0.7rem] font-normal text-sentinela-text-3">
                {u.hint}
              </span>
            </label>
            <input
              ref={u.ref}
              type="file"
              accept={u.accept}
              className="hidden"
              onChange={(e) => u.setter(e.target.files?.[0] || null)}
            />
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => u.ref.current?.click()}
              className={`w-full px-3 py-2.5 rounded-xl border text-left text-[0.82rem] transition-all
                ${
                  u.file
                    ? "bg-sentinela-primary/5 border-sentinela-primary/20 text-sentinela-text"
                    : "bg-sentinela-elevated border-sentinela-border text-sentinela-text-3 hover:border-sentinela-primary/30"
                }`}
            >
              {u.file ? (
                <span className="flex items-center gap-2">
                  <span className="text-sentinela-primary font-semibold">✓</span>
                  <span className="truncate">{u.file.name}</span>
                </span>
              ) : (
                <span>{u.cta}</span>
              )}
            </motion.button>
            {u.file && (
              <button
                onClick={() => u.setter(null)}
                className="text-[0.72rem] text-sentinela-text-3 hover:text-sentinela-danger mt-1 ml-1"
              >
                Remover
              </button>
            )}
          </div>
        ))}

        {/* Clinical Data */}
        <div>
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowClinical(!showClinical)}
            className={`w-full px-3 py-2.5 rounded-xl border text-left text-[0.82rem] transition-all
              ${
                hasClinical
                  ? "bg-sentinela-primary/5 border-sentinela-primary/20 text-sentinela-text"
                  : "bg-sentinela-elevated border-sentinela-border text-sentinela-text-3 hover:border-sentinela-primary/30"
              }`}
          >
            <span className="flex items-center gap-2">
              <Heart size={14} />
              {hasClinical ? (
                <>
                  <span className="text-sentinela-primary font-semibold">✓</span>
                  <span>Dados clínicos inseridos</span>
                </>
              ) : (
                <span>Adicionar dados clínicos</span>
              )}
            </span>
          </motion.button>
          {showClinical && (
            <div className="mt-2 space-y-2 bg-sentinela-elevated border border-sentinela-border rounded-xl p-3">
              <p className="text-[0.72rem] text-sentinela-text-3 mb-2">
                Sinais vitais obstétricos (opcionais)
              </p>
              {(
                [
                  { key: "age", label: "Idade", placeholder: "ex: 28" },
                  {
                    key: "systolic_bp",
                    label: "PA Sistólica (mmHg)",
                    placeholder: "ex: 120",
                  },
                  {
                    key: "diastolic_bp",
                    label: "PA Diastólica (mmHg)",
                    placeholder: "ex: 80",
                  },
                  {
                    key: "blood_sugar",
                    label: "Glicose (mmol/L)",
                    placeholder: "ex: 7.5",
                  },
                  {
                    key: "body_temp",
                    label: "Temperatura (°C)",
                    placeholder: "ex: 37.0",
                  },
                  {
                    key: "heart_rate",
                    label: "Freq. Cardíaca (bpm)",
                    placeholder: "ex: 76",
                  },
                  {
                    key: "baseline_fhr",
                    label: "FC fetal basal (bpm)",
                    placeholder: "ex: 140",
                  },
                  {
                    key: "nsp_class",
                    label: "CTG NSP (1, 2 ou 3)",
                    placeholder: "ex: 2",
                  },
                ] as const
              ).map((field) => (
                <div key={field.key}>
                  <label className="text-[0.72rem] text-sentinela-text-2">
                    {field.label}
                  </label>
                  <input
                    type="number"
                    step="any"
                    placeholder={field.placeholder}
                    value={clinical[field.key as keyof ClinicalData] ?? ""}
                    onChange={(e) => {
                      const val = e.target.value
                        ? Number(e.target.value)
                        : undefined;
                      setClinical({
                        ...clinical,
                        [field.key]: val,
                        ...(field.key === "body_temp" && val !== undefined
                          ? { body_temp_unit: "C" as const }
                          : {}),
                      });
                    }}
                    className="w-full px-2 py-1.5 text-[0.82rem] bg-sentinela-surface border border-sentinela-border rounded-lg
                               placeholder:text-sentinela-text-3 focus:outline-none focus:border-sentinela-primary/40 transition-all"
                  />
                </div>
              ))}
              <div>
                <label className="text-[0.72rem] text-sentinela-text-2">
                  Classificação Maternal Health Risk
                </label>
                <select
                  value={clinical.risk_label ?? ""}
                  onChange={(e) =>
                    setClinical({
                      ...clinical,
                      risk_label: e.target.value
                        ? (e.target.value as ClinicalData["risk_label"])
                        : undefined,
                    })
                  }
                  className="w-full px-2 py-1.5 text-[0.82rem] bg-sentinela-surface border border-sentinela-border rounded-lg
                             focus:outline-none focus:border-sentinela-primary/40 transition-all"
                >
                  <option value="">Não informado</option>
                  <option value="low risk">Baixo risco</option>
                  <option value="mid risk">Risco intermediário</option>
                  <option value="high risk">Alto risco</option>
                </select>
              </div>
              {hasClinical && (
                <button
                  onClick={() => setClinical({})}
                  className="text-[0.72rem] text-sentinela-text-3 hover:text-sentinela-danger mt-1"
                >
                  Limpar dados clínicos
                </button>
              )}
            </div>
          )}
        </div>

        {/* Action — immediately after uploads */}
        <motion.button
          whileHover={hasInput && !isProcessing ? { scale: 1.02, y: -1 } : {}}
          whileTap={hasInput && !isProcessing ? { scale: 0.98 } : {}}
          onClick={onAnalyze}
          disabled={!hasInput || isProcessing}
          className={`w-full py-3 rounded-xl font-bold text-[0.92rem] tracking-wide transition-all
            ${
              hasInput && !isProcessing
                ? "bg-sentinela-primary text-[#041016] shadow-glow hover:bg-sentinela-primary-hover"
                : "bg-sentinela-primary/40 text-white/70 cursor-not-allowed"
            }`}
        >
          <span className="flex items-center justify-center gap-2">
            <Sparkles size={16} />
            {isProcessing
              ? "Analisando evidências..."
              : hasInput
                ? "Analisar evidências"
                : "Adicione uma evidência"}
          </span>
        </motion.button>
      </div>

      {/* About */}
      <div className="px-4 pb-4 space-y-3">
        <details className="group">
          <summary className="flex items-center gap-1.5 text-[0.75rem] text-sentinela-text-3 cursor-pointer hover:text-sentinela-text-2 transition-colors">
            <Info size={12} /> Sobre o Sentinela
          </summary>
          <p className="mt-2 text-[0.78rem] text-sentinela-text-3 leading-relaxed">
            O Sentinela oferece apoio à análise e não substitui avaliação
            profissional, escuta qualificada ou protocolos institucionais de
            proteção.
            <br />
            <br />
            <span className="text-sentinela-text-3/70 text-[0.72rem]">
              POSTECH IADT · Tech Challenge Fase 4
            </span>
          </p>
        </details>
      </div>
    </aside>
  );
}
