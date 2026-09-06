"""İnsan yazımı 24 sağlamlık görevini JSONL olarak dışa aktarır."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.robustness_tasks import ROBUSTNESS_TASKS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "robustness_tasks_v1.jsonl")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(json.dumps(task.model_dump(mode="json"), ensure_ascii=False) for task in ROBUSTNESS_TASKS) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"tasks": len(ROBUSTNESS_TASKS), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
