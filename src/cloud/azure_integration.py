"""Azure integration envelope for the Tech Challenge Fase 4 demo.

The project can run fully offline for evaluation. This module records the
managed Azure services that would receive each artifact and flags whether the
current environment is only simulating the cloud step or has credentials ready
for a real adapter.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any

from src.config import AzureConfig


def config_from_env(default: AzureConfig | None = None) -> AzureConfig:
    base = default or AzureConfig()
    return AzureConfig(
        region=os.getenv("AZURE_REGION", base.region),
        cognitive_endpoint=os.getenv("AZURE_COGNITIVE_ENDPOINT", base.cognitive_endpoint or None),
        cognitive_key=os.getenv("AZURE_COGNITIVE_KEY", base.cognitive_key or None),
        storage_account=os.getenv("AZURE_STORAGE_ACCOUNT", base.storage_account or None),
        storage_container=os.getenv("AZURE_STORAGE_CONTAINER", base.storage_container),
        service_bus_namespace=os.getenv("AZURE_SERVICE_BUS_NAMESPACE", base.service_bus_namespace or None),
        service_bus_queue=os.getenv("AZURE_SERVICE_BUS_QUEUE", base.service_bus_queue),
        key_vault_name=os.getenv("AZURE_KEY_VAULT_NAME", base.key_vault_name or None),
    )


def build_azure_receipt(
    *,
    report: dict[str, Any],
    provided_modalities: list[str],
    config: AzureConfig,
    case_id: str = "demo-case",
) -> dict[str, Any]:
    level = str(report.get("level", "unknown"))
    priority = report.get("priority") or {}
    score = float(report.get("multimodal_score_0_1", 0.0))
    human_review = bool(priority.get("humanReviewRequired"))
    timestamp = datetime.now(timezone.utc).isoformat()

    configured = bool(config.cognitive_endpoint and config.cognitive_key)
    alert_required = level in {"high", "critical"} or human_review
    modality_set = sorted(set(provided_modalities))
    payload_hash = hashlib.sha256(
        f"{case_id}|{timestamp}|{level}|{score:.6f}|{','.join(modality_set)}".encode("utf-8")
    ).hexdigest()[:16]

    return {
        "provider": "azure",
        "mode": "configured" if configured else "local_simulation",
        "region": config.region,
        "case_id": case_id,
        "timestamp_utc": timestamp,
        "payload_hash": payload_hash,
        "managed_services": {
            "video": "Azure AI Vision / Custom Vision YOLOv8 artifact registry",
            "audio": "Azure AI Speech + Azure AI Language for clinical transcript signals",
            "text": "Azure AI Language safety and sentiment enrichment",
            "clinical": "Azure Health Data Services compatible clinical envelope",
            "alerts": f"Azure Service Bus queue: {config.service_bus_queue}",
            "storage": f"Azure Blob Storage container: {config.storage_container}",
        },
        "privacy_controls": [
            "LGPD data minimization",
            "pseudonymous case_id",
            "encrypted storage boundary",
            "human-in-the-loop before clinical action",
            "non-diagnostic triage language",
        ],
        "alert": {
            "required": alert_required,
            "status": "queued_for_medical_team" if alert_required else "not_required",
            "reason": "high_or_review_required" if alert_required else "routine_monitoring",
        },
        "configuration": {
            "cognitive_endpoint": "set" if config.cognitive_endpoint else "missing",
            "storage_account": "set" if config.storage_account else "missing",
            "service_bus_namespace": "set" if config.service_bus_namespace else "missing",
            "key_vault_name": "set" if config.key_vault_name else "missing",
        },
    }
