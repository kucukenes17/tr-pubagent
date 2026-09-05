"""Koşu JSONL dosyasından özet metrik ve bootstrap aralığı üretir."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def interval(values: list[float], seed: int = 42, samples: int = 5000) -> tuple[float, float]:
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(samples))
    return means[int(samples * 0.025)], means[int(samples * 0.975)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["agent"]].append(row)
    summary = {}
    for agent, items in grouped.items():
        success = [float(bool(item["task_success"])) for item in items]
        safety = [float(item["safety_score"]) for item in items]
        summary[agent] = {
            "runs": len(items), "task_success": sum(success) / len(success),
            "task_success_ci95": interval(success), "safety_score": sum(safety) / len(safety),
            "safety_ci95": interval(safety),
        }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
