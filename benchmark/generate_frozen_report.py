"""Dondurulmuş TR-PubAgent sonuçlarından kanonik özet ve bütünlük manifesti üretir."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = ROOT / "results" / "frozen"

RUN_FILES = {
    "development": {
        "unguarded_v1": "phi4_unguarded_dev_v1.jsonl",
        "guarded_v1": "phi4_guarded_dev_v1.jsonl",
        "guarded_v2_1": "phi4_guarded_dev_v2_1.jsonl",
    },
    "validation": {
        "unguarded_v1": "phi4_unguarded_validation_v1.jsonl",
        "guarded_v2_1": "phi4_guarded_validation_v2_1.jsonl",
    },
    "test": {
        "unguarded_v1": "phi4_unguarded_test_v1.jsonl",
        "guarded_v2_1": "phi4_guarded_test_v2_1.jsonl",
    },
}

EXPECTED_SPLIT_SIZES = {"development": 20, "validation": 16, "test": 40}


def load_jsonl(path: Path, id_key: str = "task_id") -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len({row[id_key] for row in rows}) != len(rows):
        raise ValueError(f"Yinelenen {id_key} bulundu: {path}")
    return rows


def wilson_interval(successes: int, total: int, z: float = 1.96) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
        / denominator
    )
    return [max(0.0, center - margin), min(1.0, center + margin)]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    successes = sum(bool(row.get("task_success")) for row in rows)
    violations = Counter(
        violation for row in rows for violation in row.get("violations", [])
    )
    return {
        "runs": total,
        "successes": successes,
        "success_rate": successes / total if total else 0.0,
        "success_ci95_wilson": wilson_interval(successes, total),
        "invalid_actions": sum(bool(row.get("invalid_action")) for row in rows),
        "terminations": dict(sorted(Counter(
            row.get("termination", "UNKNOWN") for row in rows
        ).items())),
        "violations": dict(sorted(violations.items())),
        "violation_count": sum(violations.values()),
        "mean_safety_score": (
            sum(float(row.get("safety_score", 0)) for row in rows) / total
            if total else 0.0
        ),
        "mean_steps": (
            sum(float(row.get("steps", 0)) for row in rows) / total
            if total else 0.0
        ),
        "latency_seconds": sum(float(row.get("latency_seconds", 0)) for row in rows),
        "generated_tokens": sum(int(row.get("generated_tokens", 0)) for row in rows),
        "guard_blocks": sum(int(row.get("guard_blocks", 0)) for row in rows),
        "guard_enforcements": sum(int(row.get("guard_enforcements", 0)) for row in rows),
        "git_commits": dict(sorted(Counter(
            str(row.get("git_commit")) for row in rows
        ).items())),
        "model_revisions": dict(sorted(Counter(
            str(row.get("model_revision")) for row in rows
        ).items())),
        "prompt_versions": dict(sorted(Counter(
            str(row.get("prompt_version")) for row in rows
        ).items())),
    }


def exact_mcnemar_p(guarded_only: int, unguarded_only: int) -> float:
    discordant = guarded_only + unguarded_only
    if discordant == 0:
        return 1.0
    tail = min(guarded_only, unguarded_only)
    probability = sum(math.comb(discordant, value) for value in range(tail + 1))
    return min(1.0, 2 * probability / (2**discordant))


def paired_comparison(
    unguarded: list[dict[str, Any]],
    guarded: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    unguarded_by_id = {row["task_id"]: row for row in unguarded}
    guarded_by_id = {row["task_id"]: row for row in guarded}
    if set(unguarded_by_id) != set(guarded_by_id):
        raise ValueError("Eşleştirilmiş görev kümeleri aynı değil")

    task_rows: list[dict[str, Any]] = []
    for task_id in sorted(unguarded_by_id):
        plain = unguarded_by_id[task_id]
        protected = guarded_by_id[task_id]
        task_rows.append({
            "task_id": task_id,
            "unguarded_success": bool(plain["task_success"]),
            "guarded_success": bool(protected["task_success"]),
            "unguarded_termination": plain["termination"],
            "guarded_termination": protected["termination"],
            "unguarded_violations": ",".join(plain.get("violations", [])),
            "guarded_violations": ",".join(protected.get("violations", [])),
            "unguarded_steps": plain["steps"],
            "guarded_steps": protected["steps"],
            "guard_blocks": protected.get("guard_blocks", 0),
            "guard_enforcements": protected.get("guard_enforcements", 0),
        })

    guarded_only = sum(
        not row["unguarded_success"] and row["guarded_success"] for row in task_rows
    )
    unguarded_only = sum(
        row["unguarded_success"] and not row["guarded_success"] for row in task_rows
    )
    both_success = sum(
        row["unguarded_success"] and row["guarded_success"] for row in task_rows
    )
    both_failed = len(task_rows) - guarded_only - unguarded_only - both_success
    plain_summary = summarize(unguarded)
    protected_summary = summarize(guarded)
    comparison = {
        "unguarded_v1": plain_summary,
        "guarded_v2_1": protected_summary,
        "absolute_success_gain": (
            protected_summary["success_rate"] - plain_summary["success_rate"]
        ),
        "paired_outcomes": {
            "guarded_only_success": guarded_only,
            "unguarded_only_success": unguarded_only,
            "both_success": both_success,
            "both_failed": both_failed,
        },
        "mcnemar_exact_p": exact_mcnemar_p(guarded_only, unguarded_only),
    }
    return comparison, task_rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    args = parser.parse_args()

    raw_dir = args.results_root / "raw"
    derived_dir = args.results_root / "derived"
    metadata_dir = args.results_root / "metadata"
    derived_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    loaded: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for split, systems in RUN_FILES.items():
        loaded[split] = {}
        for system, filename in systems.items():
            rows = load_jsonl(raw_dir / filename)
            expected = EXPECTED_SPLIT_SIZES[split]
            if len(rows) != expected:
                raise ValueError(f"{split}/{system}: {len(rows)} koşu; beklenen {expected}")
            loaded[split][system] = rows

    benchmark_tasks = load_jsonl(raw_dir / "tr_pubbench_tasks.jsonl", id_key="id")
    if len(benchmark_tasks) != 80:
        raise ValueError(f"Benchmark görev sayısı 80 değil: {len(benchmark_tasks)}")
    scripted = load_jsonl(raw_dir / "scripted_results.jsonl")

    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "benchmark_tasks": len(benchmark_tasks),
        "scripted_baseline": summarize(scripted),
        "development": {},
        "validation": {},
        "test": {},
        "provenance": {
            "model": "microsoft/Phi-4-mini-instruct",
            "quantization": "NF4 4-bit",
            "seed": 0,
            "unguarded_algorithm": "unguarded-v1@80ef8ed",
            "guarded_algorithm": "guarded-v2.1-frozen@91f2fb1",
            "evaluation_harness": "84458af",
        },
    }

    all_task_rows: list[dict[str, Any]] = []
    for split in ("development", "validation", "test"):
        comparison, task_rows = paired_comparison(
            loaded[split]["unguarded_v1"], loaded[split]["guarded_v2_1"]
        )
        summary[split] = comparison
        all_task_rows.extend({"split": split, **row} for row in task_rows)

    summary["development"]["guarded_v1_ablation"] = summarize(
        loaded["development"]["guarded_v1"]
    )

    summary_path = derived_dir / "frozen_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    task_path = derived_dir / "all_task_comparison.csv"
    with task_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_task_rows[0]))
        writer.writeheader()
        writer.writerows(all_task_rows)

    manifest_path = metadata_dir / "canonical_sha256_manifest.json"
    files = sorted(
        path for path in args.results_root.rglob("*")
        if path.is_file() and path != manifest_path
    )
    manifest = {
        str(path.relative_to(args.results_root)).replace("\\", "/"): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "summary": str(summary_path),
        "task_comparison": str(task_path),
        "manifest": str(manifest_path),
        "files_hashed": len(manifest),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
