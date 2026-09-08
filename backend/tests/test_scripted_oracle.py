"""Reachability check, not a model baseline: the oracle sees hidden targets."""

import pytest

from app.tasks import TASKS
from benchmark.run_scripted import run_task


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_scripted_oracle_reaches_success_for_every_task(client, task):
    result = run_task(client, task.model_dump(mode="json"), "scripted-oracle")
    assert result["task_success"], result
    assert not result["violations"], result
    events = client.get(f"/v1/runs/{result['run_id']}/events").json()
    assert all(event["event_type"] != "invalid_action" for event in events)
