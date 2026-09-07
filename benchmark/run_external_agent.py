"""Kullanıcının HTTP ajanını TR-PubBench ortamında çalıştırır.

Bu CLI yerel çalışır; TR-PubAgent API sunucusunun kullanıcı URL'lerine istek
atmasını gerektirmez. Böylece SSRF yüzeyi oluşturulmaz.
"""

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

from fastapi.testclient import TestClient

from app.external_agent import ExternalAgentError, HttpAgentPolicy, sanitized_agent_url
from app.guard import check_action
from app.guarded_policy import action_signature, enforced_action, public_action_error, terminal_action
from app.main import app
from app.models import AuthorizationContract, GuardCheckRequest, GuardDecisionType, ProposedAction


PROTOCOL_VERSION = "tr-pubagent.agent.v1"
RUNNER_VERSION = "external-agent-runner-v1"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_task(
    client: TestClient,
    task: dict[str, Any],
    policy: HttpAgentPolicy,
    seed: int,
    agent_name: str,
    guard_mode: str,
) -> dict[str, Any]:
    created_response = client.post(
        "/v1/runs", json={"task_id": task["id"], "agent": agent_name, "seed": seed}
    )
    created_response.raise_for_status()
    run_id = created_response.json()["id"]
    contract = AuthorizationContract.model_validate(task["authorization"])
    trace: list[dict[str, Any]] = []
    applied_signatures: set[str] = set()
    feedback = ""
    semantic_errors = 0
    guard_blocks = 0
    guard_enforcements = 0
    invalid_action = False
    termination = "MAX_STEPS"
    started = time.perf_counter()

    for _ in range(task["max_steps"] - 1):
        observation = client.get(f"/v1/environments/{run_id}/observation").json()
        controller_action = False
        proposed: ProposedAction | None = None
        metadata: dict[str, Any] = {}
        if guard_mode == "rule":
            proposed = terminal_action(observation)
            controller_action = proposed is not None
        if proposed is None:
            try:
                proposed, metadata = policy.next_action(task["id"], observation, feedback)
            except ExternalAgentError as error:
                trace.append({"observation": observation, "agent_error": str(error)})
                invalid_action = True
                termination = "AGENT_ERROR"
                break

        action = proposed
        guard_payload: dict[str, Any] | None = None
        if guard_mode == "rule":
            validation_error = public_action_error(proposed, observation, applied_signatures)
            if validation_error:
                guard_blocks += 1
                feedback = validation_error
                trace.append({
                    "observation": observation,
                    "proposed_action": proposed.model_dump(mode="json"),
                    "agent_metadata": metadata,
                    "guard_stage": "public_contract",
                    "guard_error": validation_error,
                })
                continue

            state = observation.get("state", {})
            decision = check_action(GuardCheckRequest(
                user_request=task["user_request"],
                action=proposed,
                contract=contract,
                known_facts=state.get("fields", {}),
                confirmed_actions=state.get("confirmed_actions", []),
            ))
            guard_payload = decision.model_dump(mode="json")
            if decision.decision != GuardDecisionType.ALLOW:
                guard_blocks += 1
                replacement = enforced_action(decision, observation)
                if replacement is None:
                    response = client.post(
                        f"/v1/environments/{run_id}/action",
                        json={
                            "action": proposed.model_dump(mode="json"),
                            "guard": guard_payload,
                        },
                    )
                    trace.append({
                        "observation": observation,
                        "proposed_action": proposed.model_dump(mode="json"),
                        "agent_metadata": metadata,
                        "guard": guard_payload,
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
        environment_result = (
            response.json() if response.status_code == 200 else {"error": response.text}
        )
        trace.append({
            "observation": observation,
            "proposed_action": proposed.model_dump(mode="json"),
            "action": action.model_dump(mode="json"),
            "agent_metadata": metadata,
            "controller_action": controller_action,
            "guard": guard_payload,
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

    evaluation = client.post(f"/v1/evaluate/{run_id}").json()
    return {
        "task_id": task["id"],
        "run_id": run_id,
        "agent": agent_name,
        "agent_endpoint": sanitized_agent_url(policy.endpoint),
        "protocol_version": PROTOCOL_VERSION,
        "runner_version": RUNNER_VERSION,
        "guard_mode": guard_mode,
        "git_commit": git_commit(),
        "seed": seed,
        "termination": termination,
        "invalid_action": invalid_action,
        "semantic_errors": semantic_errors,
        "guard_blocks": guard_blocks,
        "guard_enforcements": guard_enforcements,
        "latency_seconds": round(time.perf_counter() - started, 3),
        "steps": len(trace),
        "trace": trace,
        **evaluation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bir HTTP ajanını TR-PubBench üzerinde değerlendir")
    parser.add_argument("--agent-url", required=True, help="v1 /act endpoint'i")
    parser.add_argument("--agent-name", default="external-agent")
    parser.add_argument("--split", choices=["development", "validation", "test"], default="development")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--task-ids", nargs="*", default=[])
    parser.add_argument("--guard", choices=["none", "rule"], default="none")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "outputs" / "external_agent_results.jsonl",
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit en az 1 olmalı")
    if args.timeout <= 0:
        parser.error("--timeout sıfırdan büyük olmalı")

    try:
        policy = HttpAgentPolicy(
            endpoint=args.agent_url,
            timeout_seconds=args.timeout,
            allow_remote=args.allow_remote,
        )
    except ValueError as error:
        parser.error(str(error))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    os.environ["TR_PUBAGENT_DB"] = str(ROOT / "outputs" / "external_agent_runs.db")
    existing: list[dict[str, Any]] = []
    if args.output.exists() and not args.overwrite:
        existing = [
            json.loads(line)
            for line in args.output.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    endpoint_for_log = sanitized_agent_url(args.agent_url)
    completed = {
        (item.get("task_id"), item.get("seed"))
        for item in existing
        if item.get("agent") == args.agent_name
        and item.get("agent_endpoint") == endpoint_for_log
        and item.get("guard_mode") == args.guard
    }

    with TestClient(app) as client:
        split_tasks = client.get("/v1/tasks", params={"split": args.split}).json()
        if args.task_ids:
            requested = set(args.task_ids)
            selected = [task for task in split_tasks if task["id"] in requested]
            missing = requested - {task["id"] for task in selected}
            if missing:
                parser.error(f"Split içinde bulunamayan task id: {sorted(missing)}")
        else:
            selected = split_tasks[: args.limit]
        pending = [task for task in selected if (task["id"], args.seed) not in completed]
        results = existing
        if len(selected) != len(pending):
            print(f"{len(selected) - len(pending)} tamamlanmış koşu atlanıyor.", flush=True)
        for index, task in enumerate(pending, start=1):
            print(f"[{index}/{len(pending)}] {task['id']}", flush=True)
            results.append(run_task(
                client, task, policy, args.seed, args.agent_name, args.guard
            ))
            args.output.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n",
                encoding="utf-8",
            )

    selected_ids = {task["id"] for task in selected}
    chosen = [
        item for item in results
        if item.get("task_id") in selected_ids
        and item.get("seed") == args.seed
        and item.get("agent") == args.agent_name
        and item.get("agent_endpoint") == endpoint_for_log
        and item.get("guard_mode") == args.guard
    ]
    print(json.dumps({
        "runs": len(chosen),
        "successes": sum(bool(item.get("task_success")) for item in chosen),
        "invalid_actions": sum(bool(item.get("invalid_action")) for item in chosen),
        "violations": sum(len(item.get("violations", [])) for item in chosen),
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
