from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app


def test_parallel_runs_keep_state_and_events_isolated(client):
    run_ids = [client.post("/v1/runs", json={"task_id": "BUR-001", "agent": f"parallel-{i}"}).json()["id"] for i in range(16)]

    def write(pair):
        index, run_id = pair
        with TestClient(app) as worker:
            response = worker.post(f"/v1/environments/{run_id}/action", json={
                "action": {"tool": "fill", "target_id": "income", "arguments": {"value": str(10000 + index)}}
            })
            assert response.status_code == 200 and response.json()["applied"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(write, enumerate(run_ids)))
    for index, run_id in enumerate(run_ids):
        observation = client.get(f"/v1/environments/{run_id}/observation").json()
        assert observation["state"]["fields"] == {"income": str(10000 + index)}
        events = client.get(f"/v1/runs/{run_id}/events").json()
        assert [event["step"] for event in events] == [1, 2]


def test_concurrent_events_on_one_run_get_unique_monotonic_steps(client):
    run_id = client.post("/v1/runs", json={"task_id": "BUR-001", "agent": "parallel-one"}).json()["id"]

    def write(value):
        with TestClient(app) as worker:
            return worker.post(f"/v1/environments/{run_id}/action", json={
                "action": {"tool": "fill", "target_id": "income", "arguments": {"value": value}}
            }).status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(write, map(str, range(12)))) == [200] * 12
    steps = [event["step"] for event in client.get(f"/v1/runs/{run_id}/events").json()]
    assert steps == list(range(1, 14))
