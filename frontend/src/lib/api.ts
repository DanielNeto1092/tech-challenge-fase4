import type { SentinelaReport, ClinicalData } from "@/types/sentinela";

const API_BASE = "http://127.0.0.1:8000";

export async function analyzeCase(data: {
  transcript?: string;
  audio?: File;
  video?: File;
  image?: File;
  clinical?: ClinicalData;
}): Promise<SentinelaReport> {
  const form = new FormData();

  if (data.transcript?.trim()) {
    form.append("transcript", data.transcript.trim());
  }
  if (data.audio) {
    form.append("audio", data.audio);
  }
  if (data.video) {
    form.append("video", data.video);
  }
  if (data.image) {
    form.append("image", data.image);
  }
  if (data.clinical && Object.values(data.clinical).some((v) => v != null)) {
    form.append("clinical_json", JSON.stringify(data.clinical));
  }

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Erro desconhecido" }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
