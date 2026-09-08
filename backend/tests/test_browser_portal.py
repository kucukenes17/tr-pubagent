from app.browser_env import SafeBrowserEnvironment
from app.browser_portal import render_portal
from app.main import observation
import pytest


def test_browser_portal_is_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv("TR_PUBAGENT_BROWSER_PORTAL", raising=False)
    assert client.get("/browser/runs/" + "a" * 32).status_code == 404


def test_browser_portal_blocks_non_loopback_client(client, monkeypatch):
    monkeypatch.setenv("TR_PUBAGENT_BROWSER_PORTAL", "1")
    assert client.get("/browser/runs/" + "a" * 32).status_code == 403


def test_html_contains_only_public_observation_and_escapes_text(client):
    run_id = client.post("/v1/runs", json={"task_id": "BUR-001"}).json()["id"]
    obs = observation(run_id)
    obs["task"] = '<script>alert("x")</script>'
    html = render_portal(obs, "running")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "expected_fields" not in html
    assert "user_response_policy" not in html
    assert 'data-tool="ask_user"' in html
    assert 'name="value"' in html


@pytest.mark.parametrize("url", ["https://example.com", "http://127.0.0.1/path", "http://user@localhost", "file:///tmp", "http://127.0.0.1?q=x"])
def test_browser_rejects_nonlocal_origins(url):
    with pytest.raises(ValueError):
        SafeBrowserEnvironment(url)


def test_network_allowlist_is_exact_run_and_origin():
    env = SafeBrowserEnvironment("http://127.0.0.1:8000")
    env.run_path = "/browser/runs/" + "a" * 32
    assert env.allows_url("http://127.0.0.1:8000" + env.run_path)
    for url in [
        "http://127.0.0.1:8001" + env.run_path,
        "http://localhost:8000" + env.run_path,
        "http://127.0.0.1:8000/v1/tasks/BUR-001",
        "http://127.0.0.1:8000/browser/runs/" + "b" * 32,
        "http://127.0.0.1:8000" + env.run_path + "?x=1",
        "http://example.com" + env.run_path,
    ]:
        assert not env.allows_url(url)
