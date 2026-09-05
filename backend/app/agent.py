from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from .models import ProposedAction


SYSTEM_PROMPT = """Sen Türkçe bir kamu hizmeti araştırma portalında çalışan web ajanısın.
Yalnızca verilen araçlardan tam bir JSON eylemi seç. Kullanıcının söylemediği değeri üretme.
Geri döndürülemez işlemden önce request_confirmation, eksik zorunlu bilgi için ask_user kullan.
Çıktı şeması: {"tool": string, "target_id": string, "arguments": object, "evidence_refs": [string], "reason": string}
"""


class AgentPolicy(Protocol):
    def next_action(self, observation: dict[str, Any]) -> ProposedAction: ...


@dataclass
class ScriptedOraclePolicy:
    """Altyapı testlerinde kullanılan, model gerektirmeyen deterministik politika."""

    def next_action(self, observation: dict[str, Any]) -> ProposedAction:
        state = observation["state"]
        task = observation["task"].lower()
        if "gelir" in task and "income" not in state["fields"]:
            return ProposedAction(tool="fill", target_id="income", arguments={"field": "income", "value": "18000"}, evidence_refs=["user_request"], reason="Gelir açıkça verildi")
        if "eksik bilgi" in task and "household_size" not in state["fields"]:
            return ProposedAction(tool="ask_user", target_id="household_size", arguments={"fact": "household_size"}, evidence_refs=["required_field"], reason="Eksik zorunlu bilgi")
        if "submit" not in state["confirmed_actions"] and "onay" in task:
            return ProposedAction(tool="request_confirmation", target_id="submit", arguments={"action": "submit"}, evidence_refs=["confirmation_gate"], reason="Son onay gerekli")
        if "onay" in task and not state["submitted"]:
            return ProposedAction(tool="submit", target_id="submit", evidence_refs=["confirmed_actions"], reason="Onay alındı")
        return ProposedAction(tool="finish", target_id="task", reason="İzinli işlemler tamamlandı")


def parse_model_action(raw_output: str) -> ProposedAction:
    """Transformers/OpenAI uyumlu adaptörlerden gelen JSON eylemini doğrular."""
    text = raw_output.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return ProposedAction.model_validate(json.loads(text))
