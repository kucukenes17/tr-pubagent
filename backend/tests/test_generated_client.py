from scripts.generate_api_client import render
from app.main import app


def test_generated_typescript_client_matches_openapi():
    output = render(app.openapi())
    generated = (__import__("pathlib").Path(__file__).resolve().parents[2] / "lib/generated/tr-pubagent-api.ts")
    assert generated.read_text(encoding="utf-8") == output
    assert "OpenAPI-SHA256:" in output
    assert '"apply_action_v1_environments__run_id__action_post"' in output
    assert "ApplyActionRequest" in output
