from app.ml_guard import RiskPrediction, classifier_feature_text, classifier_text, hybrid_decision, prediction_to_decision
from app.models import GuardDecision, GuardDecisionType, ProposedAction, RiskLabel


def action(tool="submit", target="submit"):
    return ProposedAction(tool=tool, target_id=target, arguments={})


def prediction(label, confidence=0.95):
    return RiskPrediction(label=label, confidence=confidence, scores={str(label): confidence})


def test_classifier_text_is_stable_and_contains_no_python_repr():
    text = classifier_text("Başvuruyu hazırla", {"b": 2, "a": 1}, action())
    assert 'DURUM: {"a":1,"b":2}' in text
    assert '"tool":"submit"' in text
    assert classifier_feature_text("x", '{"a":1}', '{"tool":"finish"}') == 'TALEP: x DURUM: {"a":1} EYLEM: {"tool":"finish"}'


def test_low_confidence_prediction_allows_action():
    decision = prediction_to_decision(
        prediction(RiskLabel.PRIVACY_VIOLATION, 0.4), action=action(),
        required_facts=[], known_facts={}, confirmation_gates=["submit"], threshold=0.8,
    )
    assert decision.decision == GuardDecisionType.ALLOW


def test_missing_information_prediction_can_be_enforced_as_question():
    decision = prediction_to_decision(
        prediction(RiskLabel.MISSING_INFORMATION), action=action("fill", "district"),
        required_facts=["district"], known_facts={}, confirmation_gates=[], threshold=0.8,
    )
    assert decision.decision == GuardDecisionType.BLOCK_AND_ASK
    assert decision.missing_facts == ["district"]


def test_hybrid_never_overrides_rule_block():
    rule = GuardDecision(
        decision=GuardDecisionType.BLOCK, risk_labels=[RiskLabel.PRIVACY_VIOLATION],
        confidence=0.99, explanation="kural", evidence=["privacy:email"],
    )
    learned = GuardDecision(
        decision=GuardDecisionType.ALLOW, risk_labels=[RiskLabel.SAFE],
        confidence=0.9, explanation="ml", evidence=["ml:SAFE"],
    )
    assert hybrid_decision(rule, learned) is rule
