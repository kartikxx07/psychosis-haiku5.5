#!/usr/bin/env python3
"""Compile and run exact eight-turn transcript replays with logged interventions."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
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

from run_model_forensics_evals import api_model_id, parse_transcript, response_reasoning, safe_id


PROJECT_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = PROJECT_DIR / "model_forensics_evals" / "eight_turn_replay_manifest.json"
OUTPUT_ROOT = PROJECT_DIR / "eight_turn_ablation_transcripts"
MISMATCH_MARKERS = (
    "you said",
    "your words",
    "you're telling me",
    "you suggest",
    "you mentioned",
    "you've guided",
    "based on your",
    "your guidance",
    "your plan",
    "your willingness",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=OUTPUT_ROOT / "canonical_v1")
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--models", nargs="+")
    parser.add_argument("--characters", nargs="+")
    parser.add_argument("--conditions", nargs="+")
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=3000)
    parser.add_argument("--max-empty-retries", type=int, default=2)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--temperature", type=float, default=0.0)
    return parser.parse_args()


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def user_turns(source_path: Path, count: int) -> list[str]:
    messages = parse_transcript(source_path, count)
    turns = [message["content"] for message in messages if message["role"] == "user"]
    if len(turns) != count:
        raise ValueError(f"Expected {count} user turns in {source_path}, found {len(turns)}")
    return turns


def delete_once(text: str, deletion: str, label: str) -> str:
    count = text.count(deletion)
    if count != 1:
        raise ValueError(f"{label}: exact deletion must occur once, found {count}: {deletion!r}")
    return text.replace(deletion, "", 1)


def emotional_ablation(
    original: str, markers: list[str], label: str
) -> tuple[str, list[dict[str, Any]]]:
    parts = re.split(r"(?<=[.!?])([ \t\n]+)", original)
    transformed_parts: list[str] = []
    edits: list[dict[str, Any]] = []
    index = 0
    while index < len(parts):
        sentence = parts[index]
        separator = parts[index + 1] if index + 1 < len(parts) else ""
        lowered = sentence.lower()
        matched = [marker for marker in markers if marker.lower() in lowered]
        if matched and sentence.strip():
            edits.append(
                {
                    "operation": "delete_exact_sentence",
                    "text": sentence + separator,
                    "matched_markers": matched,
                }
            )
        else:
            transformed_parts.extend((sentence, separator))
        index += 2
    transformed = "".join(transformed_parts).strip()
    if not transformed:
        raise ValueError(f"{label}: emotional ablation removed the entire user turn")
    return transformed, edits


def compile_condition(
    source: dict[str, Any],
    originals: list[str],
    condition: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    turns = list(originals)
    edit_log: list[dict[str, Any]] = []

    if condition == "emotional_pressure_ablated":
        for turn_index, original in enumerate(originals, start=1):
            transformed, edits = emotional_ablation(
                original,
                manifest["emotional_sentence_markers"],
                f"{source['character']} turn {turn_index}",
            )
            turns[turn_index - 1] = transformed
            for edit in edits:
                edit_log.append({"turn": turn_index, **edit})
        if not edit_log:
            raise ValueError(f"{source['character']}: no emotional spans were found")

    elif condition in manifest["universal_appends"]:
        operation = manifest["universal_appends"][condition]
        turn_index = operation["turn"]
        addition = operation["text_template"]
        turns[turn_index - 1] = turns[turn_index - 1] + addition
        edit_log.append({"turn": turn_index, "operation": "append_exact", "text": addition})

    elif condition in manifest["identity_conditions"]:
        if not source.get("identity_conditions"):
            raise ValueError(f"{source['character']}: identity condition is not applicable")
        for operation in source.get("identity_deletions", []):
            turn_index = operation["turn"]
            turns[turn_index - 1] = delete_once(
                turns[turn_index - 1],
                operation["text"],
                f"{source['character']} {condition} turn {turn_index}",
            )
            edit_log.append(
                {"turn": turn_index, "operation": "delete_exact", "text": operation["text"]}
            )
        if condition != "expertise_ablated":
            template = manifest["identity_appends"][condition]
            addition = template.format(domain=source["domain"])
            turns[0] = turns[0] + addition
            edit_log.append({"turn": 1, "operation": "append_exact", "text": addition})

    elif condition != "control_verbatim":
        raise ValueError(f"Unknown condition: {condition}")

    mismatches = []
    for turn_index, text in enumerate(turns, start=1):
        found = [marker for marker in MISMATCH_MARKERS if marker in text.lower()]
        if found:
            mismatches.append({"turn": turn_index, "markers": found})
    digest = hashlib.sha256(
        json.dumps(turns, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "character": source["character"],
        "source_path": source["path"],
        "condition_id": condition,
        "user_turns": turns,
        "edit_log": edit_log,
        "source_assistant_reference_flags": mismatches,
        "compiled_user_turns_sha256": digest,
    }


def compile_inputs(manifest: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected_characters = set(args.characters or [source["character"] for source in manifest["sources"]])
    selected_conditions = set(
        args.conditions
        or (manifest["universal_conditions"] + manifest["identity_conditions"])
    )
    compiled: list[dict[str, Any]] = []
    for source in manifest["sources"]:
        if source["character"] not in selected_characters:
            continue
        originals = user_turns(PROJECT_DIR / source["path"], manifest["assistant_turns"])
        applicable = list(manifest["universal_conditions"])
        if source.get("identity_conditions"):
            applicable.extend(manifest["identity_conditions"])
        for condition in applicable:
            if condition not in selected_conditions:
                continue
            item = compile_condition(source, originals, condition, manifest)
            item["original_user_turns"] = originals
            compiled.append(item)
    return compiled


def conversation_markdown(record: dict[str, Any]) -> str:
    lines = [
        f"# {record['character']} — {record['condition_id']}",
        "",
        f"- Model: `{record['model_configured']}`",
        f"- Source: `{record['source_path']}`",
        f"- Status: `{record['status']}`",
        f"- Compiled user hash: `{record['compiled_user_turns_sha256']}`",
        "",
        "## Edit log",
        "",
        "```json",
        json.dumps(record["edit_log"], indent=2, ensure_ascii=False),
        "```",
    ]
    for turn in record["turn_records"]:
        lines.extend(
            [
                "",
                f"## Turn {turn['turn']}/8",
                "",
                "### User",
                "",
                turn["user"],
                "",
                "### Provider-returned reasoning",
                "",
                turn["reasoning"] or "_No provider-returned reasoning._",
                "",
                "### Assistant",
                "",
                turn["assistant"] or "_No final answer returned._",
            ]
        )
    return "\n".join(lines) + "\n"


async def model_turn(
    client: AsyncOpenAI,
    model_configured: str,
    messages: list[dict[str, str]],
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any]]:
    model = api_model_id(model_configured)
    last_error: Exception | None = None
    for transport_attempt in range(1, args.retries + 1):
        try:
            token_limit = args.max_tokens
            for empty_attempt in range(args.max_empty_retries + 1):
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=token_limit,
                    temperature=args.temperature,
                    extra_body={
                        "reasoning": {"effort": args.reasoning_effort, "exclude": False}
                    },
                )
                payload = response.model_dump(mode="json")
                choice = payload["choices"][0]
                message = choice["message"]
                answer = message.get("content") or ""
                if answer.strip():
                    return (
                        {
                            "assistant": answer,
                            "reasoning": response_reasoning(message),
                            "reasoning_details": message.get("reasoning_details"),
                            "finish_reason": choice.get("finish_reason"),
                            "usage": payload.get("usage") or {},
                            "provider": payload.get("provider"),
                            "model_returned": payload.get("model"),
                            "response_id": payload.get("id"),
                            "max_tokens_used": token_limit,
                            "empty_retries": empty_attempt,
                        },
                        payload,
                    )
                token_limit *= 2
            raise RuntimeError("Provider exhausted all token ceilings without a final answer")
        except Exception as error:
            last_error = error
            status = getattr(error, "status_code", None)
            if transport_attempt == args.retries or status not in {
                402,
                408,
                409,
                429,
                500,
                502,
                503,
                504,
            }:
                break
            if status == 402:
                wait_for = 125 + random.random() * 5
            else:
                wait_for = (20 if status == 429 else 2 ** (transport_attempt - 1)) + random.random()
            await asyncio.sleep(wait_for)
    assert last_error is not None
    raise last_error


async def main() -> int:
    args = parse_args()
    manifest = load_manifest()
    compiled = compile_inputs(manifest, args)
    models = args.models or manifest["models"]
    run_dir = args.run_dir.resolve()
    if not run_dir.is_relative_to(PROJECT_DIR):
        raise SystemExit("run-dir must be inside the project")
    run_dir.mkdir(parents=True, exist_ok=True)
    compiled_path = run_dir / "compiled_inputs.json"
    compiled_payload = {
        "schema_version": 1,
        "source_manifest": str(MANIFEST_PATH.relative_to(PROJECT_DIR)),
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "items": compiled,
    }
    compiled_path.write_text(
        json.dumps(compiled_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    total_conversations = len(compiled) * len(models)
    total_calls = total_conversations * manifest["assistant_turns"]
    print(
        json.dumps(
            {
                "compiled_items": len(compiled),
                "models": models,
                "conversations": total_conversations,
                "maximum_calls": total_calls,
                "compiled_inputs": str(compiled_path),
            },
            indent=2,
        ),
        flush=True,
    )
    if args.compile_only:
        return 0

    load_dotenv(PROJECT_DIR.parent / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is missing")
    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, timeout=240.0)
    semaphore = asyncio.Semaphore(args.concurrency)
    counter_lock = asyncio.Lock()
    counters = {"turns": 0, "errors": 0, "complete_conversations": 0}
    expected_turn_calls = total_calls

    async def run_conversation(model: str, item: dict[str, Any]) -> None:
        model_dir = safe_id(model)
        character_dir = safe_id(item["character"])
        condition_id = safe_id(item["condition_id"])
        target_dir = run_dir / "raw" / model_dir / character_dir
        md_dir = run_dir / "markdown" / model_dir / character_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        md_dir.mkdir(parents=True, exist_ok=True)
        state_path = target_dir / f"{condition_id}.json"
        md_path = md_dir / f"{condition_id}.md"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("compiled_user_turns_sha256") != item["compiled_user_turns_sha256"]:
                raise ValueError(f"Compiled input changed for {model} {item['character']} {condition_id}")
        else:
            state = {
                "schema_version": 1,
                "status": "running",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "model_configured": model,
                **item,
                "messages": [],
                "turn_records": [],
            }
        if state.get("status") == "complete" and len(state["turn_records"]) == 8:
            async with counter_lock:
                counters["complete_conversations"] += 1
                counters["turns"] += 8
            return
        start_turn = len(state["turn_records"]) + 1
        try:
            for turn_number in range(start_turn, 9):
                user_text = item["user_turns"][turn_number - 1]
                state["messages"].append({"role": "user", "content": user_text})
                async with semaphore:
                    started = time.perf_counter()
                    turn_result, raw_response = await model_turn(
                        client, model, state["messages"], args
                    )
                state["messages"].append(
                    {"role": "assistant", "content": turn_result["assistant"]}
                )
                state["turn_records"].append(
                    {
                        "turn": turn_number,
                        "user": user_text,
                        **turn_result,
                        "latency_seconds": round(time.perf_counter() - started, 3),
                        "raw_response": raw_response,
                    }
                )
                state["updated_at"] = datetime.now(timezone.utc).isoformat()
                state_path.write_text(
                    json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                async with counter_lock:
                    counters["turns"] += 1
                    print(
                        f"[{counters['turns']}/{expected_turn_calls}] {model} "
                        f"{item['character']} {item['condition_id']} turn={turn_number}",
                        flush=True,
                    )
            state["status"] = "complete"
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            state_path.write_text(
                json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            md_path.write_text(conversation_markdown(state), encoding="utf-8")
            async with counter_lock:
                counters["complete_conversations"] += 1
        except Exception as error:
            state["status"] = "error"
            state["error_type"] = type(error).__name__
            state["error"] = str(error)
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            state_path.write_text(
                json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            async with counter_lock:
                counters["errors"] += 1
                print(
                    f"ERROR {model} {item['character']} {item['condition_id']}: {error}",
                    flush=True,
                )

    await asyncio.gather(
        *(run_conversation(model, item) for model in models for item in compiled)
    )
    await client.close()
    summary = {
        "schema_version": 1,
        "models": models,
        "compiled_conditions": len(compiled),
        "expected_conversations": total_conversations,
        "expected_turn_calls": expected_turn_calls,
        "completed_conversations": counters["complete_conversations"],
        "turns_accounted_for": counters["turns"],
        "errors": counters["errors"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if counters["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
