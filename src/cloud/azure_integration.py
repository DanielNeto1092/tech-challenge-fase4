"""Azure integration for the Tech Challenge Fase 4 demo.

The project can run offline, but this module also contains real REST adapters
for Azure AI Speech, Azure AI Language and Azure Service Bus. When credentials
are absent, callers receive an explicit local_simulation receipt.
"""
from __future__ import annotations

import base64
import hmac
import hashlib
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
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
        service_bus_connection_string=os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING", base.service_bus_connection_string or None),
        key_vault_name=os.getenv("AZURE_KEY_VAULT_NAME", base.key_vault_name or None),
    )


@dataclass(frozen=True)
class AzureCognitiveAdapter:
    """Small REST adapter for Azure Speech and Language.

    It avoids SDK-specific dependencies and keeps the integration demonstrable
    with only httpx. The adapter is considered enabled when both endpoint and
    key are configured.
    """

    config: AzureConfig
    timeout_s: float = 30.0

    @property
    def enabled(self) -> bool:
        return bool(self.config.cognitive_key and (self.config.cognitive_endpoint or self.config.region))

    def speech_to_text(self, audio_path: str | Path, *, language: str = "pt-BR") -> dict[str, Any]:
        if not self.enabled:
            return {"available": False, "mode": "local_simulation", "reason": "missing_azure_cognitive_credentials"}

        region = self.config.region
        url = (
            f"https://{region}.stt.speech.microsoft.com/"
            f"speech/recognition/conversation/cognitiveservices/v1?language={language}"
        )
        headers = {
            "Ocp-Apim-Subscription-Key": str(self.config.cognitive_key),
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
        }
        audio_bytes = Path(audio_path).read_bytes()
        try:
            import httpx

            with httpx.Client(timeout=self.timeout_s) as client:
                resp = client.post(url, headers=headers, content=audio_bytes)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            return {"available": False, "mode": "configured", "provider": "azure_speech", "error": str(exc)}

        transcript = payload.get("DisplayText") or payload.get("NBest", [{}])[0].get("Display") or ""
        return {
            "available": True,
            "mode": "configured",
            "provider": "azure_speech",
            "language": language,
            "transcript": transcript,
            "raw_status": payload.get("RecognitionStatus"),
            "duration": payload.get("Duration"),
        }

    def analyze_text(self, text: str, *, language: str = "pt-br") -> dict[str, Any]:
        if not self.enabled:
            return {"available": False, "mode": "local_simulation", "reason": "missing_azure_cognitive_credentials"}
        if not text.strip():
            return {"available": False, "mode": "configured", "reason": "empty_text"}

        endpoint = (self.config.cognitive_endpoint or "").rstrip("/")
        url = f"{endpoint}/language/:analyze-text?api-version=2023-04-01"
        headers = {
            "Ocp-Apim-Subscription-Key": str(self.config.cognitive_key),
            "Content-Type": "application/json",
        }
        payload = {
            "kind": "SentimentAnalysis",
            "parameters": {"opinionMining": True},
            "analysisInput": {"documents": [{"id": "1", "language": language, "text": text[:5000]}]},
        }
        keyphrase_payload = {
            "kind": "KeyPhraseExtraction",
            "analysisInput": {"documents": [{"id": "1", "language": language, "text": text[:5000]}]},
        }

        try:
            import httpx

            with httpx.Client(timeout=self.timeout_s) as client:
                sent_resp = client.post(url, headers=headers, json=payload)
                sent_resp.raise_for_status()
                key_resp = client.post(url, headers=headers, json=keyphrase_payload)
                key_resp.raise_for_status()
            sentiment = _first_document(sent_resp.json())
            keyphrases = _first_document(key_resp.json())
        except Exception as exc:
            return {"available": False, "mode": "configured", "provider": "azure_language", "error": str(exc)}

        confidence = sentiment.get("confidenceScores") or {}
        negative = float(confidence.get("negative", 0.0) or 0.0)
        neutral = float(confidence.get("neutral", 0.0) or 0.0)
        positive = float(confidence.get("positive", 0.0) or 0.0)
        phrases = keyphrases.get("keyPhrases") or []
        critical_terms = _critical_key_phrases(phrases)
        risk_score = min(1.0, max(negative, 0.35 * len(critical_terms)))
        return {
            "available": True,
            "mode": "configured",
            "provider": "azure_language",
            "sentiment": sentiment.get("sentiment"),
            "confidence_scores": {"positive": positive, "neutral": neutral, "negative": negative},
            "key_phrases": phrases,
            "critical_terms": critical_terms,
            "risk_score": round(risk_score, 3),
        }


def _first_document(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return payload["results"]["documents"][0]
    except (KeyError, IndexError, TypeError):
        return {}


def _critical_key_phrases(phrases: list[str]) -> list[str]:
    critical_roots = (
        "amea", "agress", "medo", "viol", "isol", "controle", "dor",
        "sangramento", "press", "ansiedade", "depress", "suic", "risco",
    )
    out: list[str] = []
    for phrase in phrases:
        normalized = phrase.strip().lower()
        if any(root in normalized for root in critical_roots):
            out.append(phrase)
    return out


def send_service_bus_alert(*, report: dict[str, Any], config: AzureConfig, case_id: str, payload_hash: str) -> dict[str, Any]:
    if not config.service_bus_connection_string:
        return {"mode": "local_simulation", "status": "not_sent", "reason": "missing_service_bus_connection_string"}

    parsed = _parse_service_bus_connection_string(config.service_bus_connection_string)
    if not parsed:
        return {"mode": "configured", "status": "not_sent", "reason": "invalid_service_bus_connection_string"}

    queue = config.service_bus_queue
    resource_uri = f"{parsed['endpoint']}{queue}"
    url = f"{resource_uri}/messages"
    token = _build_sas_token(resource_uri, parsed["key_name"], parsed["key"])
    message = {
        "case_id": case_id,
        "payload_hash": payload_hash,
        "risk_level": (report.get("priority") or {}).get("riskLevel"),
        "level": report.get("level"),
        "score": report.get("multimodal_score_0_1"),
        "human_review_required": (report.get("priority") or {}).get("humanReviewRequired"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        import httpx

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers={"Authorization": token, "Content-Type": "application/json"}, json=message)
        resp.raise_for_status()
    except Exception as exc:
        return {"mode": "configured", "status": "send_failed", "provider": "azure_service_bus", "error": str(exc)}
    return {"mode": "configured", "status": "sent", "provider": "azure_service_bus", "queue": queue}


def _parse_service_bus_connection_string(value: str) -> dict[str, str] | None:
    parts = {}
    for item in value.split(";"):
        if "=" in item:
            key, val = item.split("=", 1)
            parts[key] = val
    endpoint = parts.get("Endpoint", "").rstrip("/") + "/"
    key_name = parts.get("SharedAccessKeyName")
    key = parts.get("SharedAccessKey")
    if not endpoint.startswith("https://") or not key_name or not key:
        return None
    return {"endpoint": endpoint, "key_name": key_name, "key": key}


def _build_sas_token(resource_uri: str, key_name: str, key: str, ttl_s: int = 3600) -> str:
    expiry = int(time.time()) + ttl_s
    encoded_uri = quote_plus(resource_uri)
    string_to_sign = f"{encoded_uri}\n{expiry}".encode("utf-8")
    signed = hmac.new(base64.b64decode(key), string_to_sign, hashlib.sha256).digest()
    signature = quote_plus(base64.b64encode(signed).decode("utf-8"))
    return f"SharedAccessSignature sr={encoded_uri}&sig={signature}&se={expiry}&skn={key_name}"


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

    delivery = send_service_bus_alert(report=report, config=config, case_id=case_id, payload_hash=payload_hash) if alert_required else {
        "mode": "not_required",
        "status": "not_sent",
        "reason": "routine_monitoring",
    }

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
            "status": "queued_for_medical_team" if alert_required and delivery.get("status") == "sent" else ("prepared_for_medical_team" if alert_required else "not_required"),
            "reason": "high_or_review_required" if alert_required else "routine_monitoring",
            "delivery": delivery,
        },
        "configuration": {
            "cognitive_endpoint": "set" if config.cognitive_endpoint else "missing",
            "storage_account": "set" if config.storage_account else "missing",
            "service_bus_namespace": "set" if config.service_bus_namespace else "missing",
            "service_bus_connection_string": "set" if config.service_bus_connection_string else "missing",
            "key_vault_name": "set" if config.key_vault_name else "missing",
        },
    }
