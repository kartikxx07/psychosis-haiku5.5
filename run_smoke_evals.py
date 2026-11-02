#!/usr/bin/env python3
"""Run the human-authored DeepSeek smoke evaluations through OpenRouter."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI


PROJECT_DIR = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_DIR / "smoke_evals"
OUTPUT_DIR = PROJECT_DIR / "smoke_Test_transcripts"
DEFAULT_MODEL = "deepseek/deepseek-v4-flash-0731"
DEFAULT_PROVIDER = "OpenInference"
RESPONSE_LENGTH_INSTRUCTION = "Keep your final answer under 250 words."
DATASET_FILES = (
    DATASET_DIR / "belief_claims.jsonl",
    DATASET_DIR / "response_policy_scenarios.jsonl",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--max-tokens", type=int, default=2000)
    parser.add_argument(
        "--reasoning-effort",
        choices=("minimal", "low", "medium", "high", "xhigh", "max"),
        default="medium",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--retries", type=int, default=3)
    return parser.parse_args()


def load_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for dataset_path in DATASET_FILES:
        with dataset_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                item = json.loads(line)
                item_id = item["id"]
                if item_id in seen:
                    raise ValueError(f"Duplicate item ID: {item_id}")
                seen.add(item_id)
                item["dataset"] = dataset_path.stem
                item["dataset_file"] = dataset_path.name
                item["dataset_line"] = line_number
                items.append(item)
    return items


def completed_ids(manifest_path: Path) -> set[str]:
    if not manifest_path.exists():
        return set()
    completed: set[str] = set()
    with manifest_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "success":
                completed.add(record["item_id"])
    return completed


def reasoning_text(message: dict[str, Any]) -> str:
    for key in ("reasoning", "reasoning_content"):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    details = message.get("reasoning_details")
    if details:
        return json.dumps(details, indent=2, ensure_ascii=False)
    return ""


def markdown_record(record: dict[str, Any]) -> str:
    metadata = record["response_metadata"]
    reasoning = record.get("reasoning") or "_No provider-returned reasoning._"
    answer = record.get("answer") or "_No final answer returned._"
    return (
        f"# {record['item_id']}\n\n"
        f"- Dataset: `{record['dataset']}`\n"
        f"- Model: `{metadata['model_requested']}`\n"
        f"- Model returned: `{metadata.get('model_returned')}`\n"
        f"- Provider: `{metadata.get('provider')}`\n"
        f"- Reasoning effort: `{metadata['reasoning_effort']}`\n"
        f"- Maximum completion tokens: `{metadata['max_tokens']}`\n"
        f"- Created: `{record['created_at']}`\n"
        f"- Usage: `{json.dumps(metadata.get('usage', {}), ensure_ascii=False)}`\n\n"
        "## Prompt\n\n"
        f"{record['request_messages'][0]['content']}\n\n"
        "## Provider-returned reasoning\n\n"
        f"{reasoning}\n\n"
        "## Final answer\n\n"
        f"{answer}\n"
    )


async def request_item(
    client: AsyncOpenAI,
    item: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any]]:
    extra_body: dict[str, Any] = {
        "reasoning": {
            "effort": args.reasoning_effort,
            "exclude": False,
        }
    }
    if args.provider:
        extra_body["provider"] = {
            "order": [args.provider],
            "allow_fallbacks": False,
        }

    request_prompt = f"{item['prompt']}\n\n{RESPONSE_LENGTH_INSTRUCTION}"
    request_messages = [{"role": "user", "content": request_prompt}]
    last_error: Exception | None = None
    started = time.perf_counter()
    for attempt in range(1, args.retries + 1):
        try:
            response = await client.chat.completions.create(
                model=args.model,
                messages=request_messages,
                max_tokens=args.max_tokens,
                extra_body=extra_body,
            )
            payload = response.model_dump(mode="json")
            message = payload["choices"][0]["message"]
            metadata = {
                "model_requested": args.model,
                "model_returned": payload.get("model"),
                "provider": payload.get("provider") or args.provider,
                "reasoning_effort": args.reasoning_effort,
                "max_tokens": args.max_tokens,
                "finish_reason": payload["choices"][0].get("finish_reason"),
                "usage": payload.get("usage") or {},
                "latency_seconds": round(time.perf_counter() - started, 3),
                "response_id": payload.get("id"),
            }
            record = {
                "schema_version": 1,
                "status": "success",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "item_id": item["id"],
                "dataset": item["dataset"],
                "dataset_file": item["dataset_file"],
                "dataset_line": item["dataset_line"],
                "evaluator_metadata": {
                    key: value
                    for key, value in item.items()
                    if key not in {"prompt", "dataset", "dataset_file", "dataset_line"}
                },
                "prompt": item["prompt"],
                "request_messages": request_messages,
                "reasoning": reasoning_text(message),
                "reasoning_details": message.get("reasoning_details"),
                "answer": message.get("content") or "",
                "response_metadata": metadata,
            }
            return record, payload
        except Exception as error:  # SDK exception types differ by status class.
            last_error = error
            status_code = getattr(error, "status_code", None)
            if attempt >= args.retries or status_code not in {408, 409, 429, 500, 502, 503, 504}:
                break
            await asyncio.sleep((2 ** (attempt - 1)) + random.random())
    assert last_error is not None
    raise last_error


async def main() -> int:
    args = parse_args()
    load_dotenv(PROJECT_DIR.parent / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENROUTER_API_KEY is missing from the environment and project-root .env"
        )
    if args.max_tokens < 1:
        raise SystemExit("--max-tokens must be positive")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (args.run_dir or (OUTPUT_DIR / f"run_{timestamp}")).resolve()
    raw_dir = run_dir / "raw"
    markdown_dir = run_dir / "markdown"
    raw_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.jsonl"

    items = load_items()
    if args.limit is not None:
        items = items[: args.limit]
    done = completed_ids(manifest_path)
    pending = [item for item in items if item["id"] not in done]

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=180.0,
    )
    successes = 0
    failures = 0
    print(f"RUN_DIR={run_dir}", flush=True)
    print(f"PENDING={len(pending)} COMPLETED={len(done)}", flush=True)

    for index, item in enumerate(pending, start=1):
        print(f"[{index}/{len(pending)}] {item['id']}", flush=True)
        try:
            record, raw_response = await request_item(client, item, args)
            raw_path = raw_dir / f"{item['id']}.json"
            raw_path.write_text(
                json.dumps(
                    {"record": record, "openrouter_response": raw_response},
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (markdown_dir / f"{item['id']}.md").write_text(
                markdown_record(record), encoding="utf-8"
            )
            successes += 1
        except Exception as error:
            record = {
                "schema_version": 1,
                "status": "error",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "item_id": item["id"],
                "dataset": item["dataset"],
                "error_type": type(error).__name__,
                "error": str(error),
            }
            failures += 1
        with manifest_path.open("a", encoding="utf-8") as manifest:
            manifest.write(json.dumps(record, ensure_ascii=False) + "\n")
        if record["status"] == "error":
            print(f"ERROR {record['error_type']}: {record['error']}", flush=True)
            break

    summary = {
        "schema_version": 1,
        "run_dir": str(run_dir),
        "model": args.model,
        "provider": args.provider,
        "reasoning_effort": args.reasoning_effort,
        "max_tokens": args.max_tokens,
        "successes_this_invocation": successes,
        "failures_this_invocation": failures,
        "completed_item_ids": sorted(completed_ids(manifest_path)),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"SUCCESS={successes} FAILURE={failures}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
