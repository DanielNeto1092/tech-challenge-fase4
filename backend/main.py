"""Sentinela AI — FastAPI Backend.

Wraps SentinelaPipeline for the React frontend.
Run with: uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to sys.path so src.pipeline is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.cloud import build_azure_receipt, config_from_env  # noqa: E402
from src.extractors.clinical import ClinicalExtractor  # noqa: E402
from src.pipeline import SentinelaPipeline  # noqa: E402

logger = logging.getLogger("sentinela.api")

POSE_MODEL_PATH = PROJECT_ROOT / "models" / "yolov8n-pose.pt"
POSE_MODEL_FALLBACK = "yolov8n-pose.pt"
POSE_MAX_FRAMES = 10
PYTHON_EXE = sys.executable

app = FastAPI(title="Sentinela AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pose extraction (runs in subprocess to avoid YOLO/cv2 threading deadlock) ──
def _extract_keypoints(video_path: Path, output_json: Path, max_frames: int = POSE_MAX_FRAMES) -> dict:
    """Run YOLOv8n-Pose in a subprocess and return keypoints dict + metadata."""
    pose_model = str(POSE_MODEL_PATH) if POSE_MODEL_PATH.exists() else POSE_MODEL_FALLBACK

    script = f'''
import json, sys, cv2, numpy as np
from pathlib import Path
from ultralytics import YOLO

cv2.setNumThreads(0)
video_path = Path(r"{video_path}")
model_ref = r"{pose_model}"
max_frames = {max_frames}
output_path = Path(r"{output_json}")

model = YOLO(model_ref)
cap = cv2.VideoCapture(str(video_path))
if not cap.isOpened():
    print(json.dumps({{"error": "cannot open video"}}))
    sys.exit(1)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
fps = cap.get(cv2.CAP_PROP_FPS) or 0
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
indices = np.linspace(0, max(0, total_frames - 1), num=min(max_frames, max(1, total_frames)), dtype=int)

all_keypoints = {{}}
for i, frame_idx in enumerate(indices):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
    ok, frame = cap.read()
    if not ok or frame is None:
        continue
    results = model.predict(source=frame, conf=0.3, verbose=False)
    frame_detections = []
    for r in results:
        if r.keypoints is None:
            continue
        for person_idx in range(len(r.keypoints)):
            kpts = r.keypoints[person_idx].data[0]
            keypoints_list = [[float(kpts[j][0]), float(kpts[j][1]), float(kpts[j][2])] for j in range(17)]
            frame_detections.append({{"keypoints": keypoints_list}})
    if frame_detections:
        all_keypoints[str(i)] = frame_detections
cap.release()

output_path.write_text(json.dumps(all_keypoints), encoding="utf-8")
meta = {{
    "pose_model": model_ref,
    "pose_model_source": "local" if Path(model_ref).exists() else "ultralytics_cache",
    "source_video": video_path.name,
    "total_frames": total_frames,
    "fps": round(fps, 1),
    "resolution": f"{{width}}x{{height}}",
    "frames_sampled": len(indices),
    "frames_with_person": len(all_keypoints),
}}
print(json.dumps(meta))
'''
    result = subprocess.run(
        [PYTHON_EXE, "-c", script],
        capture_output=True, text=True, timeout=120,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Pose extraction failed: {result.stderr[-500:]}")

    meta = json.loads(result.stdout.strip().split("\n")[-1])
    return meta


@app.get("/health")
def health():
    return {"status": "ok", "service": "sentinela-ai", "version": "2.0.0"}


@app.post("/analyze")
async def analyze(
    transcript: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    clinical_json: Optional[str] = Form(None),
):
    tmpdir = Path(tempfile.mkdtemp(prefix="sentinela_api_"))
    kwargs: dict = {}
    video_meta: dict | None = None
    provided_modalities: list[str] = []

    if transcript and transcript.strip():
        txt_path = tmpdir / "transcript.txt"
        txt_path.write_text(transcript.strip(), encoding="utf-8")
        kwargs["transcript"] = txt_path
        provided_modalities.append("text")

    if audio and audio.filename:
        audio_path = tmpdir / audio.filename
        audio_path.write_bytes(await audio.read())
        kwargs["audio_wav"] = audio_path
        provided_modalities.append("audio")

    if video and video.filename:
        video_path = tmpdir / video.filename
        video_path.write_bytes(await video.read())
        kwargs["video_file"] = video_path
        provided_modalities.append("video")

        # Extract keypoints with YOLOv8n-Pose for real pose analysis (subprocess)
        try:
            kp_json_path = tmpdir / "pose_keypoints.json"
            video_meta = _extract_keypoints(video_path, kp_json_path)
            kwargs["pose_json"] = kp_json_path
        except FileNotFoundError as e:
            return JSONResponse(status_code=500, content={"error": str(e)})
        except Exception as e:
            logger.warning("Pose extraction failed, continuing with visual-only: %s", e)
            video_meta = {"pose_extraction_error": str(e)}

    if image and image.filename:
        image_path = tmpdir / image.filename
        image_path.write_bytes(await image.read())
        kwargs["image_for_objects"] = image_path
        provided_modalities.append("objects")

    # Clinical / obstetric data
    if clinical_json and clinical_json.strip():
        try:
            cdata = json.loads(clinical_json)
            kwargs["clinical_data"] = ClinicalExtractor.from_mapping(cdata)
            provided_modalities.append("clinical")
        except (json.JSONDecodeError, TypeError, KeyError):
            return JSONResponse(
                status_code=400,
                content={"error": "Dados clínicos inválidos. Envie JSON com campos numéricos."},
            )

    if not kwargs:
        return JSONResponse(
            status_code=400,
            content={"error": "Nenhuma evidência fornecida. Envie pelo menos uma modalidade."},
        )

    try:
        pipeline = SentinelaPipeline()
        t0 = time.perf_counter()
        report = pipeline.analyze(**kwargs)
        elapsed = time.perf_counter() - t0
        report["_api_elapsed_s"] = round(elapsed, 3)

        # Attach video processing metadata for traceability
        if video_meta:
            report["_video_processing"] = video_meta
        report["_azure_integration"] = build_azure_receipt(
            report=report,
            provided_modalities=provided_modalities,
            config=config_from_env(pipeline._cfg.azure),
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    return _serialize(report)


def _serialize(obj):
    """Make report JSON-serializable (convert Path objects etc)."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj
