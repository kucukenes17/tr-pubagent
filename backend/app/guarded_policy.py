from __future__ import annotations

import json
from typing import Any

from .models import GuardDecision, GuardDecisionType, ProposedAction


def action_signature(action: ProposedAction) -> str:
    """Döngü tespiti için kararlı bir eylem kimliği üretir."""
    return json.dumps(action.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)


def terminal_action(observation: dict[str, Any]) -> ProposedAction | None:
    """Yalnızca görünür durumdan güvenli onay/gönderim/bitiş adımını seçer."""
    if observation.get("remaining_required_fields"):
        return None
    state = observation.get("state", {})
    if observation.get("submission_required") and not state.get("submitted", False):
        confirmed = set(state.get("confirmed_actions", []))
        if "submit" not in confirmed:
            return ProposedAction(
                tool="request_confirmation", target_id="submit",
                evidence_refs=["guarded_controller:confirmation_gate"],
                reason="Gönderimden önce açık kullanıcı onayı gerekli.",
            )
        return ProposedAction(
            tool="submit", target_id="submit",
            evidence_refs=["guarded_controller:confirmed"],
            reason="Gönderim onayı mevcut.",
        )
    return ProposedAction(
        tool="finish", target_id="task", arguments={"summary": "İzinli işlemler tamamlandı."},
        evidence_refs=["guarded_controller:ready_to_finish"],
        reason="Zorunlu alan kalmadı ve güvenli biçimde bitirilebilir.",
    )


def public_action_error(
    action: ProposedAction,
    observation: dict[str, Any],
    applied_signatures: set[str],
) -> str | None:
    """Modele gönderilmeden önce görünür araç/hedef sözleşmesini doğrular."""
    if action.tool not in observation.get("candidate_actions", []):
        return f"{action.tool} aracı bu adımda izinli değil"
    targets = observation.get("action_targets", {}).get(action.tool)
    if targets is not None and action.target_id not in targets:
        return f"{action.tool} için geçersiz target_id: {action.target_id}; izinliler: {targets}"
    if action_signature(action) in applied_signatures:
        return "Aynı eylem daha önce uygulandı; güncel duruma göre farklı bir eylem seç"
    return None


def enforced_action(
    decision: GuardDecision,
    observation: dict[str, Any],
) -> ProposedAction | None:
    """Yönlendirilebilir guard kararlarını güvenli yürütme eylemine çevirir."""
    if decision.decision == GuardDecisionType.BLOCK_AND_ASK:
        askable = set(observation.get("askable_facts", []))
        fact = next((item for item in decision.missing_facts if item in askable), None)
        if fact:
            return ProposedAction(
                tool="ask_user", target_id=fact,
                evidence_refs=["guard:missing_fact"], reason=decision.explanation,
            )
    if decision.decision == GuardDecisionType.REQUIRE_CONFIRMATION:
        confirmation = decision.required_confirmation
        if confirmation in observation.get("confirmation_actions", []):
            return ProposedAction(
                tool="request_confirmation", target_id=confirmation,
                evidence_refs=["guard:confirmation_gate"], reason=decision.explanation,
            )
    return None
