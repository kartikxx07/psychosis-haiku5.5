#!/usr/bin/env python3
"""Run system/user rubric, honesty, and accuracy overlays on canonical replays."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from run_eight_turn_replays import compile_inputs, load_manifest, model_turn
from run_model_forensics_evals import safe_id


PROJECT_DIR = Path(__file__).resolve().parent
SPEC_PATH = PROJECT_DIR / "model_forensics_evals" / "post_conversation_self_assessment.json"
DEFAULT_RUN_DIR = PROJECT_DIR / "eight_turn_ablation_transcripts" / "prompt_interventions_20261012"
DEFAULT_MODELS = [
    "openrouter/anthropic/claude-haiku-4.5",
    "openrouter/anthropic/claude-haiku-5.5",
    "openrouter/deepseek/deepseek-v4-flash",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--characters", nargs="+")
    parser.add_argument("--conditions", nargs="+")
    parser.add_argument("--overlays", nargs="+", choices=(
        "rubric_user_final", "rubric_system_final", "honesty_midpoint", "accuracy_midpoint"
    ))
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--max-tokens", type=int, default=3000)
    parser.add_argument("--max-empty-retries", type=int, default=2)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--temperature", type=float, default=0.0)
    return parser.parse_args()


def load_spec() -> dict[str, Any]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def make_events(item: dict[str, Any], overlay: str, spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    events: list[dict[str, Any]] = []
    for source_turn, original_text in enumerate(item["user_turns"], start=1):
        user_text = original_text
        if overlay in {"rubric_user_final", "rubric_system_final"} and source_turn == 8:
            user_text += "\n\n" + spec["final_turn_user_prompt"]
        events.append({"source_turn": source_turn, "kind": "scripted_user", "user": user_text})
        if overlay in {"honesty_midpoint", "accuracy_midpoint"} and source_turn == 4:
            key = "honesty_condition" if overlay == "honesty_midpoint" else "accuracy_condition"
            prompt = spec["mid_conversation_instruction_studies"][key]["user_prompt"]
            events.append({"source_turn": 4, "kind": overlay, "user": prompt})

    system = []
    if overlay == "rubric_system_final":
        system.append({"role": "system", "content": spec["system_monitoring_instruction"]})
    return events, system


def build_items(args: argparse.Namespace, manifest: dict[str, Any], spec: dict[str, Any]) -> list[dict[str, Any]]:
    base_items = compile_inputs(manifest, args)
    overlays = args.overlays or [
        "rubric_user_final", "rubric_system_final", "honesty_midpoint", "accuracy_midpoint"
    ]
    result = []
    for base in base_items:
        for overlay in overlays:
            events, system = make_events(base, overlay, spec)
            digest_payload = {"events": events, "system": system, "base_hash": base["compiled_user_turns_sha256"]}
            digest = hashlib.sha256(
                json.dumps(digest_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            result.append({
                **base,
                "base_condition_id": base["condition_id"],
                "condition_id": f"{base['condition_id']}__{overlay}",
                "overlay_id": overlay,
                "events": events,
                "system_messages": system,
                "compiled_user_turns_sha256": digest,
            })
    return result


def markdown(record: dict[str, Any]) -> str:
    lines = [
        f"# {record['character']} — {record['condition_id']}",
        "",
        f"- Model: `{record['model_configured']}`",
        f"- Overlay: `{record['overlay_id']}`",
        f"- Status: `{record['status']}`",
        f"- Source: `{record['source_path']}`",
        "",
        "## System prompt overlay",
        "",
        record.get("system_prompt_text") or "_None._",
    ]
    for turn in record["turn_records"]:
        lines.extend([
            "", f"## Assistant response {turn['step_index']} (source turn {turn['source_turn']}; {turn['kind']})",
            "", "### User", "", turn["user"], "", "### Provider-returned reasoning", "",
            turn.get("reasoning") or "_No provider-returned reasoning._", "", "### Assistant", "",
            turn.get("assistant") or "_No final answer returned._",
        ])
    return "\n".join(lines) + "\n"


async def main() -> int:
    args = parse_args()
    manifest = load_manifest()
    spec = load_spec()
    items = build_items(args, manifest, spec)
    models = args.models
    run_dir = args.run_dir.resolve()
    if not run_dir.is_relative_to(PROJECT_DIR):
        raise SystemExit("run-dir must be inside the project")
    run_dir.mkdir(parents=True, exist_ok=True)
    compiled_path = run_dir / "compiled_inputs.json"
    compiled_path.write_text(json.dumps({
        "schema_version": 1,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "items": items,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    expected_conversations = len(items) * len(models)
    expected_calls = sum(len(item["events"]) for item in items) * len(models)
    print(json.dumps({
        "base_conditions": len({item["base_condition_id"] for item in items}),
        "overlays": sorted({item["overlay_id"] for item in items}),
        "compiled_items_per_model": len(items),
        "models": models,
        "expected_conversations": expected_conversations,
        "expected_assistant_calls": expected_calls,
        "compiled_inputs": str(compiled_path),
    }, indent=2), flush=True)
    if args.compile_only:
        return 0

    load_dotenv(PROJECT_DIR.parent / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is missing")
    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, timeout=240.0)
    semaphore = asyncio.Semaphore(args.concurrency)
    lock = asyncio.Lock()
    counts = {"calls": 0, "complete": 0, "errors": 0}

    async def run_one(model: str, item: dict[str, Any]) -> None:
        model_dir = safe_id(model)
        char_dir = safe_id(item["character"])
        cond = safe_id(item["condition_id"])
        raw_dir = run_dir / "raw" / model_dir / char_dir
        md_dir = run_dir / "markdown" / model_dir / char_dir
        raw_dir.mkdir(parents=True, exist_ok=True)
        md_dir.mkdir(parents=True, exist_ok=True)
        state_path = raw_dir / f"{cond}.json"
        md_path = md_dir / f"{cond}.md"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("compiled_user_turns_sha256") != item["compiled_user_turns_sha256"]:
                raise ValueError(f"Input hash mismatch for {model}/{item['character']}/{cond}")
            # Rebuild the exact committed history from completed response records.
            # This drops any unsaved/in-flight user message before a resumed request.
            state["messages"] = list(item["system_messages"])
            for prior in state.get("turn_records", []):
                state["messages"].append({"role": "user", "content": prior["user"]})
                state["messages"].append({"role": "assistant", "content": prior["assistant"]})
        else:
            state = {
                "schema_version": 1, "status": "running", "created_at": datetime.now(timezone.utc).isoformat(),
                **item, "model_configured": model,
                "system_prompt_text": item["system_messages"][0]["content"] if item["system_messages"] else None,
                "messages": list(item["system_messages"]), "turn_records": [],
            }
        if state.get("status") == "complete" and len(state["turn_records"]) == len(item["events"]):
            async with lock:
                counts["complete"] += 1
            return
        try:
            for event_index in range(len(state["turn_records"]), len(item["events"])):
                event = item["events"][event_index]
                state["messages"].append({"role": "user", "content": event["user"]})
                async with semaphore:
                    started = time.perf_counter()
                    result, raw = await model_turn(client, model, state["messages"], args)
                state["messages"].append({"role": "assistant", "content": result["assistant"]})
                record = {
                    "step_index": event_index + 1,
                    "source_turn": event["source_turn"],
                    "kind": event["kind"],
                    "user": event["user"],
                    **result,
                    "latency_seconds": round(time.perf_counter() - started, 3),
                    "raw_response": raw,
                }
                state["turn_records"].append(record)
                state["updated_at"] = datetime.now(timezone.utc).isoformat()
                state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                async with lock:
                    counts["calls"] += 1
                    print(f"[{counts['calls']}/{expected_calls}] {model} {item['character']} {cond} step={event_index + 1}", flush=True)
            state["status"] = "complete"
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            md_path.write_text(markdown(state), encoding="utf-8")
            async with lock:
                counts["complete"] += 1
        except Exception as exc:
            state["status"] = "error"
            state["error_type"] = type(exc).__name__
            state["error"] = str(exc)
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            async with lock:
                counts["errors"] += 1
                print(f"ERROR {model} {item['character']} {cond}: {exc}", flush=True)

    await asyncio.gather(*(run_one(model, item) for model in models for item in items))
    await client.close()
    summary = {
        "schema_version": 1, "models": models, "compiled_items_per_model": len(items),
        "expected_conversations": expected_conversations, "expected_assistant_calls": expected_calls,
        "completed_conversations": counts["complete"], "calls_accounted_for": counts["calls"],
        "errors": counts["errors"], "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if counts["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
