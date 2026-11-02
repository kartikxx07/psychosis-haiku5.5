#!/usr/bin/env python3
"""Run the small, single-turn mental-health routing eval through OpenRouter."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI


PROJECT_DIR = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_DIR / "model_forensics_evals" / "mental_health_triage_cases.json"


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=[
        "openrouter/deepseek/deepseek-v4-flash",
        "openrouter/anthropic/claude-haiku-4.5",
        "openrouter/anthropic/claude-haiku-5.5",
    ])
    parser.add_argument(
        "--run-dir", type=Path,
        default=PROJECT_DIR / "model_forensics_transcripts" / "mental_health_triage_20261011",
    )
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    # The repository stores the shared OpenRouter credentials one directory above
    # this project; support a project-local override if one is added later.
    load_dotenv(PROJECT_DIR / ".env")
    load_dotenv(PROJECT_DIR.parent / ".env", override=False)
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY (or OPENROUTER_KEY) is not set")

    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    if args.run_dir.is_absolute():
        run_dir = args.run_dir
    else:
        run_dir = PROJECT_DIR / args.run_dir
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(args.concurrency)
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        max_retries=3,
        timeout=120,
        default_headers={"HTTP-Referer": "https://openrouter.ai", "X-Title": "AI Psychosis Forensics"},
    )
    manifest: list[dict[str, Any]] = []

    async def run_one(model: str, case: dict[str, Any]) -> dict[str, Any]:
        model_id = model.removeprefix("openrouter/")
        record_id = f"{safe_id(model)}__{safe_id(case['case_id'])}"
        path = raw_dir / f"{record_id}.json"
        async with semaphore:
            try:
                response = await client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": case["prompt"]}],
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                )
                message = response.choices[0].message
                content = message.content
                if isinstance(content, list):
                    content = "\n".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in content
                    )
                record = {
                    "schema_version": 1,
                    "status": "success" if content and str(content).strip() else "empty",
                    "record_id": record_id,
                    "model_configured": model,
                    "model_requested": model_id,
                    "case_id": case["case_id"],
                    "severity_band": case["severity_band"],
                    "location": case["location"],
                    "prompt": case["prompt"],
                    "response": content,
                    "expected_response_features": case["expected_response_features"],
                    "disallowed_shortcut": case["disallowed_shortcut"],
                    "usage": response.usage.model_dump() if response.usage else None,
                    "provider": getattr(response, "provider", None),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as exc:  # record the failed cell and continue the matrix
                record = {
                    "schema_version": 1,
                    "status": "error",
                    "record_id": record_id,
                    "model_configured": model,
                    "model_requested": model_id,
                    "case_id": case["case_id"],
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            manifest_item = {k: record.get(k) for k in (
                "record_id", "status", "model_configured", "case_id", "error_type", "error"
            ) if k in record}
            return manifest_item

    jobs = [run_one(model, case) for model in args.models for case in dataset["cases"]]
    for future in asyncio.as_completed(jobs):
        item = await future
        manifest.append(item)
        print(f"{len(manifest)}/{len(jobs)} {item['status']} {item['model_configured']} {item['case_id']}", flush=True)

    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    success = sum(item["status"] == "success" for item in manifest)
    summary = {
        "schema_version": 1,
        "dataset": str(DATASET_PATH.relative_to(PROJECT_DIR)),
        "models": args.models,
        "cases_per_model": len(dataset["cases"]),
        "expected_calls": len(jobs),
        "successes": success,
        "errors_or_empty": len(manifest) - success,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    await client.close()
    print(json.dumps(summary, indent=2))
    return 0 if success == len(jobs) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
