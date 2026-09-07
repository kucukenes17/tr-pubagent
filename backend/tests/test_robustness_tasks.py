import json
from collections import Counter
from pathlib import Path

from benchmark.check_task_leakage import audit
from benchmark.analyze_robustness import mcnemar_exact, wilson
from benchmark.analyze_ablation import fisher_exact_two_sided, holm_adjust
from benchmark.run_robustness import result_paths, safe_run_label
from benchmark.robustness_tasks import ROBUSTNESS_TASKS


ROOT = Path(__file__).resolve().parents[2]


def test_robustness_set_is_balanced_and_unique():
    assert len(ROBUSTNESS_TASKS) == 24
    assert len({task.id for task in ROBUSTNESS_TASKS}) == 24
    assert set(Counter(task.service for task in ROBUSTNESS_TASKS).values()) == {4}
    assert Counter(str(task.tags[0]) for task in ROBUSTNESS_TASKS) == {
        "MISSING_INFORMATION": 5,
        "IRREVERSIBLE_CONFIRMATION_REQUIRED": 5,
        "PRIVACY_VIOLATION": 5,
        "LANGUAGE_INTERPRETATION_ERROR": 5,
        "STATE_CORRUPTION_RISK": 4,
    }


def test_robustness_tasks_have_complete_contracts():
    for task in ROBUSTNESS_TASKS:
        assert task.id.startswith("OOD-")
        assert task.user_request
        assert task.authorization.goal
        assert task.oracle
        assert task.form_fields


def test_ood_requests_do_not_duplicate_frozen_benchmark():
    path = ROOT / "results" / "frozen" / "raw" / "tr_pubbench_tasks.jsonl"
    frozen = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = audit(frozen)
    # Ana benchmark dondurulduktan sonra bulunan DRS-009/DRS-014 tekrarı değiştirilmez;
    # raporda görünür tutulur ve yeni OOD paketine taşınmadığı doğrulanır.
    assert len(report["cross_split_exact_duplicates"]) == 1
    assert not report["ood_near_duplicates"]
    assert report["ood_passed"]


def test_robustness_statistics_are_bounded_and_exact():
    assert wilson(0, 40)[0] == 0.0
    assert wilson(40, 40)[1] == 1.0
    assert mcnemar_exact(40, 0) == 2 / (2 ** 40)
    assert mcnemar_exact(0, 0) == 1.0
    assert fisher_exact_two_sided(1, 9, 11, 3) < 0.01
    adjusted = holm_adjust({"a": 0.01, "b": 0.04, "c": 0.2})
    assert adjusted == {"a": 0.03, "b": 0.08, "c": 0.2}


def test_cross_model_result_paths_cannot_overwrite_phi4_defaults(tmp_path):
    assert safe_run_label("Qwen/Qwen2.5-7B-Instruct") == "qwen_qwen2_5_7b_instruct"
    default_paths = result_paths(tmp_path, "phi4")
    qwen_paths = result_paths(tmp_path, "qwen2_5_7b")
    assert default_paths["unguarded"].name == "phi4_unguarded_ood_v1.jsonl"
    assert qwen_paths["guarded"].name == "qwen2_5_7b_guarded_ood_v2_1.jsonl"
    assert result_paths(tmp_path, "phi4", "v2.2")["guarded"].name == "phi4_guarded_ood_v2_2.jsonl"
    assert set(default_paths.values()).isdisjoint(qwen_paths.values())
