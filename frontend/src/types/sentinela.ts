export interface ModalityScore {
  score_0_1: number;
  evidence?: Record<string, unknown>;
}

export interface CareAssessment {
  carePathway?: string;
  dimensions?: Record<string, number>;
  reviewFocus?: string[];
  guardrails?: string[];
}

export interface Priority {
  riskLevel?: string;
  confidence?: number;
  humanReviewRequired?: boolean;
}

export interface TraceStage {
  stage: string;
  elapsed_ms: number;
}

export interface Trace {
  request_id?: string;
  total_ms?: number;
  stages?: TraceStage[];
}

export interface AzureIntegration {
  provider?: string;
  mode?: string;
  region?: string;
  case_id?: string;
  payload_hash?: string;
  managed_services?: Record<string, string>;
  privacy_controls?: string[];
  alert?: {
    required?: boolean;
    status?: string;
    reason?: string;
  };
  configuration?: Record<string, string>;
}

export interface ClinicalData {
  age?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  blood_sugar?: number;
  body_temp?: number;
  body_temp_unit?: "C" | "F";
  heart_rate?: number;
  baseline_fhr?: number;
  nsp_class?: number;
  risk_label?: "low risk" | "mid risk" | "high risk";
}

export interface SentinelaReport {
  level: "low" | "medium" | "high" | "critical";
  multimodal_score_0_1: number;
  priority: Priority;
  care_assessment?: CareAssessment;
  modality_scores: Record<string, ModalityScore>;
  metadata?: {
    missing?: string[];
    unavailable?: Record<string, string>;
  };
  weights?: Record<string, number>;
  _trace?: Trace;
  _warnings?: string[];
  _api_elapsed_s?: number;
  _azure_integration?: AzureIntegration;
  _video_processing?: Record<string, string | number | boolean>;
}

export type AnalysisState =
  | "idle"
  | "uploading"
  | "processing"
  | "done"
  | "error";

export interface Signal {
  signal: string;
  value: number;
  detail?: string;
}

export interface TimelineEvent {
  time: string;
  text: string;
  severity: "info" | "warning" | "critical";
}
