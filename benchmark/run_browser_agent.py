"""Real-browser external-agent runner; separate from frozen API experiments."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.browser_env import BrowserActionError, SafeBrowserEnvironment
from app.external_agent import ExternalAgentError, HttpAgentPolicy
from app.guard import check_action
from app.guarded_policy import action_signature, enforced_action, public_action_error
from app.models import GuardCheckRequest, GuardDecision, GuardDecisionType, RiskLabel
from app.tasks import TASK_BY_ID


class BrowserPolicyError(RuntimeError):
    """A browser policy could not return a schema-valid action."""

    def __init__(self, message: str, attempts: list[dict] | None = None):
        super().__init__(message)
        self.attempts = attempts or []


async def run_task(
    api, browser, policy, task_id: str, max_steps: int, seed: int = 0,
    *, guarded: bool = False, agent_name: str = "browser-external-v1",
) -> dict:
    created = await api.post("/v1/runs", json={"task_id": task_id, "agent": agent_name, "seed": seed})
    created.raise_for_status()
    run_id = created.json()["id"]
    obs = await browser.open(f"/browser/runs/{run_id}")
    trace, feedback, termination = [], "", "MAX_STEPS"
    guard_blocks = 0
    guard_enforcements = 0
    applied_signatures: set[str] = set()
    start = time.monotonic()
    for _ in range(max_steps - 1):
        before = asdict(obs)
        try:
            # No task oracle, authorization gold, response policy or API state is
            # passed to the agent. Its input is the rendered accessibility tree.
            proposed, agent_metadata = await asyncio.to_thread(
                policy.next_action, task_id, before, feedback
            )
        except (ExternalAgentError, BrowserPolicyError) as error:
            trace.append({
                "observation": before, "error": str(error),
                "agent_metadata": {"attempts": getattr(error, "attempts", [])},
            })
            termination = "AGENT_ERROR"
            break
        action = proposed
        guard = None
        if guarded:
            internal_response = await api.get(f"/v1/environments/{run_id}/observation")
            internal_response.raise_for_status()
            internal = internal_response.json()
            state = internal.get("state", {})
            contract_error = public_action_error(proposed, internal, applied_signatures)
            if contract_error:
                guard = GuardDecision(
                    decision=GuardDecisionType.BLOCK,
                    risk_labels=[RiskLabel.UNAUTHORIZED],
                    confidence=0.99,
                    explanation="Eylem görünür görev sözleşmesinin dışında.",
                    evidence=[f"public_contract:{contract_error}"],
                )
            else:
                guard = check_action(GuardCheckRequest(
                    user_request=TASK_BY_ID[task_id].user_request,
                    action=proposed,
                    contract=TASK_BY_ID[task_id].authorization,
                    known_facts=state.get("fields", {}),
                    confirmed_actions=state.get("confirmed_actions", []),
                ))
            if guard.decision != GuardDecisionType.ALLOW:
                guard_blocks += 1
                replacement = enforced_action(guard, internal)
                if replacement is None:
                    feedback = guard.explanation + " Kanıt: " + ", ".join(guard.evidence)
                    trace.append({
                        "observation": before,
                        "proposed_action": proposed.model_dump(mode="json"),
                        "action": None,
                        "guard": guard.model_dump(mode="json"),
                        "agent_metadata": agent_metadata,
                        "error": feedback,
                    })
                    continue
                action = replacement
                guard_enforcements += 1
        try:
            obs = await browser.act(action)
            applied_signatures.add(action_signature(action))
            feedback = ""
        except BrowserActionError as error:
            feedback = str(error)
        trace.append({
            "observation": before,
            "proposed_action": proposed.model_dump(mode="json"),
            "action": action.model_dump(mode="json"),
            "guard": guard.model_dump(mode="json") if guard else None,
            "agent_metadata": agent_metadata,
            "error": feedback or None,
        })
        if obs.status != "running":
            termination = "FINISHED" if action.tool == "finish" and not feedback else obs.status.upper()
            break
    evaluation = await api.post(f"/v1/evaluate/{run_id}")
    evaluation.raise_for_status()
    return {
        "experiment": "browser-external-v1", "environment": "playwright-html-v1",
        "task_id": task_id, "seed": seed, "termination": termination,
        "agent": agent_name, "guarded": guarded,
        "guard_blocks": guard_blocks, "guard_enforcements": guard_enforcements,
        "generated_tokens": sum(
            int(step.get("agent_metadata", {}).get("generated_tokens", 0))
            for step in trace
        ),
        "latency_seconds": round(time.monotonic() - start, 3),
        "trace": trace, **evaluation.json(),
    }


async def run(args) -> None:
    policy = HttpAgentPolicy(args.agent_url)  # Loopback only; remote upload is not implicit.
    browser = SafeBrowserEnvironment(args.base_url)
    unknown = set(args.task_ids) - TASK_BY_ID.keys()
    if unknown:
        raise ValueError(f"Unknown tasks: {sorted(unknown)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects old experiment files from accidental overwrite.
    with args.output.open("x", encoding="utf-8") as output:
        async with httpx.AsyncClient(base_url=args.base_url, timeout=30) as api, browser:
            for task_id in args.task_ids:
                result = await run_task(api, browser, policy, task_id, TASK_BY_ID[task_id].max_steps, args.seed)
                output.write(json.dumps(result, ensure_ascii=False) + "\n")
                output.flush()
                print(json.dumps({"task_id": task_id, "success": result["task_success"], "termination": result["termination"]}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--agent-url", required=True)
    parser.add_argument("--task-ids", nargs="+", default=["BUR-001"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/browser/external-v1.jsonl")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
