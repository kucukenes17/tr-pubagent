"""TR-PubAgent v1 protokolünü uygulayan minimal örnek HTTP ajanı.

Çalıştırma:
    uvicorn examples.http_agent:app --port 9001
"""

from __future__ import annotations

from fastapi import FastAPI

from backend.app.models import ExternalAgentRequest, ExternalAgentResponse, ProposedAction


app = FastAPI(title="TR-PubAgent örnek ajanı")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/act", response_model=ExternalAgentResponse)
def act(request: ExternalAgentRequest) -> ExternalAgentResponse:
    observation = request.observation
    state = observation.get("state", {})
    fields = state.get("fields", {})
    form_fields = {item["id"]: item for item in observation.get("form_fields", [])}

    for field_id in observation.get("remaining_required_fields", []):
        if field_id in observation.get("askable_facts", []) and not fields.get(field_id):
            action = ProposedAction(tool="ask_user", target_id=field_id)
            break
        field = form_fields.get(field_id, {})
        if field.get("kind") == "file":
            action = ProposedAction(
                tool="upload_fixture", target_id=field_id,
                arguments={"fixture": state.get("fixture")},
            )
            break
        # Gerçek ajan burada kendi modelinden veya kullanıcı talebinden değer çıkarmalıdır.
        action = ProposedAction(
            tool="finish", target_id="task",
            reason=f"Örnek ajan {field_id} için güvenilir değer bulamadı.",
        )
        break
    else:
        if observation.get("submission_required") and not state.get("submitted"):
            confirmed = set(state.get("confirmed_actions", []))
            action = ProposedAction(
                tool="submit" if "submit" in confirmed else "request_confirmation",
                target_id="submit",
            )
        else:
            action = ProposedAction(tool="finish", target_id="task")

    return ExternalAgentResponse(action=action, metadata={"agent": "example-v1"})
