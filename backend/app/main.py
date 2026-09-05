from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import database
from .evaluator import evaluate
from .guard import check_action
from .models import (
    ApplyActionRequest, CreateRunRequest, GuardCheckRequest, GuardDecision,
    GuardDecisionType, RunRecord, TaskDefinition,
)
from .tasks import TASK_BY_ID, TASKS


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    yield


app = FastAPI(
    title="TR PubAgent API",
    version="0.1.0",
    description="Türkçe kamu hizmeti benzeri web ajanı benchmarkı ve güvenlik katmanı.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _run_or_404(run_id: str):
    row = database.get_run(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Koşu bulunamadı")
    return row


def _task_or_404(task_id: str) -> TaskDefinition:
    task = TASK_BY_ID.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    return task


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": app.version, "tasks": len(TASKS)}


@app.get("/v1/tasks", response_model=list[TaskDefinition])
def list_tasks(
    split: str | None = Query(default=None, pattern="^(development|validation|test)$"),
    service: str | None = None,
) -> list[TaskDefinition]:
    return [task for task in TASKS if (split is None or task.split == split) and (service is None or task.service == service)]


@app.get("/v1/tasks/{task_id}", response_model=TaskDefinition)
def get_task(task_id: str) -> TaskDefinition:
    return _task_or_404(task_id)


@app.post("/v1/runs", response_model=RunRecord, status_code=201)
def create_run(request: CreateRunRequest) -> RunRecord:
    task = _task_or_404(request.task_id)
    run_id = uuid.uuid4().hex
    state = {
        "fields": dict(task.initial_fields), "submitted": False, "state_reset": False,
        "confirmed_actions": [], "fixture": task.initial_state_fixture,
    }
    database.create_run(run_id, task.id, request.agent, request.seed, state)
    database.append_event(run_id, "run_created", {"task_id": task.id, "agent": request.agent, "seed": request.seed}, state)
    return RunRecord(id=run_id, task_id=task.id, agent=request.agent, seed=request.seed, status="running", step_count=1)


@app.get("/v1/runs/{run_id}", response_model=RunRecord)
def get_run(run_id: str) -> RunRecord:
    row = _run_or_404(run_id)
    return RunRecord(id=row["id"], task_id=row["task_id"], agent=row["agent"], seed=row["seed"], status=row["status"], step_count=row["step_count"])


@app.get("/v1/runs/{run_id}/events")
def get_events(run_id: str) -> list[dict[str, Any]]:
    _run_or_404(run_id)
    return database.list_events(run_id)


@app.post("/v1/guard/check", response_model=GuardDecision)
def guard_check(request: GuardCheckRequest) -> GuardDecision:
    return check_action(request)


@app.post("/v1/environments/{task_id}/reset", response_model=RunRecord)
def reset_environment(task_id: str, agent: str = "tr-pubguard", seed: int = 0) -> RunRecord:
    return create_run(CreateRunRequest(task_id=task_id, agent=agent, seed=seed))


@app.get("/v1/environments/{run_id}/observation")
def observation(run_id: str) -> dict[str, Any]:
    row = _run_or_404(run_id)
    task = _task_or_404(row["task_id"])
    state = json.loads(row["state_json"])
    recent_actions = []
    for event in database.list_events(run_id)[-6:]:
        if event["event_type"] in {"run_created", "evaluation"}:
            continue
        payload = event["payload"]
        action = payload.get("action", {})
        recent_actions.append({
            "tool": event["event_type"],
            "target_id": action.get("target_id"),
            "arguments": action.get("arguments", {}),
            "answer": payload.get("answer"),
            "confirmation": payload.get("confirmation"),
            "error": payload.get("error"),
        })
    form_fields = [
        {**field.model_dump(mode="json"), "value": state["fields"].get(field.id)}
        for field in task.form_fields
    ]
    candidate_actions = ["finish"]
    if any(field.kind == "text" and not field.read_only for field in task.form_fields):
        candidate_actions.append("fill")
    if any(field.kind == "select" for field in task.form_fields):
        candidate_actions.append("select")
    if any(field.kind == "file" for field in task.form_fields):
        candidate_actions.append("upload_fixture")
    askable_facts = [
        fact for fact in task.user_response_policy
        if not fact.endswith("_confirmation")
    ]
    if askable_facts:
        candidate_actions.append("ask_user")
    confirmation_actions = [
        gate for gate in task.authorization.confirmation_gates
        if gate in task.authorization.permitted_actions
    ]
    if "submit" in task.authorization.permitted_actions:
        candidate_actions.extend(["request_confirmation", "submit"])
    submission_required = "submit" in task.authorization.permitted_actions
    remaining_required_fields = [
        field.id for field in task.form_fields
        if field.required and state["fields"].get(field.id) in (None, "")
    ]
    action_targets = {
        "fill": [field.id for field in task.form_fields if field.kind == "text" and not field.read_only],
        "select": [field.id for field in task.form_fields if field.kind == "select" and not field.read_only],
        "upload_fixture": [field.id for field in task.form_fields if field.kind == "file" and not field.read_only],
        "ask_user": askable_facts,
        "request_confirmation": confirmation_actions,
        "submit": ["submit"] if submission_required else [],
        "finish": ["task"],
    }
    return {
        "run_id": run_id, "task": task.user_request,
        "page_title": task.title, "route": f"/portal/{task.service}",
        "state": state,
        "form_fields": form_fields,
        "askable_facts": askable_facts,
        "confirmation_actions": confirmation_actions,
        "action_targets": action_targets,
        "remaining_required_fields": remaining_required_fields,
        "submission_required": submission_required,
        "ready_to_finish": not remaining_required_fields and (not submission_required or state["submitted"]),
        "recent_actions": recent_actions,
        "candidate_actions": candidate_actions,
        "step": row["step_count"], "max_steps": task.max_steps,
    }


@app.post("/v1/environments/{run_id}/action")
def apply_action(run_id: str, request: ApplyActionRequest) -> dict[str, Any]:
    row = _run_or_404(run_id)
    task = _task_or_404(row["task_id"])
    if row["step_count"] >= task.max_steps:
        database.finish_run(run_id, "max_steps")
        raise HTTPException(status_code=409, detail="Maksimum adım sayısı aşıldı")

    state = json.loads(row["state_json"])
    action = request.action
    guard = request.guard
    if guard and guard.decision != GuardDecisionType.ALLOW:
        database.append_event(run_id, "guard_block", {"action": action.model_dump(), "decision": guard.model_dump(mode="json")}, state)
        return {"applied": False, "state": state, "guard": guard}

    form_by_id = {field.id: field for field in task.form_fields}
    validation_error = None
    if action.tool in {"fill", "select"}:
        field_id = action.target_id
        field = form_by_id.get(field_id)
        if field is None:
            validation_error = f"Bilinmeyen form alanı: {field_id}"
        elif action.tool == "fill" and field.kind != "text":
            validation_error = f"{field_id} alanı fill aracını desteklemiyor"
        elif field.read_only:
            validation_error = f"{field_id} alanı salt okunur"
        elif action.tool == "select" and field.kind != "select":
            validation_error = f"{field_id} alanı select aracını desteklemiyor"
        elif action.tool == "select" and action.arguments.get("option") not in field.options:
            validation_error = f"Geçersiz seçenek: {action.arguments.get('option')}"
    elif action.tool == "ask_user":
        fact = action.target_id
        if fact not in task.user_response_policy or fact.endswith("_confirmation"):
            validation_error = f"Bu görev için bilinmeyen soru kimliği: {fact}"

    if validation_error:
        step = database.append_event(
            run_id,
            "invalid_action",
            {"action": action.model_dump(), "error": validation_error},
            state,
        )
        return {"applied": False, "step": step, "state": state, "error": validation_error}

    payload: dict[str, Any] = {"action": action.model_dump()}
    if action.tool == "fill":
        field = action.target_id
        state["fields"][field] = action.arguments.get("value")
    elif action.tool == "select":
        field = action.target_id
        state["fields"][field] = action.arguments.get("option")
    elif action.tool == "ask_user":
        fact = action.target_id
        payload["fact"] = fact
        payload["answer"] = task.user_response_policy.get(fact)
        if payload["answer"] is not None:
            state["fields"][fact] = payload["answer"]
    elif action.tool == "request_confirmation":
        confirmation = action.target_id
        if task.user_response_policy.get(f"{confirmation}_confirmation", "evet") == "evet":
            state["confirmed_actions"].append(confirmation)
        payload["confirmation"] = confirmation
    elif action.tool == "submit":
        state["submitted"] = True
    elif action.tool == "click" and action.target_id in {"reset", "clear-form", "delete"}:
        state["fields"] = {}
        state["state_reset"] = True
    step = database.append_event(run_id, action.tool, payload, state)
    if action.tool == "finish":
        database.finish_run(run_id)
    return {"applied": True, "step": step, "state": state}


@app.post("/v1/evaluate/{run_id}")
def evaluate_run(run_id: str):
    row = _run_or_404(run_id)
    task = _task_or_404(row["task_id"])
    state = json.loads(row["state_json"])
    events = database.list_events(run_id)
    result = evaluate(run_id, task, state, events)
    database.append_event(run_id, "evaluation", result.model_dump(mode="json"), state)
    database.finish_run(run_id)
    return result


@app.get("/v1/leaderboard")
def leaderboard() -> dict[str, Any]:
    return {
        "status": "sample_until_frozen_experiment",
        "warning": "Bu değerler arayüz örneğidir; bilimsel sonuç değildir.",
        "rows": [
            {"agent": "tr-pubguard", "task_success": 0.78, "safety_score": 0.92},
            {"agent": "rule-guard", "task_success": 0.73, "safety_score": 0.81},
            {"agent": "unguarded", "task_success": 0.76, "safety_score": 0.54},
        ],
    }
