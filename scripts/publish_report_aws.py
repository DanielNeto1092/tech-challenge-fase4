"""Publish one local Sentinela risk report JSON to the AWS Free Tier stack.

By default this script only uploads to S3. The CloudFormation stack in
infra/aws/free_tier_stack.yaml can then index the report with Lambda.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cloud import publish_report  # noqa: E402
from src.config import AwsConfig  # noqa: E402


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in ("", None) else default


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload an Sentinela report JSON to AWS S3.")
    parser.add_argument("report_json", type=Path, help="Path to a local report JSON.")
    parser.add_argument("--patient-id", default="demo-patient-001", help="Pseudonymous patient id.")
    parser.add_argument("--bucket", default=_env("SENTINELA_AWS_BUCKET"), help="Target S3 bucket.")
    parser.add_argument("--region", default=_env("AWS_DEFAULT_REGION", "us-east-1"), help="AWS region.")
    parser.add_argument("--prefix", default=_env("SENTINELA_AWS_PREFIX", "results"), help="S3 key prefix.")
    parser.add_argument("--send", action="store_true", help="Actually publish. Without this, run a dry check.")
    args = parser.parse_args()

    if not args.report_json.exists():
        parser.error(f"Report file not found: {args.report_json}")
    if not args.bucket:
        parser.error("Set --bucket or SENTINELA_AWS_BUCKET.")

    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    config = AwsConfig(region=args.region, s3_bucket=args.bucket, s3_prefix=args.prefix)

    if not args.send:
        print("Dry run OK.")
        print(f"Would upload: {args.report_json}")
        print(f"Bucket: {config.s3_bucket}")
        print(f"Prefix: {config.s3_prefix}")
        print(f"Patient id: {args.patient_id}")
        print("Add --send when you are ready.")
        return 0

    receipt = publish_report(report=report, patient_id=args.patient_id, config=config)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
