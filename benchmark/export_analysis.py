"""Create a new supplementary metrics/Parquet package from explicit snapshots."""

import argparse
import hashlib
import json
from pathlib import Path

from benchmark.extended_metrics import aggregate, contract_metrics, question_metrics


def reject_constant(value):
    raise ValueError(f"Non-standard JSON constant: {value}")


def read_jsonl(path):
    rows = [json.loads(line, parse_constant=reject_constant) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Each JSONL record must be an object")
    return rows


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_parquet(rows: list[dict], path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    # Canonical JSON column preserves arbitrary nested traces, empty objects,
    # large integers and missing-vs-null values without Arrow schema inference.
    schema = pa.schema([
        ("row_index", pa.int64()), ("task_id", pa.string()), ("run_id", pa.string()),
        ("record_json", pa.string()),
    ], metadata={b"tr_pubagent.schema": b"lossless-json-records-v1"})
    records = [{"row_index": index, "task_id": row.get("task_id"), "run_id": row.get("run_id"),
                "record_json": json.dumps(row, ensure_ascii=False, allow_nan=False, sort_keys=True)}
               for index, row in enumerate(rows)]
    with path.open("xb") as output:
        pq.write_table(pa.Table.from_pylist(records, schema=schema), output, compression="zstd")


def read_parquet(path):
    import pyarrow.parquet as pq
    return [json.loads(row["record_json"]) for row in pq.read_table(path).to_pylist()]


def export_package(source: Path, tasks_path: Path, destination: Path) -> dict:
    rows, tasks = read_jsonl(source), read_jsonl(tasks_path)
    gold = {task["id"]: task for task in tasks}
    if len(gold) != len(tasks):
        raise ValueError("Duplicate task IDs in gold snapshot")
    if not rows:
        raise ValueError("No runs to analyze")
    metrics = []
    for row in rows:
        task = gold[row["task_id"]]  # Missing gold is an error, not a guessed label.
        metrics.append({
            "run_id": row.get("run_id"), "task_id": row["task_id"],
            "questions": question_metrics(row, task),
            # Only an explicitly logged extraction output counts as a prediction.
            "contract": contract_metrics(row.get("predicted_contract"), task["authorization"]),
        })
    aggregated = aggregate(metrics)
    limitations = ["Post-hoc supplementary analysis; not a new model experiment",
                   "Gold labels come from the supplied synthetic task snapshot"]
    if not aggregated["contract_runs"]:
        limitations.append("Contract extraction is unmeasured when predictions were not logged")
    else:
        limitations.append("Contract scores describe only the named extractor and supplied task distribution")
    summary = {
        "protocol": "supplementary-metrics-v1", "source_sha256": sha256(source),
        "gold_sha256": sha256(tasks_path), **aggregated,
        "limitations": limitations,
    }
    # Refuse every existing directory, including frozen/derived destinations.
    destination.mkdir(parents=True, exist_ok=False)
    write_parquet(rows, destination / "runs.parquet")
    if read_parquet(destination / "runs.parquet") != rows:
        raise RuntimeError("Parquet round-trip mismatch")
    (destination / "metrics.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n" for item in metrics), encoding="utf-8")
    summary["parquet_roundtrip_verified"] = True
    (destination / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest = {p.name: sha256(p) for p in sorted(destination.iterdir()) if p.is_file()}
    (destination / "sha256_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_package(args.input, args.tasks, args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
