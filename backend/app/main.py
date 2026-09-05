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
        "fields": {}, "submitted": False, "state_reset": False,
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
    return {
        "run_id": run_id, "task": task.user_request,
        "page_title": task.title, "route": f"/portal/{task.service}",
        "state": state,
        "candidate_actions": ["navigate", "click", "fill", "select", "upload_fixture", "ask_user", "request_confirmation", "submit", "finish"],
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

    payload: dict[str, Any] = {"action": action.model_dump()}
    if action.tool == "fill":
        field = str(action.arguments.get("field", action.target_id))
        state["fields"][field] = action.arguments.get("value")
    elif action.tool == "select":
        field = str(action.arguments.get("field", action.target_id))
        state["fields"][field] = action.arguments.get("option")
    elif action.tool == "ask_user":
        fact = str(action.arguments.get("fact", action.target_id))
        payload["fact"] = fact
        payload["answer"] = task.user_response_policy.get(fact)
        if payload["answer"] is not None:
            state["fields"][fact] = payload["answer"]
    elif action.tool == "request_confirmation":
        confirmation = str(action.arguments.get("action", action.target_id))
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
