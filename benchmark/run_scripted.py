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
    created = client.post("/v1/runs", json={"task_id": task["id"], "agent": agent, "seed": 0}).json()
    run_id = created["id"]
    # Oracle gizli altın durumu kullanır; yalnızca altyapının ulaşılabilir bir
    # başarı durumu üretebildiğini sınar ve bilimsel baseline olarak raporlanmaz.
    for fact in task["oracle"]["must_ask"]:
        client.post(f"/v1/environments/{run_id}/action", json={"action": {"tool": "ask_user", "target_id": fact, "arguments": {"fact": fact}}})
    for field, value in task["oracle"]["expected_fields"].items():
        client.post(f"/v1/environments/{run_id}/action", json={"action": {"tool": "fill", "target_id": field, "arguments": {"field": field, "value": value}}})
    if task["oracle"]["must_submit"]:
        client.post(f"/v1/environments/{run_id}/action", json={"action": {"tool": "request_confirmation", "target_id": "submit", "arguments": {"action": "submit"}}})
        client.post(f"/v1/environments/{run_id}/action", json={"action": {"tool": "submit", "target_id": "submit", "arguments": {}}})
    client.post(f"/v1/environments/{run_id}/action", json={"action": {"tool": "finish", "target_id": "task", "arguments": {}}})
    result = client.post(f"/v1/evaluate/{run_id}").json()
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
