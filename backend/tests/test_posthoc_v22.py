from app.posthoc_v22 import explicit_currency_action, explicit_select_action, posthoc_grounded_action


def select_observation(task: str):
    return {
        "task": task,
        "remaining_required_fields": ["service_day"],
        "action_targets": {"select": ["service_day"], "fill": []},
        "askable_facts": [],
        "form_fields": [{
            "id": "service_day", "label": "Hizmet günü", "kind": "select",
            "read_only": False,
            "options": ["pazartesi", "salı", "çarşamba", "perşembe", "cuma"],
        }],
    }


def test_selects_only_non_negated_explicit_option():
    action = explicit_select_action(select_observation(
        "Salı günü gelemem. Hastane randevusunu perşembe gününe ayarla."
    ))
    assert action is not None
    assert action.tool == "select"
    assert action.target_id == "service_day"
    assert action.arguments == {"option": "perşembe"}


def test_handles_same_clause_correction_without_selecting_forbidden_option():
    action = explicit_select_action(select_observation("Pazartesi değil cuma gününü seç."))
    assert action is not None
    assert action.arguments == {"option": "cuma"}


def test_refuses_ambiguous_positive_options():
    assert explicit_select_action(select_observation("Salı veya perşembe olabilir.")) is None


def test_binds_single_explicit_currency_to_matching_field():
    observation = {
        "task": "Gelir hanesine 18.000 TL gir. Belge türünü bilmiyorsan bana sor.",
        "remaining_required_fields": ["income", "document_type"],
        "action_targets": {"fill": ["income", "document_type"], "select": []},
        "askable_facts": ["document_type"],
        "form_fields": [
            {"id": "income", "label": "Aylık gelir", "kind": "text", "read_only": False},
            {"id": "document_type", "label": "Belge türü", "kind": "text", "read_only": False},
        ],
    }
    action = explicit_currency_action(observation)
    assert action is not None
    assert action.tool == "fill"
    assert action.target_id == "income"
    assert action.arguments == {"value": "18000"}
    assert posthoc_grounded_action(observation) == action


def test_refuses_multiple_currency_values():
    observation = {
        "task": "Gelir 18.000 TL veya 20.000 TL olabilir.",
        "remaining_required_fields": ["income"],
        "action_targets": {"fill": ["income"], "select": []},
        "askable_facts": [],
        "form_fields": [{"id": "income", "label": "Aylık gelir", "kind": "text", "read_only": False}],
    }
    assert explicit_currency_action(observation) is None
