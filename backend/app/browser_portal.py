"""Opt-in loopback-only HTML benchmark surface (not the hosted demo).

Only public observations are rendered. Every operation uses a real HTML form;
the browser runner cannot inject an action directly into the simulator.
"""

from __future__ import annotations

import json
import os
from html import escape
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .models import ApplyActionRequest, ProposedAction


LOOPBACK = {"127.0.0.1", "localhost", "::1"}
HEADERS = {
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}


def check_local(request: Request) -> None:
    if os.getenv("TR_PUBAGENT_BROWSER_PORTAL") != "1":
        raise HTTPException(404, "Tarayıcı portalı etkin değil")
    if not request.client or request.client.host not in LOOPBACK or request.url.hostname not in LOOPBACK:
        raise HTTPException(403, "Yalnızca yerel deneyler")
    origin = request.headers.get("origin")
    if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
        raise HTTPException(403, "Farklı kaynaktan form gönderilemez")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Farklı kaynaktan form gönderilemez")


def render_portal(obs: dict, status: str) -> str:
    def e(value) -> str:
        return escape(str(value), quote=True)

    def form(tool: str, target: str, label: str, control: str = "") -> str:
        disabled = " disabled" if status != "running" else ""
        return (
            f'<form method="post" data-tool="{e(tool)}" data-target="{e(target)}">'
            f'<input type="hidden" name="tool" value="{e(tool)}">'
            f'<input type="hidden" name="target" value="{e(target)}">'
            f'{control}<button{disabled}>{e(label)} [{e(target)}]</button></form>'
        )

    fields = []
    for field in obs["form_fields"]:
        target, label = field["id"], field["label"]
        value = field["value"] if field["value"] is not None else ""
        prefix = f'<label for="field-{e(target)}">{e(label)} [{e(target)}]</label>'
        if field["read_only"]:
            fields.append(prefix + f'<input id="field-{e(target)}" value="{e(value)}" readonly>')
        elif field["kind"] == "text":
            fields.append(form("fill", target, "Kaydet", prefix + f'<input id="field-{e(target)}" name="value" value="{e(value)}">'))
        elif field["kind"] == "select":
            options = '<option value="">Seçiniz</option>' + "".join(
                f'<option value="{e(option)}"{" selected" if option == value else ""}>{e(option)}</option>'
                for option in field["options"]
            )
            fields.append(form("select", target, "Seçimi kaydet", prefix + f'<select id="field-{e(target)}" name="value">{options}</select>'))
        else:
            options = '<option value="">Sentetik fixture seçin</option>' + "".join(
                f'<option value="{e(option)}"{" selected" if option == value else ""}>{e(option)}</option>'
                for option in field["options"]
            )
            fields.append(form("upload_fixture", target, "Fixture yükle", prefix + f'<select id="field-{e(target)}" name="fixture_id">{options}</select>'))
    questions = "".join(form("ask_user", fact, "Kullanıcıya sor") for fact in obs["askable_facts"])
    # Unsafe actions remain available: this is an unguarded environment, not an
    # oracle-assisted UI that makes unsafe trajectories impossible to measure.
    operations = form("request_confirmation", "submit", "Gönderim onayı iste")
    operations += form("submit", "submit", "Başvuruyu gönder")
    operations += form("click", "reset", "Formu sıfırla")
    operations += form("finish", "task", "Görevi bitir")
    messages = e(json.dumps(obs["recent_actions"], ensure_ascii=False, indent=2))
    return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(obs['page_title'])} — TR-PubAgent yerel deney</title>
<style>body{{font:16px/1.6 system-ui;margin:0;background:#f1f5f9;color:#172554}}
main{{max-width:1080px;margin:32px auto;padding:24px;background:white;border-radius:16px}}
.columns{{display:grid;grid-template-columns:1fr 1fr;gap:32px}}form{{margin:16px 0}}
label{{display:block;font-weight:600}}input,select,button{{font:inherit;padding:10px;border:1px solid #94a3b8;border-radius:6px;max-width:100%;box-sizing:border-box}}
button{{background:#1d4ed8;color:white;cursor:pointer;margin:4px}}button:disabled{{opacity:.5}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
@media(max-width:700px){{.columns{{grid-template-columns:1fr}}main{{margin:8px}}}}</style></head>
<body><main data-run-id="{e(obs['run_id'])}" data-step="{obs['step']}" data-status="{e(status)}">
<p>TR-PubAgent · Yerel tarayıcı deneyi · Sentetik veriler</p><h1>{e(obs['page_title'])}</h1>
<p id="task">{e(obs['task'])}</p><p>Durum: {e(status)} · Adım: {obs['step']} / {obs['max_steps']}</p>
<div class="columns"><section aria-label="Başvuru alanları"><h2>Başvuru</h2>{''.join(fields)}</section>
<section aria-label="Kullanıcı ve işlemler"><h2>Kullanıcıya sor</h2>{questions}<h2>İşlemler</h2>{operations}</section></div>
<h2>Son işlemler ve yanıtlar</h2><pre role="status">{messages}</pre>
<p>Gönderildi: {e(obs['state']['submitted'])} · Onaylar: {e(', '.join(obs['state']['confirmed_actions']))}</p>
</main></body></html>'''


def register_browser_portal(app, observation, get_run, apply_action) -> None:
    @app.get("/browser/runs/{run_id}", response_class=HTMLResponse, include_in_schema=False)
    def page(run_id: str, request: Request):
        check_local(request)
        return HTMLResponse(render_portal(observation(run_id), get_run(run_id).status), headers=HEADERS)

    @app.post("/browser/runs/{run_id}", include_in_schema=False)
    async def action(run_id: str, request: Request):
        check_local(request)
        if get_run(run_id).status != "running":
            raise HTTPException(409, "Koşu kapandı")
        if request.headers.get("content-type", "").split(";")[0] != "application/x-www-form-urlencoded":
            raise HTTPException(415, "HTML formu gerekli")
        body = await request.body()
        if len(body) > 16384:
            raise HTTPException(413, "Form çok büyük")
        params = parse_qs(body.decode("utf-8"), keep_blank_values=True)
        if any(len(values) != 1 for values in params.values()):
            raise HTTPException(400, "Yinelenen form alanı")
        tool = params.get("tool", [""])[0]
        target = params.get("target", [""])[0]
        targets = observation(run_id)["action_targets"]
        targets.update({"submit": ["submit"], "request_confirmation": ["submit"], "click": ["reset"]})
        if target not in targets.get(tool, []):
            raise HTTPException(400, "Görünür bir form eylemi değil")
        arguments = {}
        if tool in {"fill", "select"}:
            arguments["value" if tool == "fill" else "option"] = params.get("value", [""])[0]
        elif tool == "upload_fixture":
            arguments["fixture_id"] = params.get("fixture_id", [""])[0]
        apply_action(run_id, ApplyActionRequest(action=ProposedAction(tool=tool, target_id=target, arguments=arguments)))
        return RedirectResponse(f"/browser/runs/{run_id}", status_code=303, headers=HEADERS)
