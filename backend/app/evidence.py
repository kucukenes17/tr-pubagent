from __future__ import annotations

import json
import re
from typing import Any


def evidence_candidates(observation: dict[str, Any]) -> list[dict[str, Any]]:
    """Kanıt bağlama için yalnızca eksik, yazılabilir ve kullanıcıya sorulmayan metin alanlarını döndürür."""
    remaining = set(observation.get("remaining_required_fields", []))
    askable = set(observation.get("askable_facts", []))
    return [
        {"id": field["id"], "label": field.get("label", "")}
        for field in observation.get("form_fields", [])
        if field.get("id") in remaining
        and field.get("id") not in askable
        and field.get("kind") == "text"
        and not field.get("read_only", False)
    ]


def evidence_prompt(user_request: str, fields: list[dict[str, Any]]) -> str:
    return (
        "Kullanıcı isteğinde aşağıdaki form alanları için açıkça yazılmış değerleri çıkar. "
        "Tahmin etme, dolaylı çıkarım yapma ve kullanıcıya sorulması gereken bilgi üretme. "
        "Yalnızca alan kimliklerini anahtar kullanan tek bir JSON nesnesi döndür. "
        "Açık değer yoksa {} döndür. Alan etiketi yalnızca rakam istiyorsa nokta, boşluk ve "
        "para birimi işaretlerini kaldır.\n"
        f"Kullanıcı isteği: {user_request}\n"
        f"Alanlar: {json.dumps(fields, ensure_ascii=False)}"
    )


def parse_evidence_values(
    raw_output: str,
    fields: list[dict[str, Any]],
) -> dict[str, str]:
    """Model çıktısını izinli alanlarla sınırlar ve görünür biçim ipuçlarını uygular."""
    text = raw_output.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    decoder = json.JSONDecoder()
    payload: Any = None
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            payload = candidate
            break
    if not isinstance(payload, dict):
        return {}

    allowed = {field["id"]: field for field in fields}
    values: dict[str, str] = {}
    for field_id, value in payload.items():
        if field_id not in allowed or not isinstance(value, (str, int, float)):
            continue
        normalized = str(value).strip()
        label = str(allowed[field_id].get("label", "")).casefold()
        if "yalnızca rakam" in label:
            normalized = re.sub(r"\D", "", normalized)
        if normalized:
            values[field_id] = normalized
    return values
