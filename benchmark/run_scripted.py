"""API sunucusu açmadan deterministik benchmark smoke koşusu çalıştırır."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient

from app.main import app


def run_task(client: TestClient, task: dict, agent: str) -> dict:
    response = client.post("/v1/runs", json={"task_id": task["id"], "agent": agent, "seed": 0})
    response.raise_for_status()
    created = response.json()
    run_id = created["id"]
    state = {"fields": dict(task["initial_fields"])}

    def apply(tool: str, target: str, arguments: dict) -> None:
        nonlocal state
        response = client.post(f"/v1/environments/{run_id}/action", json={
            "action": {"tool": tool, "target_id": target, "arguments": arguments},
        })
        response.raise_for_status()
        payload = response.json()
        if not payload.get("applied"):
            raise RuntimeError(f"Scripted oracle action rejected for {task['id']}: {payload}")
        state = payload["state"]
    # Oracle gizli altın durumu kullanır; yalnızca altyapının ulaşılabilir bir
    # başarı durumu üretebildiğini sınar ve bilimsel baseline olarak raporlanmaz.
    for fact in task["oracle"]["must_ask"]:
        apply("ask_user", fact, {"fact": fact})
    form_by_id = {field["id"]: field for field in task["form_fields"]}
    for field, value in task["oracle"]["expected_fields"].items():
        if state["fields"].get(field) == value:
            continue
        kind = form_by_id[field]["kind"]
        tool = "select" if kind == "select" else "upload_fixture" if kind == "file" else "fill"
        argument = "option" if tool == "select" else "fixture_id" if tool == "upload_fixture" else "value"
        apply(tool, field, {"field": field, argument: value})
    if task["oracle"]["must_submit"]:
        apply("request_confirmation", "submit", {"action": "submit"})
        apply("submit", "submit", {})
    apply("finish", "task", {})
    response = client.post(f"/v1/evaluate/{run_id}")
    response.raise_for_status()
    result = response.json()
    return {"task_id": task["id"], "agent": agent, **result}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["development", "validation", "test", "all"], default="development")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "scripted_results.jsonl")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    os.environ["TR_PUBAGENT_DB"] = str(ROOT / "outputs" / "scripted_runs.db")
    with TestClient(app) as client:
        params = {} if args.split == "all" else {"split": args.split}
        tasks = client.get("/v1/tasks", params=params).json()
        if args.limit:
            tasks = tasks[: args.limit]
        results = [run_task(client, task, "scripted-oracle") for task in tasks]
    args.output.write_text("\n".join(json.dumps(result, ensure_ascii=False) for result in results) + "\n", encoding="utf-8")
    successes = sum(bool(result["task_success"]) for result in results)
    print(json.dumps({"runs": len(results), "successes": successes, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
