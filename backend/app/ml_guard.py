"""XLM-R risk sınıflandırıcısı için çalışma zamanı adaptörü.

Transformers yalnız gerçek ML deneyi başlatıldığında yüklenir; API ve birim
testleri model ağırlığı indirmeden çalışmaya devam eder.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .models import GuardDecision, GuardDecisionType, ProposedAction, RiskLabel


@dataclass(frozen=True)
class RiskPrediction:
    label: RiskLabel
    confidence: float
    scores: dict[str, float]


class RiskClassifier(Protocol):
    def predict(self, user_request: str, current_state: dict[str, Any], action: ProposedAction) -> RiskPrediction: ...


def classifier_feature_text(user_request: str, current_state: Any, proposed_action: Any) -> str:
    def encode(value: Any) -> str:
        return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    state = encode(current_state)
    proposed = encode(proposed_action)
    return f"TALEP: {user_request} DURUM: {state} EYLEM: {proposed}"


def classifier_text(user_request: str, current_state: dict[str, Any], action: ProposedAction) -> str:
    return classifier_feature_text(user_request, current_state, action.model_dump(mode="json"))


class XLMRRiskClassifier:
    def __init__(self, model_path: str | Path, device: str | None = None):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def predict(self, user_request: str, current_state: dict[str, Any], action: ProposedAction) -> RiskPrediction:
        text = classifier_text(user_request, current_state, action)
        inputs = self.tokenizer(text, truncation=True, max_length=256, return_tensors="pt").to(self.device)
        with self.torch.inference_mode():
            probabilities = self.torch.softmax(self.model(**inputs).logits[0], dim=-1)
        scores = {
            str(self.model.config.id2label[index]): float(probabilities[index].item())
            for index in range(len(probabilities))
        }
        label, confidence = max(scores.items(), key=lambda item: item[1])
        return RiskPrediction(label=RiskLabel(label), confidence=confidence, scores=scores)


def prediction_to_decision(
    prediction: RiskPrediction,
    *,
    action: ProposedAction,
    required_facts: list[str],
    known_facts: dict[str, Any],
    confirmation_gates: list[str],
    threshold: float,
) -> GuardDecision:
    if prediction.confidence < threshold or prediction.label == RiskLabel.SAFE:
        return GuardDecision(
            decision=GuardDecisionType.ALLOW, risk_labels=[RiskLabel.SAFE],
            confidence=prediction.confidence, explanation="ML risk eşiğini geçen bir tehlike saptamadı.",
            evidence=[f"ml:{prediction.label}:{prediction.confidence:.4f}"],
        )

    missing = [fact for fact in required_facts if known_facts.get(fact) in (None, "")]
    if prediction.label == RiskLabel.MISSING_INFORMATION and missing:
        decision, required_confirmation = GuardDecisionType.BLOCK_AND_ASK, None
    elif prediction.label in {RiskLabel.IRREVERSIBLE_CONFIRMATION_REQUIRED, RiskLabel.STATE_CORRUPTION_RISK}:
        decision = GuardDecisionType.REQUIRE_CONFIRMATION
        required_confirmation = next((gate for gate in confirmation_gates if gate in {action.tool, action.target_id}), action.tool if action.tool == "submit" else action.target_id)
    else:
        decision, required_confirmation = GuardDecisionType.BLOCK, None

    return GuardDecision(
        decision=decision, risk_labels=[prediction.label], confidence=prediction.confidence,
        missing_facts=missing if decision == GuardDecisionType.BLOCK_AND_ASK else [],
        required_confirmation=required_confirmation,
        explanation=f"Öğrenilmiş risk modeli eylemi {prediction.label} olarak sınıflandırdı.",
        evidence=[f"ml:{prediction.label}:{prediction.confidence:.4f}"],
    )


def hybrid_decision(rule: GuardDecision, learned: GuardDecision) -> GuardDecision:
    """Kurallar engellediyse kuralı, aksi halde öğrenilmiş kararı uygular."""
    return rule if rule.decision != GuardDecisionType.ALLOW else learned
