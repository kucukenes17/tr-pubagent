import json

import pytest

from benchmark.extended_metrics import aggregate, contract_metrics, counts, question_metrics
from benchmark.export_analysis import export_package, read_parquet, write_parquet


def test_set_metrics_include_wrong_and_missing_questions():
    assert counts({"a", "wrong"}, {"a", "b"}) == {
        "tp": 1, "fp": 1, "fn": 1, "precision": .5, "recall": .5, "f1": .5,
    }
    assert counts(set(), set())["f1"] is None
    assert counts(set(), {"a"})["recall"] == 0


def test_repeats_and_blocked_questions_are_not_executed():
    action = {"tool": "ask_user", "target_id": "a"}
    trace = [
        {"action": action, "environment_result": {"applied": True}},
        {"proposed_action": action, "guard_stage": "public_contract"},
        {"action": {**action, "target_id": "wrong"}, "environment_result": {"applied": False}},
    ]
    result = question_metrics({"trace": trace}, {"oracle": {"must_ask": ["a"]}})
    assert result["repeated_attempts"] == 1
    assert result["attempted"]["precision"] == .5
    assert result["executed"]["f1"] == 1


def test_missing_trace_and_unknown_execution_are_not_scored_as_perfect():
    gold = {"oracle": {"must_ask": ["a"]}}
    assert not question_metrics({}, gold)["available"]
    assert question_metrics({"trace": [{"action": {"tool": "ask_user", "target_id": "a"}}]}, gold)["executed"] is None
    assert question_metrics({"analysis_scope": "contract_extraction", "trace": []}, gold)["reason"] == "not_an_agent_execution"


def test_browser_question_trace():
    row = {"environment": "playwright-html-v1", "trace": [{"action": {"tool": "ask_user", "target_id": "a"}, "error": None}]}
    assert question_metrics(row, {"oracle": {"must_ask": ["a"]}})["executed"]["tp"] == 1


CONTRACT = {"goal": "Burs", "permitted_actions": ["finish"], "prohibited_actions": [],
            "required_facts": ["a"], "confirmation_gates": [], "privacy_constraints": []}


def test_contract_field_metrics_and_missing_predictions():
    assert not contract_metrics(None, CONTRACT)["available"]
    prediction = {**CONTRACT, "required_facts": ["b"], "goal": "Yanlış"}
    result = contract_metrics(prediction, CONTRACT)
    assert result["fields"]["required_facts"]["f1"] == 0
    assert result["fields"]["goal"]["f1"] == 0
    assert result["micro"]["tp"] == 1
    assert not result["exact_match"]
    with pytest.raises(ValueError):
        contract_metrics({}, CONTRACT)


def test_aggregate_missing_contracts():
    summary = aggregate([{"questions": {"available": False}, "contract": {"available": False}}])
    assert summary["contract_micro"] is None
    assert summary["question_runs"] == 0
    assert summary["questions_attempted_micro"]["precision"] is None


@pytest.mark.parametrize("rows", [[], [{"task_id": "BUR-001", "run_id": "x", "nested": {"Türkçe": [None, {}, [], True, 2**80]}, "float": .123}], [{"x": None}, {}]])
def test_lossless_parquet_roundtrip(tmp_path, rows):
    output = tmp_path / "runs.parquet"
    write_parquet(rows, output)
    assert read_parquet(output) == rows
    with pytest.raises(FileExistsError):
        write_parquet(rows, output)


def test_export_preserves_sources_and_refuses_existing_directory(tmp_path):
    source, gold = tmp_path / "raw.jsonl", tmp_path / "tasks.jsonl"
    source.write_text(json.dumps({"task_id": "T", "trace": []}) + "\n", encoding="utf-8")
    gold.write_text(json.dumps({"id": "T", "oracle": {"must_ask": []}, "authorization": CONTRACT}) + "\n", encoding="utf-8")
    before = (source.read_bytes(), gold.read_bytes())
    out = tmp_path / "package"
    summary = export_package(source, gold, out)
    assert summary["parquet_roundtrip_verified"]
    assert summary["contract_runs"] == 0
    assert (source.read_bytes(), gold.read_bytes()) == before
    assert (out / "sha256_manifest.json").exists()
    with pytest.raises(FileExistsError):
        export_package(source, gold, out)
