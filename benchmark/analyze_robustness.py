"""Çok-seed OOD koşularını eşleştirir ve küme-bootstrap özeti üretir."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from benchmark.robustness_tasks import ROBUSTNESS_TASK_BY_ID

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = sum(bool(row.get("task_success")) for row in rows)
    violations = Counter(label for row in rows for label in row.get("violations", []))
    return {
        "runs": len(rows),
        "successes": successes,
        "success_rate": successes / len(rows),
        "success_ci95_wilson": wilson(successes, len(rows)),
        "invalid_actions": sum(bool(row.get("invalid_action")) for row in rows),
        "violations": dict(sorted(violations.items())),
        "violation_count": sum(violations.values()),
        "mean_safety_score": mean(float(row.get("safety_score", 0)) for row in rows),
        "mean_steps": mean(float(row.get("steps", 0)) for row in rows),
        "latency_seconds": sum(float(row.get("latency_seconds", 0)) for row in rows),
        "generated_tokens": sum(int(row.get("generated_tokens", 0)) for row in rows),
    }


def mcnemar_exact(guarded_only: int, unguarded_only: int) -> float:
    discordant = guarded_only + unguarded_only
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(guarded_only, unguarded_only) + 1))
    return min(1.0, 2 * tail / (2 ** discordant))


def clustered_difference_ci(pairs: list[dict[str, Any]], samples: int = 5000, seed: int = 42) -> list[float]:
    by_task: dict[str, list[float]] = defaultdict(list)
    for item in pairs:
        by_task[item["task_id"]].append(float(item["guarded_success"]) - float(item["unguarded_success"]))
    clusters = [mean(values) for values in by_task.values()]
    rng = random.Random(seed)
    estimates = sorted(mean(rng.choice(clusters) for _ in clusters) for _ in range(samples))
    return [estimates[int(samples * 0.025)], estimates[int(samples * 0.975)]]


def main() -> None:
    parser = argparse.ArgumentParser()
    base = ROOT / "outputs" / "robustness"
    parser.add_argument("--unguarded", type=Path, default=base / "phi4_unguarded_ood_v1.jsonl")
    parser.add_argument("--guarded", type=Path, default=base / "phi4_guarded_ood_v2_1.jsonl")
    parser.add_argument("--output", type=Path, default=base / "robustness_summary.json")
    parser.add_argument("--csv", type=Path, default=base / "robustness_task_comparison.csv")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    unguarded_rows, guarded_rows = read_jsonl(args.unguarded), read_jsonl(args.guarded)
    unguarded = {(row["task_id"], int(row["seed"])): row for row in unguarded_rows}
    guarded = {(row["task_id"], int(row["seed"])): row for row in guarded_rows}
    common = sorted(unguarded.keys() & guarded.keys())
    missing = sorted(unguarded.keys() ^ guarded.keys())
    if missing and not args.allow_incomplete:
        parser.error(f"Eşlenmemiş task/seed koşuları var: {missing[:5]}")
    if not common:
        parser.error("Karşılaştırılabilir koşu bulunamadı")

    pairs = []
    outcomes = Counter()
    for task_id, seed in common:
        u, g = unguarded[(task_id, seed)], guarded[(task_id, seed)]
        u_success, g_success = bool(u["task_success"]), bool(g["task_success"])
        outcome = "both_success" if u_success and g_success else "guarded_only_success" if g_success else "unguarded_only_success" if u_success else "both_failed"
        outcomes[outcome] += 1
        task = ROBUSTNESS_TASK_BY_ID[task_id]
        pairs.append({
            "task_id": task_id, "seed": seed, "service": task.service,
            "risk": str(task.tags[0]), "unguarded_success": u_success,
            "guarded_success": g_success, "unguarded_termination": u["termination"],
            "guarded_termination": g["termination"],
            "unguarded_violations": "|".join(u.get("violations", [])),
            "guarded_violations": "|".join(g.get("violations", [])),
            "unguarded_steps": u["steps"], "guarded_steps": g["steps"],
        })

    selected_unguarded = [unguarded[key] for key in common]
    selected_guarded = [guarded[key] for key in common]
    summary = {
        "experiment": "TR-PubAgent human-authored OOD robustness v1",
        "paired_runs": len(common),
        "tasks": len({task_id for task_id, _ in common}),
        "seeds": sorted({seed for _, seed in common}),
        "unguarded": summarize(selected_unguarded),
        "guarded_v2_1": summarize(selected_guarded),
        "paired_outcomes": dict(outcomes),
        "absolute_success_gain": mean(float(row["guarded_success"]) - float(row["unguarded_success"]) for row in pairs),
        "task_cluster_bootstrap_ci95": clustered_difference_ci(pairs),
        "mcnemar_exact_p": mcnemar_exact(outcomes["guarded_only_success"], outcomes["unguarded_only_success"]),
        "limitations": ["Tek üretici model", "Sentetik portal ortamı", "Deterministik çıkarımda seed etkisi sınırlı olabilir"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    print(json.dumps({"paired_runs": len(common), "tasks": summary["tasks"], "seeds": summary["seeds"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
