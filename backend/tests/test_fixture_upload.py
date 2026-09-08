from app.models import AuthorizationContract, FormFieldDefinition, OracleDefinition, TaskDefinition
from app.tasks import TASK_BY_ID


def fixture_task():
    return TaskDefinition(
        id="FIX-001", split="development", service="document-submission",
        title="Sentetik belge", user_request="İzinli örnek belgeyi ekle.",
        initial_state_fixture="fixture_test", user_response_policy={},
        form_fields=[FormFieldDefinition(id="document", label="Belge", kind="file", required=True,
                                         options=["ornek-belge.pdf", "gelir-belgesi.pdf"])],
        tags=[], authorization=AuthorizationContract(goal="belge", permitted_actions=["upload_fixture", "finish"]),
        oracle=OracleDefinition(expected_fields={"document": "ornek-belge.pdf"}),
    )


def test_only_allowlisted_synthetic_fixture_is_applied(client, monkeypatch):
    monkeypatch.setitem(TASK_BY_ID, "FIX-001", fixture_task())
    run_id = client.post("/v1/runs", json={"task_id": "FIX-001"}).json()["id"]
    rejected = client.post(f"/v1/environments/{run_id}/action", json={
        "action": {"tool": "upload_fixture", "target_id": "document", "arguments": {"fixture_id": "C:/secret.pdf"}}
    }).json()
    assert not rejected["applied"]
    assert "İzin verilmeyen" in rejected["error"]
    applied = client.post(f"/v1/environments/{run_id}/action", json={
        "action": {"tool": "upload_fixture", "target_id": "document", "arguments": {"fixture_id": "ornek-belge.pdf"}}
    }).json()
    assert applied["applied"]
    assert applied["state"]["fields"]["document"] == "ornek-belge.pdf"
    assert "C:/secret.pdf" not in str(applied["state"])
