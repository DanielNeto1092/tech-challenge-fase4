from __future__ import annotations

from pathlib import Path
from typing import Any

from src.domain.types import ModalityScore, ObjectDetection


class SharpObjectDetector:
    """YOLOv8 detector for sharp/dangerous objects.

    Prefer the custom detector trained on the sharp-objects dataset. When that
    weight file is absent, fall back to YOLOv8n COCO so the prototype can still
    identify generic knife, scissors and fork classes.
    """

    def __init__(
        self,
        model_path: Path,
        conf_threshold: float = 0.5,
        risk_classes: tuple[str, ...] = (
            "Knife",
            "Cutter",
            "Scissors",
            "Ice Pick",
            "Screwdriver",
            "Peeler",
            "Fork",
        ),
        fallback_model: str | None = "yolov8n.pt",
        fallback_risk_classes: tuple[str, ...] = ("knife", "scissors", "fork"),
        fallback_conf_threshold: float = 0.25,
    ):
        self._model_path = model_path
        self._conf = conf_threshold
        self._fallback_conf = fallback_conf_threshold
        self._custom_risk_classes = {c.lower() for c in risk_classes}
        self._fallback_model = fallback_model
        self._fallback_risk_classes = {c.lower() for c in fallback_risk_classes}
        self._model = None
        self._active_model_source: str | None = None
        self._active_risk_classes: set[str] = set()

    def _load_model(self) -> None:
        if self._model is not None:
            return

        from ultralytics import YOLO

        if self._model_path.exists():
            self._model = YOLO(str(self._model_path))
            self._active_model_source = "custom_sharp_objects"
            self._active_risk_classes = self._custom_risk_classes
            return

        if not self._fallback_model:
            raise FileNotFoundError(f"model_not_found: {self._model_path}")

        self._model = YOLO(self._fallback_model)
        self._active_model_source = "coco_yolov8n_fallback"
        self._active_risk_classes = self._fallback_risk_classes

    def detect(self, source: str | Path) -> list[ObjectDetection]:
        self._load_model()
        conf = self._fallback_conf if self._active_model_source == "coco_yolov8n_fallback" else self._conf
        results = self._model.predict(source=str(source), conf=conf, verbose=False)
        detections: list[ObjectDetection] = []

        for r in results:
            if r.boxes is None:
                continue
            for i in range(len(r.boxes)):
                cls_id = int(r.boxes.cls[i])
                cls_name = str(r.names[cls_id])
                conf = float(r.boxes.conf[i])
                bbox = tuple(float(x) for x in r.boxes.xyxy[i].tolist())
                detections.append(
                    ObjectDetection(
                        class_name=cls_name,
                        confidence=conf,
                        bbox=bbox,  # type: ignore[arg-type]
                        is_risk_object=cls_name.lower() in self._active_risk_classes,
                    )
                )

        return detections

    def score(self, source: str | Path) -> ModalityScore:
        try:
            detections = self.detect(source)
        except Exception as exc:
            return ModalityScore(
                modality="objects",
                score_0_1=0.0,
                confidence_0_1=0.0,
                evidence={
                    "available": False,
                    "reason": f"model_unavailable: {exc}",
                    "custom_model_path": str(self._model_path),
                    "fallback_model": self._fallback_model,
                },
            )

        risk_dets = [d for d in detections if d.is_risk_object]
        is_fallback = self._active_model_source == "coco_yolov8n_fallback"
        base_evidence: dict[str, Any] = {
            "available": True,
            "model_source": self._active_model_source,
            "custom_model_available": self._model_path.exists(),
            "risk_classes": sorted(self._active_risk_classes),
        }
        if is_fallback:
            base_evidence["limitation"] = (
                "COCO fallback detects only generic knife, scissors and fork classes; "
                "it does not replace the custom sharp-object detector."
            )

        if not risk_dets:
            return ModalityScore(
                modality="objects",
                score_0_1=0.0,
                confidence_0_1=0.65 if is_fallback else 0.9,
                evidence={
                    **base_evidence,
                    "total_detections": len(detections),
                    "risk_detections": 0,
                    "objects": [],
                },
            )

        max_conf = max(d.confidence for d in risk_dets)
        count_factor = min(1.0, len(risk_dets) / 3.0)
        raw_score = 0.7 * max_conf + 0.3 * count_factor
        confidence = max_conf * (0.85 if is_fallback else 1.0)

        return ModalityScore(
            modality="objects",
            score_0_1=round(max(0.0, min(1.0, raw_score)), 3),
            confidence_0_1=round(max(0.0, min(1.0, confidence)), 3),
            evidence={
                **base_evidence,
                "total_detections": len(detections),
                "risk_detections": len(risk_dets),
                "objects": [
                    {"class": d.class_name, "conf": round(d.confidence, 3)}
                    for d in risk_dets[:10]
                ],
            },
        )
