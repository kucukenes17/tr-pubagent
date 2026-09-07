"""Sürümlenmiş HTTP sözleşmesi üzerinden harici ajan adaptörü."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import ValidationError

from .models import ExternalAgentRequest, ExternalAgentResponse, ProposedAction


PROTOCOL_VERSION = "tr-pubagent.agent.v1"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ExternalAgentError(RuntimeError):
    """Ağ, HTTP veya ajan protokolü hatası."""


def validate_agent_url(endpoint: str, allow_remote: bool = False) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Ajan adresi geçerli bir http(s) URL olmalı")
    if parsed.username or parsed.password:
        raise ValueError("Kimlik bilgisini URL'ye koymayın; TR_PUBAGENT_AGENT_TOKEN kullanın")
    if parsed.hostname.lower() not in LOOPBACK_HOSTS and not allow_remote:
        raise ValueError(
            "Uzak ajan adresleri varsayılan olarak kapalıdır; bilinçli kullanım için --allow-remote ekleyin"
        )
    return endpoint


def sanitized_agent_url(endpoint: str) -> str:
    """Sonuç dosyasına sorgu/fragment veya kullanıcı bilgisi yazmadan adres kaydeder."""
    parsed = urlsplit(endpoint)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


@dataclass
class HttpAgentPolicy:
    endpoint: str
    timeout_seconds: float = 30.0
    allow_remote: bool = False
    token_env: str = "TR_PUBAGENT_AGENT_TOKEN"
    client: httpx.Client | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.endpoint = validate_agent_url(self.endpoint, self.allow_remote)

    def next_action(
        self,
        task_id: str,
        observation: dict[str, Any],
        feedback: str = "",
    ) -> tuple[ProposedAction, dict[str, Any]]:
        request = ExternalAgentRequest(
            run_id=str(observation.get("run_id", "")),
            task_id=task_id,
            observation=observation,
            feedback=feedback,
        )
        headers = {"Content-Type": "application/json"}
        token = os.getenv(self.token_env)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.post(
                self.endpoint,
                json=request.model_dump(mode="json"),
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
            parsed = ExternalAgentResponse.model_validate(payload)
        except httpx.HTTPStatusError as error:
            raise ExternalAgentError(
                f"Ajan HTTP {error.response.status_code} döndürdü"
            ) from error
        except ValidationError as error:
            raise ExternalAgentError(f"Ajan yanıtı {PROTOCOL_VERSION} şemasına uymuyor: {error}") from error
        except ValueError as error:
            raise ExternalAgentError("Ajan geçerli JSON döndürmedi") from error
        except httpx.HTTPError as error:
            raise ExternalAgentError(f"Ajana ulaşılamadı: {error}") from error
        finally:
            if owns_client:
                client.close()
        return parsed.action, parsed.metadata
