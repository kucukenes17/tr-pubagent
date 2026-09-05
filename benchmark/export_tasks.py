"""80 görevi sürümlenebilir JSONL veri setine aktarır."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.tasks import TASKS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "tr_pubbench_tasks.jsonl")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(task.model_dump(mode="json"), ensure_ascii=False) for task in TASKS) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": len(TASKS), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
