from __future__ import annotations

from .models import GuardCheckRequest, GuardDecision, GuardDecisionType, RiskLabel


IRREVERSIBLE_TOOLS = {"submit", "upload_fixture"}
STATE_DESTRUCTIVE_TARGETS = {"reset", "delete", "clear-form", "cancel"}


def check_action(request: GuardCheckRequest) -> GuardDecision:
    action = request.action
    contract = request.contract
    action_name = action.target_id if action.tool in {"click", "submit"} else action.tool

    prohibited = set(contract.prohibited_actions)
    if action_name in prohibited or action.tool in prohibited:
        return GuardDecision(
            decision=GuardDecisionType.BLOCK,
            risk_labels=[RiskLabel.UNAUTHORIZED], confidence=0.99,
            explanation="Planlanan eylem kullanıcı yetki sözleşmesinde açıkça yasaklanmış.",
            evidence=[f"prohibited:{action_name}"],
        )

    lowered_target = action.target_id.lower()
    if any(field in lowered_target or field in action.arguments for field in contract.privacy_constraints):
        return GuardDecision(
            decision=GuardDecisionType.BLOCK,
            risk_labels=[RiskLabel.PRIVACY_VIOLATION], confidence=0.98,
            explanation="Eylem, kullanıcının paylaşılmamasını istediği bir veri alanına dokunuyor.",
            evidence=[f"privacy:{field}" for field in contract.privacy_constraints],
        )

    missing = [fact for fact in contract.required_facts if fact not in request.known_facts or request.known_facts[fact] in (None, "")]
    argument_field = str(action.arguments.get("field", action.target_id))
    if missing and (action.tool in {"fill", "select", "submit"} or argument_field in missing):
        return GuardDecision(
            decision=GuardDecisionType.BLOCK_AND_ASK,
            risk_labels=[RiskLabel.MISSING_INFORMATION], confidence=0.97,
            missing_facts=missing,
            explanation="Zorunlu bilgi kullanıcı tarafından verilmedi; değer tahmin edilmemeli.",
            evidence=[f"missing:{fact}" for fact in missing],
        )

    if lowered_target in STATE_DESTRUCTIVE_TARGETS and lowered_target not in request.confirmed_actions:
        return GuardDecision(
            decision=GuardDecisionType.REQUIRE_CONFIRMATION,
            risk_labels=[RiskLabel.STATE_CORRUPTION_RISK], confidence=0.96,
            required_confirmation=lowered_target,
            explanation="Eylem önceki form durumunu bozabilir ve açık onay gerektirir.",
            evidence=[f"destructive:{lowered_target}"],
        )

    gate = action.tool if action.tool in contract.confirmation_gates else action.target_id if action.target_id in contract.confirmation_gates else None
    if (action.tool in IRREVERSIBLE_TOOLS or gate) and (gate or action.tool) not in request.confirmed_actions:
        required = gate or action.tool
        return GuardDecision(
            decision=GuardDecisionType.REQUIRE_CONFIRMATION,
            risk_labels=[RiskLabel.IRREVERSIBLE_CONFIRMATION_REQUIRED], confidence=0.99,
            required_confirmation=required,
            explanation="Geri döndürülemez eylem için açık son kullanıcı onayı bulunmuyor.",
            evidence=[f"confirmation_gate:{required}"],
        )

    return GuardDecision(
        decision=GuardDecisionType.ALLOW,
        risk_labels=[RiskLabel.SAFE], confidence=0.95,
        explanation="Eylem yetki, bilgi ve onay sınırları içinde.",
        evidence=action.evidence_refs,
    )
