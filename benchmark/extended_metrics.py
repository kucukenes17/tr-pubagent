"""Supplementary metrics v1. Never modifies the frozen evaluator or results."""

from collections import Counter

CONTRACT_FIELDS = (
    "goal", "permitted_actions", "prohibited_actions", "required_facts",
    "confirmation_gates", "privacy_constraints",
)


def counts(predicted: set, gold: set) -> dict:
    tp, fp, fn = len(predicted & gold), len(predicted - gold), len(gold - predicted)
    return score_counts(tp, fp, fn)


def score_counts(tp: int, fp: int, fn: int) -> dict:
    # Undefined denominators are null, never silently perfect performance.
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def question_metrics(row: dict, gold: dict) -> dict:
    if row.get("analysis_scope") == "contract_extraction":
        return {"available": False, "reason": "not_an_agent_execution"}
    if not isinstance(row.get("trace"), list):
        return {"available": False, "reason": "missing_trace"}
    attempted, executed = [], []
    execution_known = True
    for step in row["trace"]:
        action = step.get("action") or step.get("proposed_action")
        if not isinstance(action, dict) or action.get("tool") != "ask_user":
            continue
        target = action.get("target_id")
        if not isinstance(target, str):
            raise ValueError("ask_user must have a string target_id")
        attempted.append(target)
        result = step.get("environment_result")
        if "action" not in step and step.get("guard_stage") == "public_contract":
            continue
        if isinstance(result, dict) and isinstance(result.get("applied"), bool):
            if result["applied"] and "action" in step:
                executed.append(target)
        elif row.get("environment") == "playwright-html-v1" and "error" in step:
            if not step["error"]:
                executed.append(target)
        else:
            execution_known = False
    required = set(gold["oracle"]["must_ask"])
    return {
        "available": True,
        "attempted": counts(set(attempted), required),
        "executed": counts(set(executed), required) if execution_known else None,
        "question_attempts": len(attempted),
        "repeated_attempts": sum(n - 1 for n in Counter(attempted).values()),
        "gold_questions": sorted(required),
    }


def contract_items(contract: dict) -> set:
    if not isinstance(contract, dict) or set(contract) != set(CONTRACT_FIELDS):
        raise ValueError("Contract must explicitly contain exactly all six fields")
    items = set()
    for field in CONTRACT_FIELDS:
        value = contract[field]
        if field == "goal":
            if not isinstance(value, str):
                raise ValueError("goal must be a string")
            items.add((field, value))
        else:
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"{field} must be a string list")
            items.update((field, item) for item in value)
    return items


def contract_metrics(predicted: dict | None, gold: dict) -> dict:
    if predicted is None:
        return {"available": False, "reason": "predicted_contract_not_logged"}
    p, g = contract_items(predicted), contract_items(gold)
    return {
        "available": True, "micro": counts(p, g),
        "fields": {field: counts({x for x in p if x[0] == field}, {x for x in g if x[0] == field}) for field in CONTRACT_FIELDS},
        "exact_match": p == g,
    }


def aggregate(metrics: list[dict]) -> dict:
    def micro(items):
        return score_counts(*(sum(item[key] for item in items) for key in ("tp", "fp", "fn")))

    questions = [item["questions"] for item in metrics if item["questions"]["available"]]
    contracts = [item["contract"] for item in metrics if item["contract"]["available"]]
    executed = [item["executed"] for item in questions if item["executed"] is not None]
    return {
        "runs": len(metrics), "question_runs": len(questions), "executed_question_runs": len(executed),
        "questions_attempted_micro": micro([item["attempted"] for item in questions]),
        "questions_executed_micro": micro(executed),
        "repeated_question_attempts": sum(item["repeated_attempts"] for item in questions),
        "contract_runs": len(contracts),
        "contract_micro": micro([item["micro"] for item in contracts]) if contracts else None,
        "contract_exact_match_rate": sum(item["exact_match"] for item in contracts) / len(contracts) if contracts else None,
        "contract_fields": {field: micro([item["fields"][field] for item in contracts]) for field in CONTRACT_FIELDS} if contracts else None,
    }
