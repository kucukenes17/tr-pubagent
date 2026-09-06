"""Dört sistemli OOD ablation için eşlenmiş istatistik ve H3 özeti."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from benchmark.analyze_robustness import mcnemar_exact, read_jsonl, summarize

ROOT = Path(__file__).resolve().parents[1]


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    row1, row2, col1 = a + b, c + d, a + c
    total = row1 + row2

    def probability(x: int) -> float:
        return math.comb(col1, x) * math.comb(total - col1, row1 - x) / math.comb(total, row1)

    low, high = max(0, row1 - (total - col1)), min(row1, col1)
    observed = probability(a)
    return min(1.0, sum(probability(x) for x in range(low, high + 1) if probability(x) <= observed + 1e-15))


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, value * (total - index)))
        adjusted[name] = running
    return adjusted


def joint_safe_success(rows: list[dict[str, Any]]) -> float:
    return sum(bool(row.get("task_success")) and not row.get("violations") for row in rows) / len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    base = ROOT / "outputs" / "robustness"
    parser.add_argument("--unguarded", type=Path, default=base / "phi4_unguarded_ood_v1.jsonl")
    parser.add_argument("--rule", type=Path, default=base / "phi4_guarded_ood_v2_1.jsonl")
    parser.add_argument("--ml", type=Path, default=base / "phi4_ml_guard_ood_v2_2.jsonl")
    parser.add_argument("--hybrid", type=Path, default=base / "phi4_hybrid_guard_ood_v2_2.jsonl")
    parser.add_argument("--output", type=Path, default=base / "guard_ablation_summary.json")
    args = parser.parse_args()

    paths = {"unguarded": args.unguarded, "rule": args.rule, "ml": args.ml, "hybrid": args.hybrid}
    indexed = {
        name: {(row["task_id"], int(row["seed"])): row for row in read_jsonl(path)}
        for name, path in paths.items()
    }
    common = set.intersection(*(set(rows) for rows in indexed.values()))
    if not common:
        parser.error("Dört sistem arasında ortak task/seed koşusu yok")
    if any(set(rows) != common for rows in indexed.values()):
        parser.error("Ablation dosyaları tam eşleşmiyor; eksik koşuları tamamlayın")

    selected = {name: [rows[key] for key in sorted(common)] for name, rows in indexed.items()}
    summaries = {name: summarize(rows) | {"joint_safe_success_rate": joint_safe_success(rows)} for name, rows in selected.items()}
    success_p, violation_p, comparisons = {}, {}, {}
    baseline = indexed["unguarded"]
    for name in ("rule", "ml", "hybrid"):
        guarded_only = sum(not baseline[key]["task_success"] and indexed[name][key]["task_success"] for key in common)
        unguarded_only = sum(baseline[key]["task_success"] and not indexed[name][key]["task_success"] for key in common)
        success_p[name] = mcnemar_exact(guarded_only, unguarded_only)
        u_unsafe = sum(bool(baseline[key].get("violations")) for key in common)
        x_unsafe = sum(bool(indexed[name][key].get("violations")) for key in common)
        violation_p[name] = fisher_exact_two_sided(u_unsafe, len(common) - u_unsafe, x_unsafe, len(common) - x_unsafe)
        comparisons[name] = {"guarded_only_success": guarded_only, "unguarded_only_success": unguarded_only}

    best_joint = max(summaries[name]["joint_safe_success_rate"] for name in ("rule", "ml", "hybrid"))
    h3_supported = (
        summaries["hybrid"]["joint_safe_success_rate"] == best_joint
        and summaries["hybrid"]["joint_safe_success_rate"] > summaries["rule"]["joint_safe_success_rate"]
        and summaries["hybrid"]["joint_safe_success_rate"] > summaries["ml"]["joint_safe_success_rate"]
    )
    report = {
        "experiment": "TR-PubAgent four-system OOD guard ablation",
        "paired_runs_per_system": len(common),
        "tasks": len({key[0] for key in common}),
        "seeds": sorted({key[1] for key in common}),
        "systems": summaries,
        "paired_success_comparisons_vs_unguarded": comparisons,
        "mcnemar_exact_p": success_p,
        "mcnemar_holm_adjusted_p": holm_adjust(success_p),
        "fisher_violation_p": violation_p,
        "fisher_holm_adjusted_p": holm_adjust(violation_p),
        "h3_definition": "Hybrid joint safe-success rate is strictly greater than both Rule and ML.",
        "h3_supported": h3_supported,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runs_per_system": len(common), "h3_supported": h3_supported, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
