from __future__ import annotations

import re
from typing import Any

from .models import ProposedAction


NUMERIC_FIELD_TERMS = ("gelir", "maaş", "ücret", "tutar", "bütçe", "miktar")
NEGATIVE_SELECT_MARKERS = (
    "değil",
    "gelemem",
    "gelmem",
    "istemiyorum",
    "işaretleme",
    "kullanma",
    "seçme",
    "olmasın",
    "uygun değil",
)
CURRENCY_VALUE = re.compile(
    r"(?<![\w])(?P<value>\d{1,3}(?:[.\s]\d{3})*|\d+)\s*(?:tl\b|₺)",
    flags=re.IGNORECASE,
)


def _fold(value: str) -> str:
    return value.casefold()


def _remaining_fields(observation: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    remaining = set(observation.get("remaining_required_fields", []))
    targets = set(observation.get("action_targets", {}).get("select" if kind == "select" else "fill", []))
    return [
        field
        for field in observation.get("form_fields", [])
        if field.get("id") in remaining
        and field.get("id") in targets
        and field.get("kind") == kind
        and not field.get("read_only", False)
    ]


def _option_is_negated(text: str, option: str) -> bool:
    starts = [match.start() for match in re.finditer(re.escape(option), text)]
    if not starts:
        return False
    for start in starts:
        clause = re.split(r"[.!?;]", text[start:], maxsplit=1)[0][:96]
        if not any(marker in clause for marker in NEGATIVE_SELECT_MARKERS):
            return False
    return True


def explicit_select_action(observation: dict[str, Any]) -> ProposedAction | None:
    """Bağımsız form seçeneklerinden metinde tek ve olumsuzlanmamış olanı bağlar."""
    text = _fold(str(observation.get("task", "")))
    candidates: list[tuple[str, str]] = []
    for field in _remaining_fields(observation, "select"):
        positive = []
        for raw_option in field.get("options", []):
            option = _fold(str(raw_option))
            if option in text and not _option_is_negated(text, option):
                positive.append(str(raw_option))
        if len(positive) == 1:
            candidates.append((str(field["id"]), positive[0]))
    if len(candidates) != 1:
        return None
    field_id, option = candidates[0]
    return ProposedAction(
        tool="select",
        target_id=field_id,
        arguments={"option": option},
        evidence_refs=["user_request:explicit_non_negated_option"],
        reason="Kullanıcı metnindeki tek açık ve olumsuzlanmamış seçenek bağlandı.",
    )


def explicit_currency_action(observation: dict[str, Any]) -> ProposedAction | None:
    """Tek bir para değerini, semantiği eşleşen tek zorunlu metin alanına bağlar."""
    text = _fold(str(observation.get("task", "")))
    askable = set(observation.get("askable_facts", []))
    fields = [
        field
        for field in _remaining_fields(observation, "text")
        if field.get("id") not in askable
        and any(term in _fold(str(field.get("label", ""))) and term in text for term in NUMERIC_FIELD_TERMS)
    ]
    values = {
        re.sub(r"[.\s]", "", match.group("value"))
        for match in CURRENCY_VALUE.finditer(text)
    }
    if len(fields) != 1 or len(values) != 1:
        return None
    field_id = str(fields[0]["id"])
    value = next(iter(values))
    return ProposedAction(
        tool="fill",
        target_id=field_id,
        arguments={"value": value},
        evidence_refs=["user_request:explicit_currency_value"],
        reason="Kullanıcı metnindeki tek açık para değeri semantik olarak eşleşen alana bağlandı.",
    )


def posthoc_grounded_action(observation: dict[str, Any]) -> ProposedAction | None:
    """v2.2'nin yalnız görünür metin ve form şemasına dayanan muhafazakâr kurtarma adımı."""
    return explicit_select_action(observation) or explicit_currency_action(observation)
