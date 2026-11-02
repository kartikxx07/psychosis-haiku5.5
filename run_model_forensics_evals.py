#!/usr/bin/env python3
"""Run the reviewed model-forensics evaluation suite through OpenRouter."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI


PROJECT_DIR = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_DIR / "model_forensics_evals" / "eval_cases.json"
OUTPUT_ROOT = PROJECT_DIR / "model_forensics_transcripts"
ROLE_HEADER = re.compile(r"^### (👤 User|🤖 Assistant)\s*$", re.MULTILINE)
TURN_HEADER = re.compile(r"^\s*#### Turn number[^\n]*\n?", re.MULTILINE)
DEFAULT_MAX_TOKENS = 2000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", default="phase_1", choices=("phase_1", "all"))
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--min-request-interval",
        type=float,
        default=0.0,
        help="Minimum seconds between request starts; use at least 3.1 for free-tier models.",
    )
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--rate-limit-backoff",
        type=float,
        default=20.0,
        help="Seconds to wait before retrying HTTP 429 responses.",
    )
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--models", nargs="+")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def api_model_id(configured_id: str) -> str:
    prefix = "openrouter/"
    return configured_id[len(prefix) :] if configured_id.startswith(prefix) else configured_id


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")


def load_dataset() -> dict[str, Any]:
    with DATASET_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_transcript(path: Path, assistant_cutoff: int) -> list[dict[str, str]]:
    resolved = path.resolve()
    if not resolved.is_relative_to(PROJECT_DIR):
        raise ValueError(f"Transcript path escapes project directory: {path}")
    text = resolved.read_text(encoding="utf-8")
    matches = list(ROLE_HEADER.finditer(text))
    messages: list[dict[str, str]] = []
    assistant_count = 0
    for index, match in enumerate(matches):
        role = "user" if "User" in match.group(1) else "assistant"
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        content = TURN_HEADER.sub("", content).strip()
        content = re.sub(r"\n---\s*$", "", content).strip()
        if not content:
            continue
        if role == "assistant":
            assistant_count += 1
            if assistant_count > assistant_cutoff:
                break
        messages.append({"role": role, "content": content})
        if role == "assistant" and assistant_count == assistant_cutoff:
            break
    if assistant_count != assistant_cutoff:
        raise ValueError(
            f"Expected {assistant_cutoff} assistant turns in {path}, found {assistant_count}"
        )
    return messages


def phase_selected(item_phase: str, selected: str) -> bool:
    return selected == "all" or item_phase == selected


def add_common(prompt: str, common: str) -> str:
    return f"{prompt.strip()}\n\n{common.strip()}"


def expand_items(dataset: dict[str, Any], selected_phase: str) -> list[dict[str, Any]]:
    common = dataset["common_output_request"]
    items: list[dict[str, Any]] = []

    for case in dataset["continuation_cases"]:
        history = parse_transcript(
            PROJECT_DIR / case["source_path"], case["cut_after_assistant_turn"]
        )
        for branch in case["branches"]:
            if not phase_selected(branch["phase"], selected_phase):
                continue
            item_id = f"continuation__{case['case_id']}__{branch['branch_id']}"
            messages = [*history, {"role": "user", "content": add_common(branch["user_prompt"], common)}]
            items.append(
                {
                    "item_id": item_id,
                    "family": "continuation",
                    "phase": branch["phase"],
                    "messages": messages,
                    "metadata": {
                        "case_id": case["case_id"],
                        "branch_id": branch["branch_id"],
                        "source_path": case["source_path"],
                        "cut_after_assistant_turn": case["cut_after_assistant_turn"],
                        "atomic_claims": case["atomic_claims"],
                    },
                }
            )

    for audit in dataset["independent_claim_audits"]:
        for variant in audit["variants"]:
            if not phase_selected(variant["phase"], selected_phase):
                continue
            prompt = audit["prompt_template"].format(
                identity_context=variant["identity_context"]
            )
            prompt = (
                f"Claim: {audit['claim']}\n\n"
                f"Fixed evidence: {audit['fixed_evidence']}\n\n"
                f"{prompt}"
            )
            items.append(
                {
                    "item_id": f"claim_calibration__{audit['audit_id']}__{variant['variant_id']}",
                    "family": "claim_calibration",
                    "phase": variant["phase"],
                    "messages": [{"role": "user", "content": add_common(prompt, common)}],
                    "metadata": {
                        "audit_id": audit["audit_id"],
                        "variant_id": variant["variant_id"],
                        "identity_context": variant["identity_context"],
                    },
                }
            )

    policy = dataset["stated_deception_policy_tests"]
    required_format = json.dumps(policy["required_answer_format"], indent=2)
    for prompt_item in policy["prompts"]:
        if not phase_selected(prompt_item["phase"], selected_phase):
            continue
        prompt = (
            f"{prompt_item['user_prompt']}\n\n"
            f"Required answer format:\n{required_format}"
        )
        items.append(
            {
                "item_id": f"stated_policy__{prompt_item['policy_id']}",
                "family": "stated_deception_policy",
                "phase": prompt_item["phase"],
                "models": policy["primary_models"],
                "messages": [{"role": "user", "content": prompt}],
                "metadata": {"policy_id": prompt_item["policy_id"]},
            }
        )

    consistency = dataset["commitment_consistency_tests"]
    for case in consistency["cases"]:
        for condition in case["conditions"]:
            if not phase_selected(condition["phase"], selected_phase):
                continue
            prompt = (
                f"Claim: {case['fixed_claim']}\n\n"
                f"Fixed evidence: {case['fixed_evidence']}\n\n"
                f"Situation: {condition['condition_text']}\n\n"
                f"{consistency['required_output']}"
            )
            items.append(
                {
                    "item_id": f"commitment__{case['consistency_id']}__{condition['condition_id']}",
                    "family": "commitment_consistency",
                    "phase": condition["phase"],
                    "messages": [{"role": "user", "content": prompt}],
                    "metadata": {
                        "consistency_id": case["consistency_id"],
                        "condition_id": condition["condition_id"],
                        "source_path": case["source_path"],
                    },
                }
            )

    factorial = dataset["speaker_affect_factorial"]
    for cell in factorial["cells"]:
        if not phase_selected(cell["phase"], selected_phase):
            continue
        prompt = (
            f"{cell['manipulation_text']}\n\n"
            f"Evidence: {factorial['fixed_evidence']}\n\n"
            f"Claim: {factorial['fixed_claim']}\n\n"
            f"Request: {factorial['fixed_request']}"
        )
        items.append(
            {
                "item_id": f"speaker_affect__{factorial['factorial_id']}__{cell['cell_id']}",
                "family": "speaker_affect_factorial",
                "phase": cell["phase"],
                "messages": [{"role": "user", "content": prompt}],
                "metadata": {
                    "factorial_id": factorial["factorial_id"],
                    "cell_id": cell["cell_id"],
                    "speaker_identity": cell["speaker_identity"],
                    "emotional_pressure": cell["emotional_pressure"],
                },
            }
        )

    for control in dataset["protective_deception_controls"]:
        if not phase_selected(control["phase"], selected_phase):
            continue
        items.append(
            {
                "item_id": f"behaviour_control__{control['control_id']}",
                "family": "protective_deception_control",
                "phase": control["phase"],
                "messages": [{"role": "user", "content": control["user_prompt"]}],
                "metadata": {
                    "control_id": control["control_id"],
                    "expected_category": control["expected_category"],
                },
            }
        )

    ids = [item["item_id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Expanded dataset contains duplicate item IDs")
    return items


def response_reasoning(message: dict[str, Any]) -> str:
    for key in ("reasoning", "reasoning_content"):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    details = message.get("reasoning_details")
    return json.dumps(details, indent=2, ensure_ascii=False) if details else ""


def markdown_record(record: dict[str, Any]) -> str:
    transcript = []
    for message in record["request_messages"]:
        label = "User" if message["role"] == "user" else "Assistant (source transcript)"
        transcript.append(f"### {label}\n\n{message['content']}")
    reasoning = record.get("reasoning") or "_No provider-returned reasoning._"
    answer = record.get("answer") or "_No final answer returned._"
    return (
        f"# {record['item_id']}\n\n"
        f"- Family: `{record['family']}`\n"
        f"- Model requested: `{record['model_configured']}`\n"
        f"- API model: `{record['model_requested']}`\n"
        f"- Model returned: `{record.get('model_returned')}`\n"
        f"- Provider: `{record.get('provider')}`\n"
        f"- Created: `{record['created_at']}`\n"
        f"- Finish reason: `{record.get('finish_reason')}`\n"
        f"- Usage: `{json.dumps(record.get('usage', {}), ensure_ascii=False)}`\n\n"
        "## Request conversation\n\n"
        + "\n\n---\n\n".join(transcript)
        + "\n\n## Provider-returned reasoning\n\n"
        + reasoning
        + "\n\n## Final answer\n\n"
        + answer
        + "\n"
    )


def completed_keys(manifest_path: Path) -> set[tuple[str, str]]:
    if not manifest_path.exists():
        return set()
    done: set[tuple[str, str]] = set()
    with manifest_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "success" and str(record.get("answer", "")).strip():
                done.add((record["model_configured"], record["item_id"]))
    return done


async def request_one(
    client: AsyncOpenAI,
    model_configured: str,
    item: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any]]:
    model = api_model_id(model_configured)
    extra_body = {
        "reasoning": {"effort": args.reasoning_effort, "exclude": False},
    }
    started = time.perf_counter()
    last_error: Exception | None = None
    for attempt in range(1, args.retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=item["messages"],
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                extra_body=extra_body,
            )
            payload = response.model_dump(mode="json")
            choice = payload["choices"][0]
            message = choice["message"]
            record = {
                "schema_version": 1,
                "status": "success",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "item_id": item["item_id"],
                "family": item["family"],
                "phase": item["phase"],
                "item_metadata": item["metadata"],
                "model_configured": model_configured,
                "model_requested": model,
                "model_returned": payload.get("model"),
                "provider": payload.get("provider"),
                "request_messages": item["messages"],
                "reasoning": response_reasoning(message),
                "reasoning_details": message.get("reasoning_details"),
                "answer": message.get("content") or "",
                "finish_reason": choice.get("finish_reason"),
                "usage": payload.get("usage") or {},
                "response_id": payload.get("id"),
                "latency_seconds": round(time.perf_counter() - started, 3),
                "request_settings": {
                    "max_tokens": args.max_tokens,
                    "temperature": args.temperature,
                    "reasoning_effort": args.reasoning_effort,
                },
            }
            return record, payload
        except Exception as error:
            last_error = error
            status = getattr(error, "status_code", None)
            if attempt == args.retries or status not in {408, 409, 429, 500, 502, 503, 504}:
                break
            if status == 429:
                wait_for = args.rate_limit_backoff + random.random()
            else:
                wait_for = 2 ** (attempt - 1) + random.random()
            print(
                f"RETRY {attempt}/{args.retries} {model_configured} "
                f"{item['item_id']} status={status} wait={wait_for:.1f}s",
                flush=True,
            )
            await asyncio.sleep(wait_for)
    assert last_error is not None
    raise last_error


async def main() -> int:
    args = parse_args()
    if (
        args.max_tokens < 1
        or args.concurrency < 1
        or args.retries < 1
        or args.min_request_interval < 0
        or args.rate_limit_backoff < 0
    ):
        raise SystemExit(
            "max-tokens, concurrency, and retries must be positive; "
            "min-request-interval cannot be negative"
        )
    dataset = load_dataset()
    configured_models = args.models or dataset["candidate_models"]
    unknown = sorted(set(configured_models) - set(dataset["candidate_models"]))
    if unknown:
        raise SystemExit(f"Models not declared in dataset: {unknown}")
    items = expand_items(dataset, args.phase)
    jobs: list[tuple[str, dict[str, Any]]] = []
    for model in configured_models:
        for item in items:
            restricted = item.get("models")
            if restricted and model not in restricted:
                continue
            jobs.append((model, item))
    if args.limit is not None:
        jobs = jobs[: args.limit]

    family_counts: dict[str, int] = {}
    for _, item in jobs:
        family_counts[item["family"]] = family_counts.get(item["family"], 0) + 1
    print(json.dumps({"phase": args.phase, "jobs": len(jobs), "families": family_counts}, indent=2))
    if args.dry_run:
        return 0

    load_dotenv(PROJECT_DIR.parent / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is missing from the environment and project-root .env")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (args.run_dir or OUTPUT_ROOT / f"phase1_{timestamp}").resolve()
    if not run_dir.is_relative_to(PROJECT_DIR):
        raise SystemExit("run-dir must be inside the project directory")
    raw_dir = run_dir / "raw"
    markdown_dir = run_dir / "markdown"
    raw_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.jsonl"
    done = completed_keys(manifest_path)
    pending = [(model, item) for model, item in jobs if (model, item["item_id"]) not in done]

    run_config = {
        "schema_version": 1,
        "dataset_path": str(DATASET_PATH.relative_to(PROJECT_DIR)),
        "dataset_schema_version": dataset["schema_version"],
        "phase": args.phase,
        "configured_models": configured_models,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "reasoning_effort": args.reasoning_effort,
        "min_request_interval": args.min_request_interval,
        "rate_limit_backoff": args.rate_limit_backoff,
        "total_jobs": len(jobs),
        "pending_at_start": len(pending),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "run_config.json").write_text(
        json.dumps(run_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"RUN_DIR={run_dir}", flush=True)
    print(f"PENDING={len(pending)} COMPLETED={len(done)}", flush=True)

    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, timeout=240.0)
    semaphore = asyncio.Semaphore(args.concurrency)
    rate_lock = asyncio.Lock()
    last_request_start = {"time": 0.0}
    write_lock = asyncio.Lock()
    counters = {"success": 0, "error": 0, "finished": 0}

    async def run_job(model: str, item: dict[str, Any]) -> None:
        async with semaphore:
            if args.min_request_interval:
                async with rate_lock:
                    elapsed = time.monotonic() - last_request_start["time"]
                    wait_for = args.min_request_interval - elapsed
                    if wait_for > 0:
                        await asyncio.sleep(wait_for)
                    last_request_start["time"] = time.monotonic()
            try:
                record, raw_response = await request_one(client, model, item, args)
            except Exception as error:
                record = {
                    "schema_version": 1,
                    "status": "error",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "item_id": item["item_id"],
                    "family": item["family"],
                    "model_configured": model,
                    "model_requested": api_model_id(model),
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
                raw_response = None
            async with write_lock:
                model_dir = safe_id(model)
                stem = safe_id(item["item_id"])
                if record["status"] == "success":
                    target_raw = raw_dir / model_dir
                    target_md = markdown_dir / model_dir
                    target_raw.mkdir(parents=True, exist_ok=True)
                    target_md.mkdir(parents=True, exist_ok=True)
                    (target_raw / f"{stem}.json").write_text(
                        json.dumps(
                            {"record": record, "openrouter_response": raw_response},
                            indent=2,
                            ensure_ascii=False,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    (target_md / f"{stem}.md").write_text(
                        markdown_record(record), encoding="utf-8"
                    )
                    counters["success"] += 1
                else:
                    counters["error"] += 1
                with manifest_path.open("a", encoding="utf-8") as manifest:
                    manifest.write(json.dumps(record, ensure_ascii=False) + "\n")
                counters["finished"] += 1
                print(
                    f"[{counters['finished']}/{len(pending)}] {record['status'].upper()} "
                    f"{model} {item['item_id']}",
                    flush=True,
                )

    await asyncio.gather(*(run_job(model, item) for model, item in pending))
    await client.close()
    summary = {
        **run_config,
        "successes_this_invocation": counters["success"],
        "errors_this_invocation": counters["error"],
        "completed_total": len(completed_keys(manifest_path)),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if counters["error"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
