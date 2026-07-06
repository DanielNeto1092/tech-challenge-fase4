import { useState, useRef, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

import Sidebar from "./components/Sidebar";
import Hero from "./components/Hero";
import FlowSteps from "./components/FlowSteps";
import CapabilityCards from "./components/CapabilityCards";
import RadarProfile from "./components/RadarProfile";
import ProcessingState from "./components/ProcessingState";
import RiskHero from "./components/RiskHero";
import ExplainabilityPanel from "./components/ExplainabilityPanel";
import ModalityCards from "./components/ModalityCards";
import EvidenceTimeline from "./components/EvidenceTimeline";
import CarePathway from "./components/CarePathway";
import Limitations from "./components/Limitations";

import { analyzeCase } from "./lib/api";
import { LEVEL_LABELS, PATHWAY_LABELS, buildSignals } from "./lib/utils";
import type { SentinelaReport, AnalysisState, ClinicalData } from "./types/sentinela";

export default function App() {
  const [state, setState] = useState<AnalysisState>("idle");
  const [report, setReport] = useState<SentinelaReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingStage, setProcessingStage] = useState(0);
  const stageInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // Lifted evidence state
  const [transcript, setTranscript] = useState("");
  const [audio, setAudio] = useState<File | null>(null);
  const [video, setVideo] = useState<File | null>(null);
  const [image, setImage] = useState<File | null>(null);
  const [clinical, setClinical] = useState<ClinicalData>({});

  const hasClinical = Object.values(clinical).some(
    (v) => v != null && v !== "",
  );
  const hasInput = !!(
    transcript.trim() ||
    audio ||
    video ||
    image ||
    hasClinical
  );

  const handleAnalyze = useCallback(async () => {
    if (!hasInput) return;
    setState("uploading");
    setError(null);
    setReport(null);
    setProcessingStage(0);

    stageInterval.current = setInterval(() => {
      setProcessingStage((p) => Math.min(p + 1, 7));
    }, 800);

    setState("processing");

    try {
      const result = await analyzeCase({
        transcript: transcript.trim() || undefined,
        audio: audio || undefined,
        video: video || undefined,
        image: image || undefined,
        clinical: hasClinical ? clinical : undefined,
      });
      setReport(result);
      setState("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido");
      setState("error");
    } finally {
      if (stageInterval.current) {
        clearInterval(stageInterval.current);
        stageInterval.current = null;
      }
    }
  }, [hasInput, transcript, audio, video, image, clinical, hasClinical]);

  useEffect(() => {
    return () => {
      if (stageInterval.current) clearInterval(stageInterval.current);
    };
  }, []);

  const isProcessing = state === "uploading" || state === "processing";

  return (
    <div className="flex min-h-screen">
      <Sidebar
        transcript={transcript}
        setTranscript={setTranscript}
        audio={audio}
        setAudio={setAudio}
        video={video}
        setVideo={setVideo}
        image={image}
        setImage={setImage}
        clinical={clinical}
        setClinical={setClinical}
        onAnalyze={handleAnalyze}
        isProcessing={isProcessing}
      />

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[960px] mx-auto px-6 py-4">
          <AnimatePresence mode="wait">
            {state === "idle" && (
              <IdleView
                key="idle"
                hasTranscript={!!transcript.trim()}
                hasAudio={!!audio}
                hasVideo={!!video}
                hasImage={!!image}
                hasClinical={hasClinical}
              />
            )}
            {(state === "uploading" || state === "processing") && (
              <ProcessingState key="processing" stage={processingStage} />
            )}
            {state === "error" && (
              <ErrorView
                key="error"
                error={error}
                onRetry={() => setState("idle")}
              />
            )}
            {state === "done" && report && (
              <ResultsView key="results" report={report} />
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

/* ─── Idle View ──────────────────────────────────────────────────────── */
interface IdleViewProps {
  hasTranscript: boolean;
  hasAudio: boolean;
  hasVideo: boolean;
  hasImage: boolean;
  hasClinical: boolean;
}

function IdleView({
  hasTranscript,
  hasAudio,
  hasVideo,
  hasImage,
  hasClinical,
}: IdleViewProps) {
  const hasAny =
    hasTranscript || hasAudio || hasVideo || hasImage || hasClinical;

  const evidences = [
    { label: "Relato", added: hasTranscript },
    { label: "Áudio", added: hasAudio },
    { label: "Vídeo", added: hasVideo },
    { label: "Imagem", added: hasImage },
    { label: "Clínico", added: hasClinical },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Hero />
      <FlowSteps />
      <CapabilityCards />

      <div className="grid grid-cols-[1.4fr_1fr] gap-4 mt-4">
        {/* Evidence Status Card */}
        <div className="bg-sentinela-surface border border-sentinela-border rounded-xl p-5">
          <h3 className="font-serif text-[1.1rem] text-sentinela-text mb-1">
            {hasAny ? "Evidências recebidas" : "Aguardando evidências"}
          </h3>
          <p className="text-[0.85rem] text-sentinela-text-2 leading-relaxed mb-4">
            {hasAny
              ? "A análise será baseada nas fontes adicionadas. Você pode complementar com outras modalidades antes de continuar."
              : "Adicione um relato, áudio, vídeo, imagem ou dados clínicos para iniciar a análise. O Sentinela usará apenas as fontes disponíveis."}
          </p>
          <div className="grid grid-cols-2 gap-2">
            {evidences.map((ev) => (
              <div
                key={ev.label}
                className={`flex items-center gap-2 px-3 py-2 border rounded-lg ${
                  ev.added
                    ? "bg-sentinela-primary/5 border-sentinela-primary/20"
                    : "bg-sentinela-elevated border-sentinela-border"
                }`}
              >
                {ev.added ? (
                  <span className="text-sentinela-primary font-bold text-[0.82rem]">
                    ✓
                  </span>
                ) : (
                  <span className="text-sentinela-text-3 text-[0.82rem]">○</span>
                )}
                <span
                  className={`text-[0.85rem] ${ev.added ? "text-sentinela-text font-medium" : "text-sentinela-text-3"}`}
                >
                  {ev.label}
                </span>
                <span
                  className={`ml-auto text-[0.7rem] ${ev.added ? "text-sentinela-primary" : "text-sentinela-text-3"}`}
                >
                  {ev.added ? "adicionado" : "pendente"}
                </span>
              </div>
            ))}
          </div>
        </div>

        <RadarProfile demo />
      </div>

      {/* How it works */}
      <details className="mt-4 group bg-sentinela-surface border border-sentinela-border rounded-xl">
        <summary className="px-5 py-3 text-[0.88rem] font-medium text-sentinela-text-2 cursor-pointer flex items-center gap-2 hover:text-sentinela-text transition-colors">
          <ChevronDown
            size={16}
            className="group-open:rotate-180 transition-transform"
          />
          Como a análise é feita
        </summary>
        <div className="px-5 pb-4 text-[0.85rem] text-sentinela-text-3 leading-relaxed space-y-2">
          <p>
            <strong className="text-sentinela-text-2">Texto</strong> — NLP em
            português com detecção multi-label de sinais de risco
          </p>
          <p>
            <strong className="text-sentinela-text-2">Áudio</strong> — Extração de
            features acústicas + classificação emocional
          </p>
          <p>
            <strong className="text-sentinela-text-2">Vídeo</strong> — Estimação de
            postura, movimento corporal e bem-estar visual
          </p>
          <p>
            <strong className="text-sentinela-text-2">Objetos</strong> — Detecção
            de objetos cortantes via YOLOv8
          </p>
          <p>
            <strong className="text-sentinela-text-2">Clínico</strong> — Avaliação
            de risco obstétrico via sinais vitais (CTG, pressão, glicose)
          </p>
          <p className="pt-2 border-t border-sentinela-border">
            Fusão tardia de 5 modalidades com normalização ponderada por
            confiança. Motor de cuidado trauma-informado com 4 trilhas e
            guardrails éticos.
          </p>
        </div>
      </details>
    </motion.div>
  );
}

/* ─── Error View ─────────────────────────────────────────────────────── */
function ErrorView({
  error,
  onRetry,
}: {
  error: string | null;
  onRetry: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="max-w-md mx-auto my-16 text-center"
    >
      <div className="bg-sentinela-danger/8 border border-sentinela-danger/15 rounded-xl p-6">
        <p className="text-[1rem] font-semibold text-sentinela-danger mb-2">
          Erro na análise
        </p>
        <p className="text-[0.88rem] text-sentinela-text-2 mb-4">{error}</p>
        <button
          onClick={onRetry}
          className="px-5 py-2 bg-sentinela-primary text-white rounded-lg text-[0.88rem] font-semibold
                     hover:bg-sentinela-primary-hover transition-colors"
        >
          Tentar novamente
        </button>
      </div>
    </motion.div>
  );
}

/* ─── Results View ───────────────────────────────────────────────────── */
function ResultsView({ report }: { report: SentinelaReport }) {
  const warnings = report._warnings || [];
  const isPartial = Object.keys(report.modality_scores || {}).length < 5;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-5 pb-8"
    >
      {/* Warnings */}
      {warnings.map((w, i) => (
        <div
          key={i}
          className="bg-sentinela-danger/5 border border-sentinela-danger/12 rounded-xl px-5 py-3 text-[0.85rem] text-sentinela-danger"
        >
          <strong>Modalidade indisponível</strong> — {w}
        </div>
      ))}

      {/* Risk Hero */}
      <RiskHero report={report} />

      {/* Partial notice */}
      {isPartial && (
        <div className="bg-sentinela-warning/6 border border-sentinela-warning/15 rounded-xl px-5 py-3">
          <p className="text-[0.85rem] text-sentinela-warning font-semibold">
            Análise parcial — {Object.keys(report.modality_scores).length} de 5
            modalidades disponíveis.
          </p>
          <p className="text-[0.82rem] text-sentinela-text-2 mt-0.5">
            Adicione modalidades complementares para maior confiança.
          </p>
        </div>
      )}

      {/* Section Label */}
      <SectionLabel>Análise Detalhada</SectionLabel>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-4">
          <ExplainabilityPanel report={report} />
          <ModalityCards report={report} />
        </div>
        <div className="space-y-4">
          <RadarProfile report={report} />
          <EvidenceTimeline report={report} />
        </div>
      </div>

      {/* Care Pathway */}
      <SectionLabel>Recomendação de Cuidado</SectionLabel>
      <CarePathway report={report} />

      {/* AI Assessment */}
      <SectionLabel>Avaliação da IA</SectionLabel>
      <div className="bg-sentinela-surface border border-sentinela-border rounded-xl p-5">
        <div
          className="text-[0.88rem] text-sentinela-text-2 leading-relaxed space-y-2"
          dangerouslySetInnerHTML={{ __html: generateExecutiveSummary(report) }}
        />
      </div>

      {/* Limitations */}
      <Limitations />

      {/* Technical */}
      <details className="group bg-sentinela-surface border border-sentinela-border rounded-xl">
        <summary className="px-5 py-3 text-[0.82rem] font-medium text-sentinela-text-3 cursor-pointer flex items-center gap-2">
          <ChevronDown
            size={14}
            className="group-open:rotate-180 transition-transform"
          />
          Trace do Pipeline
        </summary>
        <div className="px-5 pb-4 text-[0.78rem] font-mono text-sentinela-text-3 space-y-1">
          <p>
            Request: {report._trace?.request_id || "N/A"} ·{" "}
            {(report._trace?.total_ms || 0).toFixed(1)}ms ·{" "}
            {report._trace?.stages?.length || 0} etapas
          </p>
          {report._trace?.stages?.map((s, i) => (
            <p key={i}>
              ✓ {s.stage} — {s.elapsed_ms.toFixed(1)}ms
            </p>
          ))}
          {report._video_processing && (
            <div className="mt-2 pt-2 border-t border-sentinela-border">
              <p className="font-semibold text-sentinela-text-2 mb-1">Processamento de Vídeo</p>
              {Object.entries(report._video_processing).map(([k, v]) => (
                <p key={k}>
                  {k}: {String(v)}
                </p>
              ))}
            </div>
          )}
          {report._azure_integration && (
            <div className="mt-2 pt-2 border-t border-sentinela-border">
              <p className="font-semibold text-sentinela-text-2 mb-1">
                Integração Azure
              </p>
              <p>
                mode: {report._azure_integration.mode} · region:{" "}
                {report._azure_integration.region}
              </p>
              <p>
                alert: {report._azure_integration.alert?.status || "N/A"} ·
                hash: {report._azure_integration.payload_hash}
              </p>
              {Object.entries(
                report._azure_integration.managed_services || {},
              ).map(([k, v]) => (
                <p key={k}>
                  {k}: {v}
                </p>
              ))}
            </div>
          )}
        </div>
      </details>

      <details className="group bg-sentinela-surface border border-sentinela-border rounded-xl">
        <summary className="px-5 py-3 text-[0.82rem] font-medium text-sentinela-text-3 cursor-pointer flex items-center gap-2">
          <ChevronDown
            size={14}
            className="group-open:rotate-180 transition-transform"
          />
          JSON Completo
        </summary>
        <pre className="px-5 pb-4 text-[0.72rem] font-mono text-sentinela-text-3 overflow-x-auto max-h-[400px] overflow-y-auto">
          {JSON.stringify(report, null, 2)}
        </pre>
      </details>
    </motion.div>
  );
}

/* ─── Helpers ────────────────────────────────────────────────────────── */
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[0.72rem] uppercase tracking-[2px] font-bold text-sentinela-text-3 border-b border-sentinela-border pb-2 mt-6">
      {children}
    </p>
  );
}

function generateExecutiveSummary(report: SentinelaReport): string {
  const level = report.level || "low";
  const score = report.multimodal_score_0_1 || 0;
  const mods = Object.keys(report.modality_scores || {});
  const unavailable = report.metadata?.unavailable || {};
  const desc: Record<string, string> = {
    low: "Perfil de baixo risco",
    medium: "Indicadores moderados de distress",
    high: "Indicadores elevados de risco",
    critical: "Perfil de risco crítico",
  };
  const modLabel = mods.length === 1 ? "modalidade" : "modalidades";
  const parts: string[] = [];

  if (unavailable.objects) {
    parts.push(
      `<strong>Análise inconclusiva</strong>: a evidência de imagem foi enviada, mas o detector de objetos não está disponível. Resultado calculado com ${mods.length} ${modLabel} (score de fusão: ${score.toFixed(3)}).`,
    );
  } else {
    parts.push(
      `<strong>${desc[level] || "Desconhecido"}</strong> detectado em ${mods.length} ${modLabel} (score de fusão: ${score.toFixed(3)}).`,
    );
  }

  const signals = buildSignals(report);
  if (signals.length > 0) {
    const top = signals
      .slice(0, 3)
      .map((s) => `${s.signal} (+${s.value.toFixed(3)})`)
      .join(" · ");
    parts.push(`Sinais principais: ${top}.`);
  }

  const pw = report.care_assessment?.carePathway;
  if (pw) {
    parts.push(
      `Trilha recomendada: <strong>${PATHWAY_LABELS[pw] || pw}</strong>.`,
    );
  }

  if (report.priority?.humanReviewRequired) {
    parts.push("Avaliação assistida por profissional recomendada.");
  } else {
    parts.push("Continuar monitoramento de rotina.");
  }

  if (report._azure_integration?.alert?.required) {
    parts.push("Alerta técnico preparado para a fila clínica no Azure.");
  }

  return parts.map((p) => `<p>${p}</p>`).join("");
}
