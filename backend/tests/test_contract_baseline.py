from benchmark.contract_baseline import extract_contract
from app.tasks import TASKS


def public(task):
    return {"title": task.title, "user_request": task.user_request,
            "form_fields": [field.model_dump(mode="json") for field in task.form_fields]}


def test_baseline_interface_cannot_receive_hidden_gold():
    task = TASKS[0]
    prediction = extract_contract(**public(task))
    assert prediction["required_facts"]
    try:
        extract_contract(**public(task), authorization=task.authorization.model_dump())
    except TypeError:
        pass
    else:
        raise AssertionError("Extractor unexpectedly accepted hidden authorization")


def test_rule_baseline_emits_all_six_contract_fields_for_every_task():
    expected = {"goal", "permitted_actions", "prohibited_actions", "required_facts",
                "confirmation_gates", "privacy_constraints"}
    for task in TASKS:
        assert set(extract_contract(**public(task))) == expected
