from app.evidence import evidence_candidates, evidence_prompt, parse_evidence_values


def test_candidates_only_include_missing_non_askable_writable_text_fields():
    observation = {
        "remaining_required_fields": ["income", "household_size", "day", "note"],
        "askable_facts": ["household_size"],
        "form_fields": [
            {"id": "income", "label": "Aylık gelir (yalnızca rakam, TL)", "kind": "text", "read_only": False},
            {"id": "household_size", "label": "Hane", "kind": "text", "read_only": False},
            {"id": "day", "label": "Gün", "kind": "select", "read_only": False},
            {"id": "note", "label": "Not", "kind": "text", "read_only": True},
        ],
    }
    assert evidence_candidates(observation) == [
        {"id": "income", "label": "Aylık gelir (yalnızca rakam, TL)"}
    ]


def test_parser_limits_fields_and_normalizes_digits_only_value():
    fields = [{"id": "income", "label": "Aylık gelir (yalnızca rakam, TL)"}]
    raw = '```json\n{"income":"18.000 TL","phone":"555"}\n```'
    assert parse_evidence_values(raw, fields) == {"income": "18000"}


def test_evidence_prompt_forbids_inference():
    prompt = evidence_prompt("Gelirim 18.000 TL", [{"id": "income", "label": "Gelir"}])
    assert "Tahmin etme" in prompt
    assert "income" in prompt
