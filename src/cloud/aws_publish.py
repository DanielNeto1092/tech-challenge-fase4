"""AWS cloud integration: S3 with free SSE-S3, optional DynamoDB and SNS."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from src.config import AwsConfig


def publish_report(
    *,
    report: dict[str, Any],
    patient_id: str,
    config: AwsConfig,
    severity_trigger: tuple[str, ...] = ("high", "critical"),
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    import boto3

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    level = str(report.get("level", "unknown"))
    dt = datetime.now(timezone.utc)

    key = f"{config.s3_prefix.rstrip('/')}/{patient_id}/{dt:%Y/%m/%d}/{timestamp}_{uuid.uuid4().hex}.json"

    payload = json.dumps({"patient_id": patient_id, "timestamp_utc": timestamp, "report": report, "metadata": extra_metadata or {}}, ensure_ascii=False).encode("utf-8")

    s3 = boto3.client("s3", region_name=config.region)
    put_kwargs: dict[str, Any] = {
        "Bucket": config.s3_bucket,
        "Key": key,
        "Body": payload,
        "ContentType": "application/json; charset=utf-8",
        "ServerSideEncryption": "AES256",
    }
    if config.kms_key_id:
        put_kwargs["ServerSideEncryption"] = "aws:kms"
        put_kwargs["SSEKMSKeyId"] = config.kms_key_id
    s3.put_object(**put_kwargs)

    receipt: dict[str, Any] = {"s3_bucket": config.s3_bucket, "s3_key": key}

    if config.dynamodb_table:
        ddb = boto3.resource("dynamodb", region_name=config.region)
        table = ddb.Table(config.dynamodb_table)
        table.put_item(Item={
            "pk": f"PATIENT#{patient_id}",
            "sk": f"TS#{timestamp}",
            "level": level,
            "score": float(report.get("multimodal_score_0_1", 0)),
            "s3_key": key,
        })
        receipt["dynamodb_table"] = config.dynamodb_table

    if config.sns_topic_arn and level in severity_trigger:
        sns = boto3.client("sns", region_name=config.region)
        resp = sns.publish(
            TopicArn=config.sns_topic_arn,
            Message=json.dumps({"patient_id": patient_id, "level": level, "score": report.get("multimodal_score_0_1"), "s3_key": key}),
            Subject=f"Sentinela Alert: {level.upper()} ({patient_id})",
        )
        receipt["sns_message_id"] = resp.get("MessageId")

    return receipt
