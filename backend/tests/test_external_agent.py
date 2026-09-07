from __future__ import annotations

import httpx
import pytest

from app.external_agent import ExternalAgentError, HttpAgentPolicy, sanitized_agent_url, validate_agent_url


def test_remote_endpoint_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="--allow-remote"):
        validate_agent_url("https://agent.example/act")
    assert validate_agent_url("https://agent.example/act", allow_remote=True).endswith("/act")


@pytest.mark.parametrize("url", ["file:///tmp/agent", "localhost:9001/act", "http://u:p@localhost/act"])
def test_unsafe_or_invalid_agent_urls_are_rejected(url):
    with pytest.raises(ValueError):
        validate_agent_url(url)


def test_sanitized_url_drops_query_and_fragment():
    assert sanitized_agent_url("http://localhost:9001/act?secret=x#part") == "http://localhost:9001/act"


def test_http_policy_sends_versioned_request_and_parses_action(monkeypatch):
    monkeypatch.setenv("TR_PUBAGENT_AGENT_TOKEN", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        body = __import__("json").loads(request.content)
        assert body["protocol_version"] == "tr-pubagent.agent.v1"
        assert body["task_id"] == "BUR-005"
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json={
            "protocol_version": "tr-pubagent.agent.v1",
            "action": {"tool": "finish", "target_id": "task", "arguments": {}},
            "metadata": {"model": "fake"},
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as mock_client:
        policy = HttpAgentPolicy("http://localhost:9001/act", client=mock_client)
        action, metadata = policy.next_action(
            "BUR-005", {"run_id": "run-1", "candidate_actions": ["finish"]}
        )
    assert action.tool == "finish"
    assert metadata == {"model": "fake"}


def test_http_policy_rejects_wrong_protocol_response():
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={
        "protocol_version": "future-v2",
        "action": {"tool": "finish", "target_id": "task"},
    }))
    with httpx.Client(transport=transport) as mock_client:
        policy = HttpAgentPolicy("http://127.0.0.1:9001/act", client=mock_client)
        with pytest.raises(ExternalAgentError, match="şemasına uymuyor"):
            policy.next_action("BUR-005", {"run_id": "run-1"})


def test_api_accepts_safe_external_agent_name(client):
    response = client.post(
        "/v1/runs", json={"task_id": "BUR-005", "agent": "my-agent.v1", "seed": 7}
    )
    assert response.status_code == 201
    assert response.json()["agent"] == "my-agent.v1"


def test_api_rejects_unsafe_external_agent_name(client):
    response = client.post(
        "/v1/runs", json={"task_id": "BUR-005", "agent": "../../bad name", "seed": 0}
    )
    assert response.status_code == 422
