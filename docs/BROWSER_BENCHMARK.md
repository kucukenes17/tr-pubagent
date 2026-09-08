# Local browser benchmark v1

This is a new execution path, not a relabeling of any frozen experiment.
The published Phi-4/Qwen results used structured API observations. They did
**not** use this Playwright environment. The hosted `/portal` remains an
independent demonstration UI and has not been changed by this work.

## What actually runs

The local FastAPI service exposes an opt-in `/browser/runs/{run_id}` HTML
portal. Each task uses its real benchmark field definitions. An external
agent receives an accessibility tree and visible recent-action messages.
Playwright fills/selects the actual controls and submits their HTML forms.
The same backend records the action in SQLite; the deterministic evaluator
checks the resulting state. Only run creation and evaluation use HTTP
directly in the runner. No gold state is sent to the agent.

Supported tools: `fill`, `select`, `upload_fixture`, `ask_user`, `request_confirmation`,
`submit`, `finish`, `click` (reset only), and `navigate` (current run only).
`target_id` identifiers are shown next to the controls. `fill` takes
`arguments.value`; `select` takes `arguments.option`; `upload_fixture` takes
`arguments.fixture_id`. A file field exposes only its task-defined synthetic
fixture IDs in a select control. No local path, arbitrary file bytes, file
chooser or host filesystem access is exposed to the agent.

The UI deliberately does not prevent unauthorized submission or filling a
private field: those are measurable unsafe actions. The deterministic user
answers only when its question button is used. Closed runs reject further
HTML actions. This path adds no guard of its own; an agent can implement
guarding before returning an action.

## Run locally (from repository root)

Use a virtual environment with `backend/requirements.txt` installed, then:

```powershell
python -m playwright install chromium
$env:TR_PUBAGENT_BROWSER_PORTAL = "1"
$env:TR_PUBAGENT_DB = "$PWD\outputs\browser-runs.db"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In another terminal, with your own locally running agent endpoint:

```powershell
python -m benchmark.run_browser_agent --agent-url http://127.0.0.1:9000/action --task-ids BUR-001 BUR-005 --output outputs/browser/my-agent-v1.jsonl
```

The HTTP envelope stays `tr-pubagent.agent.v1`, but `observation` now has
`aria_tree`, `visible_messages`, `url`, `page_title`, `run_id`, `step`, and
`status`. An existing agent expecting structured `form_fields` must adapt;
the old example is not automatically browser-compatible. The CLI refuses
to overwrite a result file. Use a new filename for each experiment. No GPU,
external provider or paid API is started by this command unless your own
agent endpoint does so.

## Acceptance tests

```powershell
python -m pytest backend/browser_tests -q
python -m pytest backend/tests -q
```

The browser suite launches a temporary loopback Uvicorn service and actual
Chromium, not a mocked DOM or TestClient. It checks all 80 tasks across six
services with a **gold-aware scripted oracle**. This establishes reachability,
not model accuracy. Further checks cover origin/route filtering, run
isolation, unsafe unconfirmed submission, closed runs, invalid tool targets,
and an external HTTP protocol stub receiving only DOM observations.

CI installs the pinned Playwright browser before collecting these tests.
No database or previous experiment artifact is reused.

Local verification, 8 September 2026: **152 tests passed** with **90.47%**
backend statement coverage, including the three real-browser tests (one
iterates over all 80 tasks). Executed with Playwright 1.55.0 / Chromium build
1187 on Windows. The 80-task gold-aware reachability check passed 80/80.
The CI workflow was updated locally; no remote CI run or release is claimed.

## Security and scope limits

- Portal disabled unless explicitly enabled; loopback client and host only.
- Browser network access restricted to the exact origin, port and current
  run page. Other runs, gold APIs and external URLs are denied; service
  workers are disabled. CSP prohibits scripts and external resources.
- The adapter never exposes arbitrary selectors, JavaScript, shell commands
  or arbitrary filesystem uploads as agent tools.
- This is **not a sandbox for hostile agent code**. The local API still has
  trusted research endpoints exposing task definitions; a separately
  running malicious process could request them outside this browser.
  Deploy only on loopback in a trusted research environment. No public
  backend deployment or public-agent security claim is made.
- New model measurements and guarded browser comparisons
  and responsive visual acceptance of this local test surface remain
  separate work. Existing frozen numbers must not be reused as browser
  performance results.
