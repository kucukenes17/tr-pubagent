"""Dondurulmuş Guarded v2.1 ile post-hoc v2.2 OOD koşularını eşler."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from benchmark.analyze_robustness import (
    clustered_difference_ci,
    mcnemar_exact,
    read_jsonl,
    summarize,
)
from benchmark.robustness_tasks import ROBUSTNESS_TASK_BY_ID


ROOT = Path(__file__).resolve().parents[1]


def compare(v21_rows: list[dict[str, Any]], v22_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    v21 = {(row["task_id"], int(row["seed"])): row for row in v21_rows}
    v22 = {(row["task_id"], int(row["seed"])): row for row in v22_rows}
    if v21.keys() != v22.keys():
        missing = sorted(v21.keys() ^ v22.keys())
        raise ValueError(f"Eşlenmemiş task/seed koşuları var: {missing[:5]}")
    if not v21:
        raise ValueError("Karşılaştırılabilir koşu bulunamadı")

    pairs: list[dict[str, Any]] = []
    outcomes: Counter[str] = Counter()
    bootstrap_pairs: list[dict[str, Any]] = []
    for task_id, seed in sorted(v21):
        before, after = v21[(task_id, seed)], v22[(task_id, seed)]
        before_success = bool(before["task_success"])
        after_success = bool(after["task_success"])
        outcome = (
            "both_success" if before_success and after_success
            else "v2_2_only_success" if after_success
            else "v2_1_only_success" if before_success
            else "both_failed"
        )
        outcomes[outcome] += 1
        task = ROBUSTNESS_TASK_BY_ID[task_id]
        pairs.append({
            "task_id": task_id,
            "seed": seed,
            "service": task.service,
            "risk": str(task.tags[0]),
            "v2_1_success": before_success,
            "v2_2_success": after_success,
            "v2_1_termination": before["termination"],
            "v2_2_termination": after["termination"],
            "v2_1_violations": "|".join(before.get("violations", [])),
            "v2_2_violations": "|".join(after.get("violations", [])),
            "v2_1_steps": before["steps"],
            "v2_2_steps": after["steps"],
        })
        bootstrap_pairs.append({
            "task_id": task_id,
            "unguarded_success": before_success,
            "guarded_success": after_success,
        })

    ordered_keys = sorted(v21)
    gain = mean(float(v22[key]["task_success"]) - float(v21[key]["task_success"]) for key in ordered_keys)
    summary = {
        "experiment": "TR-PubAgent Guarded v2.2 post-hoc OOD comparison",
        "posthoc": True,
        "paired_runs": len(ordered_keys),
        "tasks": len({task_id for task_id, _ in ordered_keys}),
        "seeds": sorted({seed for _, seed in ordered_keys}),
        "guarded_v2_1_frozen": summarize([v21[key] for key in ordered_keys]),
        "guarded_v2_2_posthoc": summarize([v22[key] for key in ordered_keys]),
        "paired_outcomes": dict(outcomes),
        "absolute_success_gain": gain,
        "task_cluster_bootstrap_ci95": clustered_difference_ci(bootstrap_pairs),
        "mcnemar_exact_p": mcnemar_exact(outcomes["v2_2_only_success"], outcomes["v2_1_only_success"]),
        "limitations": [
            "v2.2 değişiklikleri v2.1 OOD hataları görüldükten sonra tasarlandı",
            "Sentetik portal ortamı",
            "Tek üretici model ve deterministik çıkarım",
        ],
    }
    return summary, pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    base = ROOT / "outputs" / "robustness"
    parser.add_argument("--v2-1", type=Path, default=base / "phi4_guarded_ood_v2_1.jsonl")
    parser.add_argument("--v2-2", type=Path, default=base / "phi4_guarded_ood_v2_2.jsonl")
    parser.add_argument("--output", type=Path, default=base / "posthoc_v2_1_vs_v2_2_summary.json")
    parser.add_argument("--csv", type=Path, default=base / "posthoc_v2_1_vs_v2_2_tasks.csv")
    args = parser.parse_args()

    try:
        summary, pairs = compare(read_jsonl(args.v2_1), read_jsonl(args.v2_2))
    except ValueError as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    print(json.dumps({
        "paired_runs": summary["paired_runs"],
        "absolute_success_gain": summary["absolute_success_gain"],
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
