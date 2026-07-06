"""Structured JSON logging for pipeline observability."""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Generator


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_fields"):
            entry.update(record.extra_fields)
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = str(record.exc_info[1])
        return json.dumps(entry, ensure_ascii=False, default=str)


def get_logger(name: str = "sentinela") -> logging.Logger:
    """Return a logger with JSON formatting on stderr."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_extra(logger: logging.Logger, level: int, message: str, **fields: Any) -> None:
    """Emit a structured log entry with extra fields."""
    record = logger.makeRecord(
        logger.name, level, "(sentinela)", 0, message, (), None,
    )
    record.extra_fields = fields  # type: ignore[attr-defined]
    logger.handle(record)


class PipelineTracer:
    """Traces a pipeline run with request_id, stage timings, and modality coverage."""

    def __init__(self, request_id: str | None = None) -> None:
        self.request_id = request_id or uuid.uuid4().hex[:12]
        self.stages: list[dict[str, Any]] = []
        self._start = time.perf_counter()
        self._logger = get_logger("sentinela.pipeline")

    @contextmanager
    def stage(self, name: str) -> Generator[None, None, None]:
        """Context manager that times a named pipeline stage."""
        t0 = time.perf_counter()
        log_extra(self._logger, logging.INFO, f"stage_start: {name}",
                  request_id=self.request_id, stage=name)
        try:
            yield
        except Exception:
            log_extra(self._logger, logging.ERROR, f"stage_error: {name}",
                      request_id=self.request_id, stage=name,
                      elapsed_ms=round((time.perf_counter() - t0) * 1000, 1))
            raise
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        self.stages.append({"stage": name, "elapsed_ms": elapsed})
        log_extra(self._logger, logging.INFO, f"stage_done: {name}",
                  request_id=self.request_id, stage=name, elapsed_ms=elapsed)

    def summary(self, modalities: list[str], score: float, level: str) -> dict[str, Any]:
        """Return a structured summary of the pipeline run."""
        total = round((time.perf_counter() - self._start) * 1000, 1)
        result = {
            "request_id": self.request_id,
            "total_ms": total,
            "stages": self.stages,
            "modalities": modalities,
            "modality_count": len(modalities),
            "score": score,
            "level": level,
        }
        log_extra(self._logger, logging.INFO, "pipeline_complete",
                  request_id=self.request_id, total_ms=total,
                  modality_count=len(modalities), score=score, risk_level=level)
        return result
