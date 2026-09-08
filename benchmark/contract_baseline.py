"""Transparent Turkish rule baseline for authorization-contract extraction."""

from __future__ import annotations

import re


COMMON_ACTIONS = ["navigate", "click", "fill", "select", "ask_user", "request_confirmation", "finish"]


def extract_contract(*, title: str, user_request: str, form_fields: list[dict]) -> dict:
    """Predict from public task content only; accepts no oracle/contract input."""
    text = user_request.casefold()
    goal = re.sub(r"\s+güvenlik senaryosu\s+\d+$", "", title, flags=re.IGNORECASE)
    permitted = list(COMMON_ACTIONS)
    prohibited, required, privacy = [], [], []

    if "göndermeden önce" in text:
        permitted.append("submit")
    if "değer uydurma" in text:
        prohibited.append("invent_value")
        required = [field["id"] for field in form_fields if field.get("required") and field["id"] != "income"]
    if "hiçbir alana yazma" in text:
        privacy = [field["id"] for field in form_fields]
        prohibited.extend(f"share_{field_id}" for field_id in privacy)
    forbidden_day = re.search(r";\s*([^\s,;]+)\s+gününü\s+kesinlikle\s+seçme", text)
    if forbidden_day:
        prohibited.append(f"select_{forbidden_day.group(1)}")
    if "sıfırlama veya silme yapma" in text:
        prohibited.extend(["reset", "delete"])

    return {
        "goal": goal,
        "permitted_actions": permitted,
        "prohibited_actions": prohibited,
        "required_facts": required,
        "confirmation_gates": ["submit", "cancel"] if "göndermeden önce" in text else ["submit"],
        "privacy_constraints": privacy,
    }
