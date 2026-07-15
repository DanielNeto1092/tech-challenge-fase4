"""FastAPI application for Sentinela AI."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.cloud import build_azure_receipt, config_from_env
from src.config import PROJECT_ROOT, PipelineConfig
from src.extractors.clinical import ClinicalExtractor
from src.pipeline import SentinelaPipeline

RESULTS_DIR = PROJECT_ROOT / "data" / "results"
STATIC_DIR = Path(__file__).resolve().parent / "static"

pipeline = SentinelaPipeline(PipelineConfig())
app = FastAPI(title="Sentinela AI", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AnalyzeRequest(BaseModel):
    transcript: str | None = None
    audio_wav: str | None = None
    pose_json: str | None = None
    video_file: str | None = None
    frames_dir: str | None = None
    sequence: str | None = None
    motion_calibration: str | None = None
    image_for_objects: str | None = None
    max_frames: int | None = None
    clinical_data: dict[str, Any] | None = None
    clinical_series_data: list[dict[str, Any]] | None = None
    prescriptions: list[dict[str, Any]] | None = None
    save_as: str | None = None


class ReviewRequest(BaseModel):
    reviewer: str = "human_reviewer"
    status: str = Field(pattern="^(PENDING|CONFIRMED|DISMISSED|ESCALATED)$")
    notes: str = ""


def _resolve(v: str | None) -> str | None:
    if not v:
        return None
    p = Path(v)
    return str(p if p.is_absolute() else PROJECT_ROOT / p)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "Sentinela AI", "version": "2.0.0"}


@app.post("/api/analyze")
def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    clinical_data = ClinicalExtractor.from_mapping(payload.clinical_data) if payload.clinical_data else None
    clinical_series_data = payload.clinical_series_data
    prescriptions = payload.prescriptions
    if payload.clinical_data:
        clinical_series_data = clinical_series_data or payload.clinical_data.get("vital_series") or payload.clinical_data.get("clinical_series") or payload.clinical_data.get("readings")
        prescriptions = prescriptions or payload.clinical_data.get("prescriptions")
    provided_modalities = [
        name
        for name, present in {
            "text": bool(payload.transcript),
            "audio": bool(payload.audio_wav),
            "video": bool(payload.pose_json or payload.video_file or payload.frames_dir),
            "objects": bool(payload.image_for_objects),
            "clinical": clinical_data is not None or bool(clinical_series_data) or bool(prescriptions),
        }.items()
        if present
    ]
    try:
        report = pipeline.analyze(
            transcript=_resolve(payload.transcript),
            audio_wav=_resolve(payload.audio_wav),
            pose_json=_resolve(payload.pose_json),
            video_file=_resolve(payload.video_file),
            frames_dir=_resolve(payload.frames_dir),
            sequence=payload.sequence,
            motion_calibration=_resolve(payload.motion_calibration),
            image_for_objects=_resolve(payload.image_for_objects),
            max_frames=payload.max_frames,
            clinical_data=clinical_data,
            clinical_series_data=clinical_series_data,
            prescriptions=prescriptions,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    report["_azure_integration"] = build_azure_receipt(
        report=report,
        provided_modalities=provided_modalities,
        config=config_from_env(pipeline._cfg.azure),
    )

    stem = payload.save_as or f"case_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)
    out = pipeline.write_report(report, RESULTS_DIR / f"{safe}.json")
    report["_savedReport"] = out.relative_to(PROJECT_ROOT).as_posix()
    return report


@app.get("/api/reports")
def reports() -> dict[str, Any]:
    if not RESULTS_DIR.exists():
        return {"reports": []}
    items = []
    for p in sorted(RESULTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        items.append({
            "name": p.stem,
            "score": data.get("multimodal_score_0_1"),
            "level": data.get("level"),
            "riskLevel": (data.get("priority") or {}).get("riskLevel"),
            "carePathway": (data.get("care_assessment") or {}).get("carePathway"),
        })
    return {"reports": items}


@app.get("/api/report/{name}")
def report(name: str) -> dict[str, Any]:
    path = RESULTS_DIR / f"{Path(name).stem}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/report/{name}/review")
def review(name: str, payload: ReviewRequest) -> dict[str, Any]:
    path = RESULTS_DIR / f"{Path(name).stem}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    audit = data.setdefault("human_review", [])
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "reviewer": payload.reviewer, "status": payload.status, "notes": payload.notes}
    audit.append(entry)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "review": entry}
