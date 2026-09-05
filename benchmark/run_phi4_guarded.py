"""Phi-4-mini-instruct + kural tabanlı yürütme koruması deney koşucusu."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.guard import check_action
from app.guarded_policy import action_signature, enforced_action, public_action_error, terminal_action
from app.main import app
from app.models import AuthorizationContract, GuardCheckRequest, GuardDecisionType
from run_phi4 import InvalidActionError, MODEL_ID, Phi4Policy


PROMPT_VERSION = "guarded-v1"


def run_task(client: TestClient, task: dict[str, Any], policy: Phi4Policy, seed: int) -> dict[str, Any]:
    created = client.post(
        "/v1/runs", json={"task_id": task["id"], "agent": "tr-pubguard", "seed": seed}
    ).json()
    run_id = created["id"]
    contract = AuthorizationContract.model_validate(task["authorization"])
    trace: list[dict[str, Any]] = []
    applied_signatures: set[str] = set()
    feedback = ""
    invalid_action = False
    semantic_errors = 0
    guard_blocks = 0
    guard_enforcements = 0
    termination = "MAX_STEPS"
    started = time.perf_counter()

    for _ in range(task["max_steps"] - 1):
        observation = client.get(f"/v1/environments/{run_id}/observation").json()
        proposed = terminal_action(observation)
        attempts: list[dict[str, Any]] = []
        controller_action = proposed is not None
        if proposed is None:
            try:
                proposed, attempts = policy.next_action(observation, feedback=feedback)
            except InvalidActionError as error:
                trace.append({"observation": observation, "attempts": error.attempts})
                invalid_action = True
                termination = "INVALID_ACTION"
                break

        validation_error = public_action_error(proposed, observation, applied_signatures)
        if validation_error:
            guard_blocks += 1
            feedback = validation_error
            trace.append({
                "observation": observation, "attempts": attempts,
                "proposed_action": proposed.model_dump(mode="json"),
                "guard_stage": "public_contract", "guard_error": validation_error,
            })
            continue

        state = observation.get("state", {})
        decision = check_action(GuardCheckRequest(
            user_request=task["user_request"], action=proposed, contract=contract,
            known_facts=state.get("fields", {}),
            confirmed_actions=state.get("confirmed_actions", []),
        ))
        action = proposed
        if decision.decision != GuardDecisionType.ALLOW:
            guard_blocks += 1
            replacement = enforced_action(decision, observation)
            if replacement is None:
                response = client.post(
                    f"/v1/environments/{run_id}/action",
                    json={
                        "action": proposed.model_dump(mode="json"),
                        "guard": decision.model_dump(mode="json"),
                    },
                )
                trace.append({
                    "observation": observation, "attempts": attempts,
                    "proposed_action": proposed.model_dump(mode="json"),
                    "guard": decision.model_dump(mode="json"),
                    "environment_status": response.status_code,
                    "environment_result": response.json(),
                })
                feedback = decision.explanation + " Kanıt: " + ", ".join(decision.evidence)
                continue
            action = replacement
            guard_enforcements += 1

        response = client.post(
            f"/v1/environments/{run_id}/action",
            json={"action": action.model_dump(mode="json")},
        )
        environment_result = response.json() if response.status_code == 200 else {"error": response.text}
        trace.append({
            "observation": observation, "attempts": attempts,
            "proposed_action": proposed.model_dump(mode="json"),
            "action": action.model_dump(mode="json"),
            "controller_action": controller_action,
            "guard": decision.model_dump(mode="json"),
            "environment_status": response.status_code,
            "environment_result": environment_result,
        })
        if response.status_code != 200:
            termination = "ENVIRONMENT_ERROR"
            break
        if not environment_result.get("applied", True) and environment_result.get("error"):
            semantic_errors += 1
            feedback = str(environment_result["error"])
            if semantic_errors >= 3:
                invalid_action = True
                termination = "INVALID_ACTION"
                break
            continue
        applied_signatures.add(action_signature(action))
        feedback = ""
        if action.tool == "finish":
            termination = "FINISHED"
            break

    result = client.post(f"/v1/evaluate/{run_id}").json()
    generated_tokens = sum(
        int(attempt.get("generated_tokens", 0))
        for step in trace for attempt in step.get("attempts", [])
    )
    return {
        "task_id": task["id"], "run_id": run_id, "agent": "tr-pubguard",
        "model": policy.model_id,
        "model_revision": getattr(policy.model.config, "_commit_hash", None),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "prompt_version": PROMPT_VERSION,
        "generation": {
            "do_sample": False, "max_new_tokens": policy.max_new_tokens,
            "quantization": "nf4-4bit" if policy.four_bit else "float16",
        },
        "seed": seed, "termination": termination, "invalid_action": invalid_action,
        "semantic_errors": semantic_errors, "guard_blocks": guard_blocks,
        "guard_enforcements": guard_enforcements,
        "latency_seconds": round(time.perf_counter() - started, 3),
        "steps": len(trace), "generated_tokens": generated_tokens, "trace": trace,
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["development", "validation"], default="development")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "phi4_guarded_results.jsonl")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit en az 1 olmalı")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    os.environ["TR_PUBAGENT_DB"] = str(ROOT / "outputs" / "phi4_guarded_runs.db")

    existing: list[dict[str, Any]] = []
    if args.output.exists() and not args.overwrite:
        existing = [json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines() if line.strip()]
    completed = {
        item["task_id"] for item in existing
        if item.get("model") == args.model and item.get("seed") == args.seed
    }

    import torch
    torch.manual_seed(args.seed)
    policy = Phi4Policy(model_id=args.model, four_bit=not args.no_4bit)
    with TestClient(app) as client:
        selected = client.get("/v1/tasks", params={"split": args.split}).json()[:args.limit]
        pending = [task for task in selected if task["id"] not in completed]
        results = existing
        if completed:
            print(f"{len(completed)} tamamlanmış görev atlanıyor.", flush=True)
        for index, task in enumerate(pending, start=1):
            print(f"[{index}/{len(pending)}] {task['id']}", flush=True)
            results.append(run_task(client, task, policy, args.seed))
            args.output.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n",
                encoding="utf-8",
            )

    selected_ids = {task["id"] for task in selected}
    chosen = [item for item in results if item.get("task_id") in selected_ids and item.get("model") == args.model and item.get("seed") == args.seed]
    print(json.dumps({
        "runs": len(chosen),
        "successes": sum(bool(item["task_success"]) for item in chosen),
        "invalid_actions": sum(bool(item["invalid_action"]) for item in chosen),
        "guard_blocks": sum(int(item["guard_blocks"]) for item in chosen),
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
