"""24 insan yazımı OOD görevde çok-seed Unguarded/Guarded koşusu.

Kaggle T4 kullanım örneği:
python -m benchmark.run_robustness --seeds 0 17 42 --systems unguarded guarded
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient

from app.main import TASK_BY_ID, app
from benchmark.robustness_tasks import ROBUSTNESS_TASKS
from benchmark.run_phi4 import MODEL_ID, Phi4Policy, run_task as run_unguarded_task
from benchmark.run_phi4_guarded import GroundedPhi4Policy, run_task as run_guarded_task


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def run_system(
    *, name: str, policy: Phi4Policy, runner: Callable[..., dict[str, Any]], tasks: list[dict[str, Any]],
    seeds: list[int], output: Path, model: str, guarded: bool,
) -> None:
    rows = load_rows(output)
    completed = {(row.get("task_id"), row.get("seed"), row.get("model")) for row in rows}
    total = len(tasks) * len(seeds)
    current = 0
    with TestClient(app) as client:
        for seed in seeds:
            import torch
            torch.manual_seed(seed)
            for task in tasks:
                current += 1
                key = (task["id"], seed, model)
                if key in completed:
                    print(f"[{current}/{total}] {name} seed={seed} {task['id']} (atlandı)", flush=True)
                    continue
                print(f"[{current}/{total}] {name} seed={seed} {task['id']}", flush=True)
                if guarded:
                    result = runner(client, task, policy, seed, prompt_version="guarded-v2.1-grounded")
                else:
                    result = runner(client, task, policy, seed)
                result["evaluation_suite"] = "human-authored-ood-v1"
                rows.append(result)
                save_rows(output, rows)
    selected = [row for row in rows if row.get("model") == model and row.get("seed") in seeds]
    print(json.dumps({
        "system": name,
        "runs": len(selected),
        "successes": sum(bool(row.get("task_success")) for row in selected),
        "invalid_actions": sum(bool(row.get("invalid_action")) for row in selected),
        "violations": sum(len(row.get("violations", [])) for row in selected),
        "output": str(output),
    }, ensure_ascii=False), flush=True)


def release_model() -> None:
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17, 42])
    parser.add_argument("--systems", nargs="+", choices=["unguarded", "guarded"], default=["unguarded", "guarded"])
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "robustness")
    args = parser.parse_args()
    if not 1 <= args.limit <= len(ROBUSTNESS_TASKS):
        parser.error(f"--limit 1 ile {len(ROBUSTNESS_TASKS)} arasında olmalı")
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("--seeds tekrar eden değer içeremez")

    selected_models = ROBUSTNESS_TASKS[:args.limit]
    TASK_BY_ID.update({task.id: task for task in selected_models})
    tasks = [task.model_dump(mode="json") for task in selected_models]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TR_PUBAGENT_DB"] = str(args.output_dir / "robustness_runs.db")

    if "unguarded" in args.systems:
        policy = Phi4Policy(model_id=args.model, four_bit=not args.no_4bit)
        run_system(
            name="unguarded-v1", policy=policy, runner=run_unguarded_task, tasks=tasks,
            seeds=args.seeds, output=args.output_dir / "phi4_unguarded_ood_v1.jsonl",
            model=args.model, guarded=False,
        )
        del policy
        release_model()

    if "guarded" in args.systems:
        policy = GroundedPhi4Policy(model_id=args.model, four_bit=not args.no_4bit)
        run_system(
            name="guarded-v2.1", policy=policy, runner=run_guarded_task, tasks=tasks,
            seeds=args.seeds, output=args.output_dir / "phi4_guarded_ood_v2_1.jsonl",
            model=args.model, guarded=True,
        )
        del policy
        release_model()


if __name__ == "__main__":
    main()
