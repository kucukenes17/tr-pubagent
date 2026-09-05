from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskLabel(StrEnum):
    SAFE = "SAFE"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    UNAUTHORIZED = "UNAUTHORIZED"
    IRREVERSIBLE_CONFIRMATION_REQUIRED = "IRREVERSIBLE_CONFIRMATION_REQUIRED"
    PRIVACY_VIOLATION = "PRIVACY_VIOLATION"
    STATE_CORRUPTION_RISK = "STATE_CORRUPTION_RISK"
    LANGUAGE_INTERPRETATION_ERROR = "LANGUAGE_INTERPRETATION_ERROR"


class GuardDecisionType(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    BLOCK_AND_ASK = "BLOCK_AND_ASK"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"


class AuthorizationContract(BaseModel):
    goal: str
    permitted_actions: list[str] = Field(default_factory=list)
    prohibited_actions: list[str] = Field(default_factory=list)
    required_facts: list[str] = Field(default_factory=list)
    confirmation_gates: list[str] = Field(default_factory=list)
    privacy_constraints: list[str] = Field(default_factory=list)


class OracleDefinition(BaseModel):
    expected_fields: dict[str, Any] = Field(default_factory=dict)
    forbidden_fields: list[str] = Field(default_factory=list)
    must_submit: bool = False
    must_ask: list[str] = Field(default_factory=list)


class TaskDefinition(BaseModel):
    id: str
    split: Literal["development", "validation", "test"]
    service: str
    title: str
    user_request: str
    initial_state_fixture: str
    user_response_policy: dict[str, str] = Field(default_factory=dict)
    tags: list[RiskLabel]
    max_steps: int = Field(default=20, ge=1, le=50)
    authorization: AuthorizationContract
    oracle: OracleDefinition


class ProposedAction(BaseModel):
    tool: Literal[
        "navigate", "click", "fill", "select", "upload_fixture",
        "ask_user", "request_confirmation", "submit", "finish"
    ]
    target_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    reason: str = ""


class GuardCheckRequest(BaseModel):
    user_request: str
    action: ProposedAction
    contract: AuthorizationContract
    known_facts: dict[str, Any] = Field(default_factory=dict)
    confirmed_actions: list[str] = Field(default_factory=list)


class GuardDecision(BaseModel):
    decision: GuardDecisionType
    risk_labels: list[RiskLabel]
    confidence: float = Field(ge=0, le=1)
    missing_facts: list[str] = Field(default_factory=list)
    required_confirmation: str | None = None
    explanation: str
    evidence: list[str] = Field(default_factory=list)


class CreateRunRequest(BaseModel):
    task_id: str
    agent: Literal["scripted-oracle", "unguarded", "rule-guard", "ml-guard", "tr-pubguard"] = "tr-pubguard"
    seed: int = 0


class RunRecord(BaseModel):
    id: str
    task_id: str
    agent: str
    seed: int
    status: str
    step_count: int


class ApplyActionRequest(BaseModel):
    action: ProposedAction
    guard: GuardDecision | None = None


class EvaluationResult(BaseModel):
    run_id: str
    task_success: bool
    safety_score: float
    violations: list[RiskLabel]
    asked_required_questions: bool
    state_preserved: bool
    details: dict[str, Any]
