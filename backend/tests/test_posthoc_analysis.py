from benchmark.analyze_posthoc_v22 import compare


def row(task_id: str, seed: int, success: bool):
    return {
        "task_id": task_id,
        "seed": seed,
        "task_success": success,
        "termination": "FINISHED" if success else "MAX_STEPS",
        "violations": [],
        "invalid_action": False,
        "safety_score": 1.0,
        "steps": 2 if success else 19,
        "latency_seconds": 1,
        "generated_tokens": 10,
    }


def test_posthoc_comparison_keeps_versions_separate():
    before = [row("OOD-BLG-001", 0, False)]
    after = [row("OOD-BLG-001", 0, True)]
    summary, pairs = compare(before, after)
    assert summary["posthoc"] is True
    assert summary["absolute_success_gain"] == 1.0
    assert summary["paired_outcomes"] == {"v2_2_only_success": 1}
    assert pairs[0]["v2_1_success"] is False
    assert pairs[0]["v2_2_success"] is True


def test_posthoc_comparison_rejects_unpaired_runs():
    try:
        compare([row("OOD-BLG-001", 0, False)], [row("OOD-BLG-001", 17, True)])
    except ValueError as error:
        assert "Eşlenmemiş" in str(error)
    else:
        raise AssertionError("Eşlenmemiş koşular reddedilmeliydi")
