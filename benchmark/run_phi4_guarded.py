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
from app.evidence import evidence_candidates, evidence_prompt, parse_evidence_values
from app.main import app
from app.models import AuthorizationContract, GuardCheckRequest, GuardDecisionType, ProposedAction
from run_phi4 import InvalidActionError, MODEL_ID, Phi4Policy


PROMPT_VERSION = "guarded-v1"
FROZEN_V2_ALGORITHM = "guarded-v2.1-frozen@91f2fb1"


class GroundedPhi4Policy(Phi4Policy):
    """İlk ajan adımından önce görünür kullanıcı metnindeki açık alan değerlerini bağlar."""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.evidence_attempted_states: set[str] = set()
        self.evidence_diagnostics: dict[str, list[dict[str, Any]]] = {}

    def next_action(
        self, observation: dict[str, Any], feedback: str = ""
    ) -> tuple[Any, list[dict[str, Any]]]:
        run_id = str(observation.get("run_id", ""))
        fields = evidence_candidates(observation)
        attempt_key = json.dumps({
            "run_id": run_id,
            "fields": [field["id"] for field in fields],
            "known_fields": observation.get("state", {}).get("fields", {}),
        }, ensure_ascii=False, sort_keys=True)
        if fields and attempt_key not in self.evidence_attempted_states:
            self.evidence_attempted_states.add(attempt_key)
            raw = self.generate([{
                "role": "user",
                "content": evidence_prompt(observation["task"], fields),
            }])
            generated_tokens = len(self.tokenizer.encode(raw, add_special_tokens=False))
            values = parse_evidence_values(raw, fields)
            diagnostic = {
                "candidates": fields,
                "raw": raw,
                "parsed_values": values,
                "generated_tokens": generated_tokens,
            }
            self.evidence_diagnostics.setdefault(run_id, []).append(diagnostic)
            if values:
                field_id = next(field["id"] for field in fields if field["id"] in values)
                return ProposedAction(
                    tool="fill", target_id=field_id,
                    arguments={"value": values[field_id]},
                    evidence_refs=["user_request:explicit_value"],
                    reason="Kullanıcı isteğinde açıkça verilen değer görünür form alanına bağlandı.",
                ), [{
                    "stage": "evidence_extraction", "raw": raw, "error": "",
                    "generated_tokens": generated_tokens,
                }]
        return super().next_action(observation, feedback=feedback)


def run_task(
    client: TestClient,
    task: dict[str, Any],
    policy: Phi4Policy,
    seed: int,
    prompt_version: str = PROMPT_VERSION,
) -> dict[str, Any]:
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
    evidence_diagnostic = getattr(policy, "evidence_diagnostics", {}).get(run_id, [])
    generated_tokens = sum(
        int(attempt.get("generated_tokens", 0))
        for step in trace for attempt in step.get("attempts", [])
        if attempt.get("stage") != "evidence_extraction"
    )
    generated_tokens += sum(
        int(item.get("generated_tokens", 0)) for item in evidence_diagnostic
    )
    return {
        "task_id": task["id"], "run_id": run_id, "agent": "tr-pubguard",
        "model": policy.model_id,
        "model_revision": getattr(policy.model.config, "_commit_hash", None),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "prompt_version": prompt_version,
        "algorithm_version": (
            FROZEN_V2_ALGORITHM if prompt_version == "guarded-v2.1-grounded"
            else "guarded-v1@418eafc"
        ),
        "generation": {
            "do_sample": False, "max_new_tokens": policy.max_new_tokens,
            "quantization": "nf4-4bit" if policy.four_bit else "float16",
        },
        "seed": seed, "termination": termination, "invalid_action": invalid_action,
        "semantic_errors": semantic_errors, "guard_blocks": guard_blocks,
        "guard_enforcements": guard_enforcements,
        "latency_seconds": round(time.perf_counter() - started, 3),
        "steps": len(trace), "generated_tokens": generated_tokens, "trace": trace,
        "evidence_extraction": evidence_diagnostic,
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["development", "validation", "test"], default="development")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--evidence-grounding", action="store_true")
    parser.add_argument("--task-ids", nargs="*", default=[])
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
    prompt_version = "guarded-v2.1-grounded" if args.evidence_grounding else PROMPT_VERSION
    completed = {
        item["task_id"] for item in existing
        if item.get("model") == args.model
        and item.get("seed") == args.seed
        and item.get("prompt_version") == prompt_version
    }

    import torch
    torch.manual_seed(args.seed)
    policy_class = GroundedPhi4Policy if args.evidence_grounding else Phi4Policy
    policy = policy_class(model_id=args.model, four_bit=not args.no_4bit)
    with TestClient(app) as client:
        split_tasks = client.get("/v1/tasks", params={"split": args.split}).json()
        if args.task_ids:
            requested = set(args.task_ids)
            selected = [task for task in split_tasks if task["id"] in requested]
            missing_ids = requested - {task["id"] for task in selected}
            if missing_ids:
                parser.error(f"Split içinde bulunamayan task id: {sorted(missing_ids)}")
        else:
            selected = split_tasks[:args.limit]
        pending = [task for task in selected if task["id"] not in completed]
        results = existing
        if completed:
            print(f"{len(completed)} tamamlanmış görev atlanıyor.", flush=True)
        for index, task in enumerate(pending, start=1):
            print(f"[{index}/{len(pending)}] {task['id']}", flush=True)
            results.append(run_task(client, task, policy, args.seed, prompt_version=prompt_version))
            args.output.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n",
                encoding="utf-8",
            )

    selected_ids = {task["id"] for task in selected}
    chosen = [
        item for item in results
        if item.get("task_id") in selected_ids
        and item.get("model") == args.model
        and item.get("seed") == args.seed
        and item.get("prompt_version") == prompt_version
    ]
    print(json.dumps({
        "runs": len(chosen),
        "successes": sum(bool(item["task_success"]) for item in chosen),
        "invalid_actions": sum(bool(item["invalid_action"]) for item in chosen),
        "guard_blocks": sum(int(item["guard_blocks"]) for item in chosen),
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
