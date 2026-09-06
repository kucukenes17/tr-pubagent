"""Rule / ML / Hybrid Guard OOD ablation koşucusu."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient

from app.main import TASK_BY_ID, app
from app.ml_guard import XLMRRiskClassifier
from benchmark.robustness_tasks import ROBUSTNESS_TASKS
from benchmark.run_phi4 import MODEL_ID
from benchmark.run_phi4_guarded import GroundedPhi4Policy, run_task


FILES = {
    "rule": "phi4_guarded_ood_v2_1.jsonl",
    "ml": "phi4_ml_guard_ood_v2_2.jsonl",
    "hybrid": "phi4_hybrid_guard_ood_v2_2.jsonl",
}
AGENTS = {"rule": "rule-guard", "ml": "ml-guard", "hybrid": "tr-pubguard"}


def read_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--systems", nargs="+", choices=list(FILES), default=["rule", "ml", "hybrid"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17, 42])
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--ml-model-path", type=Path)
    parser.add_argument("--ml-threshold", type=float, default=0.80)
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "robustness")
    args = parser.parse_args()
    if any(system in {"ml", "hybrid"} for system in args.systems) and args.ml_model_path is None:
        parser.error("ML veya Hybrid koşusu için --ml-model-path gerekli")
    if not 0 < args.ml_threshold <= 1:
        parser.error("--ml-threshold 0 ile 1 arasında olmalı")

    selected = ROBUSTNESS_TASKS[:args.limit]
    TASK_BY_ID.update({task.id: task for task in selected})
    tasks = [task.model_dump(mode="json") for task in selected]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TR_PUBAGENT_DB"] = str(args.output_dir / "guard_ablation_runs.db")

    policy = GroundedPhi4Policy(model_id=args.model, four_bit=not args.no_4bit)
    classifier = XLMRRiskClassifier(args.ml_model_path) if args.ml_model_path else None
    with TestClient(app) as client:
        for system in args.systems:
            output = args.output_dir / FILES[system]
            rows = read_rows(output)
            completed = {(row.get("task_id"), row.get("seed"), row.get("model"), row.get("guard_strategy")) for row in rows}
            total = len(tasks) * len(args.seeds)
            index = 0
            for seed in args.seeds:
                import torch
                torch.manual_seed(seed)
                for task in tasks:
                    index += 1
                    key = (task["id"], seed, args.model, system)
                    if key in completed:
                        print(f"[{index}/{total}] {system} seed={seed} {task['id']} (atlandı)", flush=True)
                        continue
                    print(f"[{index}/{total}] {system} seed={seed} {task['id']}", flush=True)
                    row = run_task(
                        client, task, policy, seed,
                        prompt_version="guarded-v2.1-grounded" if system == "rule" else "guarded-v2.2-grounded",
                        guard_strategy=system, risk_classifier=classifier,
                        ml_threshold=args.ml_threshold, agent_name=AGENTS[system],
                    )
                    row["evaluation_suite"] = "human-authored-ood-v1"
                    row["ml_model_path"] = str(args.ml_model_path) if classifier else None
                    rows.append(row)
                    write_rows(output, rows)
            chosen = [row for row in rows if row.get("model") == args.model and row.get("seed") in args.seeds]
            print(json.dumps({
                "system": system, "runs": len(chosen),
                "successes": sum(bool(row.get("task_success")) for row in chosen),
                "violations": sum(len(row.get("violations", [])) for row in chosen),
                "output": str(output),
            }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
