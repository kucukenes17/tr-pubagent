# TR PubAgent

TR PubAgent is an open research platform for evaluating Turkish web agents on public-service-like tasks. It measures not only task completion, but also authorization boundaries, missing information, privacy, irreversible actions, language interpretation, and state preservation.

> This repository is not a government service. It connects to no real institution, uses no personal data, and runs entirely on synthetic identities and portal states.

## Frozen Phi-4 result

| System | Success on 40 synthetic test tasks | Invalid actions | Observed violations | Mean steps |
| --- | ---: | ---: | ---: | ---: |
| Unguarded v1 | 0/40 (0%) | 25 | 10 | 9.20 |
| TR-PubGuard v2.1 | 40/40 (100%) | 0 | 0 | 2.20 |

Guarded v2.1 was frozen before validation as `guarded-v2.1-frozen@91f2fb1`. The paired final-test difference has an exact McNemar value of `p=1.82×10⁻¹²`; the Wilson 95% interval for guarded success is 91.24%–100%. Generated tokens fell by 92.7%.

These numbers apply only to the frozen, programmatically generated synthetic split. They do not imply perfect performance on real public-service websites.

## What is included

- TR-PubBench: 80 deterministic Turkish tasks across six service families.
- Human-authored OOD suite: 24 additional tasks with leakage checks and a three-seed runner.
- Phi-4 unguarded and evidence-grounded guarded agents.
- Deterministic authorization, privacy, confirmation, and state-preservation checks.
- Experimental XLM-R ML-only and Hybrid Guard ablation infrastructure.
- FastAPI + SQLite environment and evaluator.
- A result-driven dashboard with paired JSONL trace replay.
- Frozen raw outputs, checksums, protocol deviations, data card, and system card.

## Quick start

```bash
npm install
npm run dev
```

For the API:

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Run validation:

```bash
npm run typecheck
npm run lint
npm run build
python -m pytest backend/tests --basetemp=.pytest-tmp
python -m benchmark.check_task_leakage --strict
```

## Research status

The main 80-task experiment and frozen result are complete. The OOD and four-system Rule/ML/Hybrid runners are pre-registered and ready for GPU execution; no unobserved result is claimed. See [the current plan](docs/PLAN_STATUS.md), [experiment report](docs/EXPERIMENT_RESULTS.md), and [OOD protocol](docs/ROBUSTNESS_PROTOCOL.md).

Code is Apache-2.0. Dataset and result licensing remains subject to the repository's final data-license audit.
