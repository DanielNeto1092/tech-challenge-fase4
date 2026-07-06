const $ = (id) => document.getElementById(id);

let currentReportName = null;

function pct(value) {
  if (typeof value !== "number") return "--";
  return `${(value * 100).toFixed(1)}%`;
}

function compactPath(value) {
  return value && value.trim() ? value.trim() : null;
}

function setStatus(text) {
  $("status").textContent = text;
}

function payloadFromForm() {
  return {
    transcript: compactPath($("transcript").value),
    audio_wav: compactPath($("audio_wav").value),
    pose_json: compactPath($("pose_json").value),
    video_file: compactPath($("video_file").value),
    frames_dir: compactPath($("frames_dir").value),
    sequence: compactPath($("sequence").value),
    motion_calibration: compactPath($("motion_calibration").value),
    save_as: compactPath($("save_as").value) || "dashboard_case",
  };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || response.statusText);
  }
  return response.json();
}

function renderReport(report) {
  const priority = report.priority || {};
  const care = report.care_assessment || {};
  const dims = care.dimensions || {};
  const modalities = report.modality_scores || {};

  $("score").textContent = pct(report.multimodal_score_0_1);
  $("riskLevel").textContent = priority.riskLevel || "--";
  $("carePathway").textContent = care.carePathwayLabel || care.carePathway || "--";

  $("wellbeing").value = dims.wellbeingIndex || 0;
  $("distress").value = dims.affectiveDistress || 0;
  $("safety").value = dims.safetySignal || 0;
  $("quality").value = dims.dataQuality || 0;

  const chips = Object.entries(modalities).map(([name, item]) => {
    let extra = "";
    if (name === "audio") {
      const emotion = item.evidence?.emotion_baseline;
      if (emotion?.available) {
        extra = ` · ${emotion.predictedEmotion} ${pct(emotion.confidence)}`;
      }
    }
    if (name === "video") {
      const visual = item.evidence?.visual_wellbeing;
      if (visual?.available) {
        extra = ` · strain ${pct(visual.visualStrain)}`;
      }
    }
    return `<span class="chip">${name}: ${pct(item.score_0_1)}${extra}</span>`;
  });
  $("modalities").innerHTML = chips.join("");

  const focus = care.reviewFocus || [];
  $("reviewFocus").innerHTML = focus.map((item) => `<li>${item}</li>`).join("");

  const nextSteps = care.nextSteps || [];
  $("nextSteps").innerHTML = nextSteps.map((item) => `<li>${item}</li>`).join("");

  const questions = care.suggestedQuestions || [];
  $("suggestedQuestions").innerHTML = questions.map((item) => `<li>${item}</li>`).join("");

  const privacy = care.privacyChecklist || [];
  $("privacyChecklist").innerHTML = privacy.map((item) => `<li>${item}</li>`).join("");
}

async function loadReports() {
  const data = await api("/api/reports");
  const select = $("reportSelect");
  select.innerHTML = "";
  for (const item of data.reports) {
    const option = document.createElement("option");
    option.value = item.name;
    option.textContent = `${item.name} · ${item.riskLevel || item.level || "--"}`;
    select.appendChild(option);
  }
  if (data.reports.length) {
    currentReportName = data.reports[0].name;
    select.value = currentReportName;
    await loadReport(currentReportName);
  }
}

async function loadReport(name) {
  if (!name) return;
  currentReportName = name;
  const report = await api(`/api/report/${encodeURIComponent(name)}`);
  renderReport(report);
}

async function analyze() {
  setStatus("Analisando...");
  const report = await api("/api/analyze", {
    method: "POST",
    body: JSON.stringify(payloadFromForm()),
  });
  renderReport(report);
  await loadReports();
  const saved = report._savedReport || "relatório salvo";
  setStatus(`Concluído: ${saved}`);
}

async function saveReview() {
  if (!currentReportName) return;
  const payload = {
    status: $("reviewStatus").value,
    notes: $("reviewNotes").value,
    reviewer: "dashboard",
  };
  await api(`/api/report/${encodeURIComponent(currentReportName)}/review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  $("reviewNotes").value = "";
  setStatus("Revisão registrada.");
}

$("analyzeBtn").addEventListener("click", () => {
  analyze().catch((error) => setStatus(`Erro: ${error.message}`));
});

$("videoExampleBtn").addEventListener("click", () => {
  $("transcript").value = "";
  $("audio_wav").value = "";
  $("pose_json").value = "";
  $("video_file").value = "";
  $("frames_dir").value = "archive/Test/Abuse";
  $("sequence").value = "Abuse030_x264";
  $("motion_calibration").value = "data/motion_calibration.json";
  $("save_as").value = "dashboard_video_motion";
});

$("daiseeExampleBtn").addEventListener("click", () => {
  $("transcript").value = "";
  $("audio_wav").value = "";
  $("pose_json").value = "";
  $("video_file").value = "archive/DAiSEE/DataSet/Test/500044/5000441001/5000441001.avi";
  $("frames_dir").value = "";
  $("sequence").value = "";
  $("motion_calibration").value = "";
  $("save_as").value = "dashboard_daisee_visual";
});

$("refreshReports").addEventListener("click", () => {
  loadReports().catch((error) => setStatus(`Erro: ${error.message}`));
});

$("reportSelect").addEventListener("change", (event) => {
  loadReport(event.target.value).catch((error) => setStatus(`Erro: ${error.message}`));
});

$("saveReview").addEventListener("click", () => {
  saveReview().catch((error) => setStatus(`Erro: ${error.message}`));
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tabPane").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.tab).classList.add("active");
  });
});

loadReports().catch((error) => setStatus(`Erro: ${error.message}`));
