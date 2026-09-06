"""Ana benchmark ve OOD kümesi arasında metinsel sızıntı denetimi."""

from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

from benchmark.robustness_tasks import ROBUSTNESS_TASKS

ROOT = Path(__file__).resolve().parents[1]


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9çğıöşü]+", text.casefold()))


def token_bigrams(text: str) -> set[tuple[str, str]]:
    tokens = normalize(text).split()
    return set(zip(tokens, tokens[1:]))


def similarity(left: str, right: str) -> float:
    left_norm, right_norm = normalize(left), normalize(right)
    left_pairs, right_pairs = token_bigrams(left), token_bigrams(right)
    union = left_pairs | right_pairs
    jaccard = len(left_pairs & right_pairs) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, left_norm, right_norm).ratio()
    return round(max(jaccard, sequence), 4)


def audit(frozen: Iterable[dict], threshold: float = 0.82) -> dict:
    frozen_rows = list(frozen)
    ood_rows = [task.model_dump(mode="json") for task in ROBUSTNESS_TASKS]
    exact = []
    seen: dict[str, tuple[str, str]] = {}
    for row in frozen_rows:
        key = normalize(row["user_request"])
        previous = seen.get(key)
        if previous and previous[1] != row["split"]:
            exact.append({"left": previous[0], "right": row["id"], "text": key})
        else:
            seen[key] = (row["id"], row["split"])

    nearest = []
    near_duplicates = []
    for ood in ood_rows:
        scored = sorted(
            ((similarity(ood["user_request"], row["user_request"]), row["id"]) for row in frozen_rows),
            reverse=True,
        )
        score, frozen_id = scored[0]
        item = {"ood_id": ood["id"], "nearest_frozen_id": frozen_id, "similarity": score}
        nearest.append(item)
        if score >= threshold:
            near_duplicates.append(item)

    return {
        "schema_version": "1.0",
        "method": "max(token-bigram Jaccard, normalized SequenceMatcher)",
        "threshold": threshold,
        "frozen_tasks": len(frozen_rows),
        "ood_tasks": len(ood_rows),
        "cross_split_exact_duplicates": exact,
        "ood_near_duplicates": near_duplicates,
        "ood_nearest_matches": nearest,
        "legacy_frozen_exact_duplicate_count": len(exact),
        "ood_passed": not near_duplicates,
        "passed": not near_duplicates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, default=ROOT / "results" / "frozen" / "raw" / "tr_pubbench_tasks.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "task_leakage_report.json")
    parser.add_argument("--threshold", type=float, default=0.82)
    parser.add_argument("--strict", action="store_true", help="Denetim başarısızsa sıfır olmayan kodla çık")
    args = parser.parse_args()
    frozen = [json.loads(line) for line in args.tasks.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = audit(frozen, args.threshold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("frozen_tasks", "ood_tasks", "legacy_frozen_exact_duplicate_count", "ood_passed")}, ensure_ascii=False))
    if args.strict and not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
