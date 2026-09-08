# TR PubAgent

TR PubAgent is an open research platform for evaluating Turkish web agents on public-service-like tasks. It measures not only task completion, but also authorization boundaries, missing information, privacy, irreversible actions, language interpretation, and state preservation.

The interactive portal lab exposes six synthetic service surfaces—scholarship, course registration, appointment, municipality, social aid, and document submission—through one shared guarded execution flow. It is a demonstrator for the benchmark contract, not a connection to a real institution.

> This repository is not a government service. It connects to no real institution, uses no personal data, and runs entirely on synthetic identities and portal states.

## Frozen Phi-4 result

| System | Success on 40 synthetic test tasks | Invalid actions | Observed violations | Mean steps |
| --- | ---: | ---: | ---: | ---: |
| Unguarded v1 | 0/40 (0%) | 25 | 10 | 9.20 |
| TR-PubGuard v2.1 | 40/40 (100%) | 0 | 0 | 2.20 |

Guarded v2.1 was frozen before validation as `guarded-v2.1-frozen@91f2fb1`. The paired final-test difference has an exact McNemar value of `p=1.82×10⁻¹²`; the Wilson 95% interval for guarded success is 91.24%–100%. Generated tokens fell by 92.7%.

These numbers apply only to the frozen, programmatically generated synthetic split. They do not imply perfect performance on real public-service websites.

## Human-authored OOD result

After the algorithm was frozen under the `robustness-protocol-v1` tag, 24 new tasks were run with three seeds. Across 72 paired runs, Unguarded succeeded in 6/72 (8.3%) and Guarded v2.1 in 66/72 (91.7%). The task-clustered bootstrap 95% interval for the success gain was +66.7 to +95.8 percentage points and exact McNemar was `p=1.73×10⁻¹⁸`. Invalid actions fell from 45 to 0 and observed violations from 12 to 0.

All six guarded failures clustered in two tasks across every seed: numeric evidence extraction and grounding a negative day preference into a select action. The frozen result is retained.

## Guard v2.2 post-hoc result

After those failures were observed, a separately labeled and narrowly scoped v2.2 correction was evaluated on the same 72 runs. Success increased from 66/72 to 72/72: six runs were v2.2-only successes, with no regressions or observed violations. Exact McNemar was `p=0.03125`; because the gains clustered in two unique tasks, the task-clustered bootstrap 95% interval was 0 to 20.83 percentage points. This post-hoc result does not replace the frozen v2.1 claim.

## Qwen2.5-7B cross-model confirmation

A separately pre-specified protocol ran the same 24 OOD tasks deterministically with `Qwen/Qwen2.5-7B-Instruct`. Unguarded succeeded on 8/24 (33.3%) and Guarded v2.1 on 24/24 (100%). Invalid actions fell from 4 to 0 and observed privacy violations from 2 to 0; paired exact McNemar was `p=3.05×10⁻⁵`.

This is second-model evidence that the guarded gain is not unique to Phi-4. It remains limited to two model families, 24 synthetic OOD tasks, and one deterministic seed. Raw traces and checksums are published under [`results/cross-model/qwen2_5_7b`](results/cross-model/qwen2_5_7b).

## Rule / ML / Hybrid ablation

The XLM-R risk classifier reached macro-F1 `1.0` on the held-out portion of 3,000 templated synthetic examples. On the same 72 OOD runs, Rule, ML-decision, and Hybrid systems each achieved 66/72 (91.7%) safe success. Rule recorded 141 blocks and 30 safe-action enforcements, ML 108 blocks and no enforcements, while Hybrid reproduced Rule's 141/30 intervention profile. The pre-defined H3 hypothesis—strict Hybrid superiority over both components—was not supported.

In a separately versioned follow-up with class-weighted XLM-R v3, in-distribution test macro-F1 remained `1.0`, but human-authored OOD success fell to 57/72 (79.2%) for both ML-only and Hybrid while Rule Guard remained at 66/72 (91.7%). ML-only produced three language-interpretation violations; Hybrid eliminated those violations but did not recover the task loss caused by false-positive blocks. The result demonstrates that an in-distribution classifier score is neither an OOD utility result nor an end-to-end agent-safety guarantee. Versioned traces are published under [`results/robustness/v3-weighted`](results/robustness/v3-weighted).

This negative result shows that a perfect synthetic classification score does not guarantee additional end-to-end agent utility. “ML Guard” changes only the decision guard; the public action contract and safe execution controller are shared by all guarded systems.

## Real Chromium transfer result

Under a separately frozen Browser v2 protocol, Phi-4 operated local synthetic HTML forms through Playwright and actual Chromium instead of receiving structured simulator state. Across 40 paired test tasks, Unguarded completed 0/40 and Rule Guard 25/40 (62.5%). Observed state-corruption violations fell from 11 to 0; exact McNemar was `p=5.96×10⁻⁸` and Fisher's exact test for violation runs was `p=4.41×10⁻⁴`.

The guard reduced mean steps from 18.68 to 8.20, generated tokens from 32,013 to 14,751, and total latency from 2,944.83 to 1,224.97 seconds—a measured 2.40× speedup. This uses a real browser engine and DOM, but the pages remain local and synthetic; it is not evidence of performance on live government portals. Raw traces, paired task data, and checksums are published under [`results/browser/phi4-v2`](results/browser/phi4-v2).

## What is included

- TR-PubBench: 80 deterministic Turkish tasks across six service families.
- Human-authored OOD suite: 24 additional tasks with leakage checks and a three-seed runner.
- Phi-4 and Qwen2.5-7B unguarded/evidence-grounded comparisons.
- Deterministic authorization, privacy, confirmation, and state-preservation checks.
- Experimental XLM-R ML-only and Hybrid Guard ablation infrastructure.
- Versioned bring-your-own-agent HTTP protocol and local direct/guarded evaluator.
- FastAPI + SQLite environment and evaluator.
- A result-driven dashboard with paired JSONL trace replay.
- A frozen Playwright/Chromium transfer benchmark with 80 model runs.
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

The main 80-task experiment, 144-run Phi-4 OOD comparison, Guard v2.2 post-hoc analysis, Rule/ML/Hybrid ablation, 48-run Qwen2.5-7B cross-model confirmation, 80-run Chromium transfer comparison, and clean-runner Docker smoke test are complete. See [the current plan](docs/PLAN_STATUS.md), [experiment report](docs/EXPERIMENT_RESULTS.md), [browser protocol](docs/BROWSER_MODEL_PROTOCOL_V2.md), [OOD protocol](docs/ROBUSTNESS_PROTOCOL.md), and [post-hoc protocol](docs/POSTHOC_V22_PROTOCOL.md).

Source code is [Apache-2.0](LICENSE). Benchmark tasks, synthetic data, and
project-produced research artifacts are released under
[CC BY 4.0](DATA_LICENSE.md) within the stated scope. Upstream model weights are
not included and retain their own terms; see [third-party notices](THIRD_PARTY.md)
and `CITATION.cff`.
