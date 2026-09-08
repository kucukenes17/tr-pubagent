"""Run contract baseline on an explicit task snapshot without overwriting it."""

import argparse
import json
from pathlib import Path

from benchmark.contract_baseline import extract_contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tasks = [json.loads(line) for line in args.tasks.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        for task in tasks:
            prediction = extract_contract(title=task["title"], user_request=task["user_request"], form_fields=task["form_fields"])
            output.write(json.dumps({"task_id": task["id"], "agent": "turkish-rule-contract-v1",
                                     "analysis_scope": "contract_extraction",
                                     "predicted_contract": prediction, "trace": []}, ensure_ascii=False) + "\n")
    print(json.dumps({"runs": len(tasks), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
