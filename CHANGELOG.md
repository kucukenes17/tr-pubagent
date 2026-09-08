# Changelog

All notable changes to TR PubAgent are documented in this file.

## [1.0.0] - 2026-09-09

### Added

- 80-task Turkish synthetic benchmark across six public-service-like domains.
- Authorization-aware Rule Guard with evidence grounding, confirmation gates,
  privacy checks, loop detection and safe execution controls.
- Frozen Phi-4 development, validation and test evaluation with raw JSONL
  traces and statistical summaries.
- Human-authored 24-task OOD suite evaluated over three seeds.
- Qwen2.5-7B cross-model confirmation.
- Rule-only, XLM-R ML-only and Hybrid Guard ablations, including the
  class-weighted XLM-R v3 negative result.
- Post-hoc Guard v2.2 analysis, kept separate from the frozen v2.1 claim.
- Bring-your-own-agent HTTP protocol and example client.
- Playwright/Chromium transfer benchmark using local synthetic HTML portals.
- Interactive results dashboard and step-by-step decision replays.
- Apache-2.0 code license, CC BY 4.0 research-data scope, third-party notices
  and machine-readable citation metadata.

### Key results

- Frozen structured test: Phi-4 success 0/40 → 40/40; observed violations
  10 → 0.
- Human-authored OOD: Phi-4 success 6/72 → 66/72; observed violations 12 → 0.
- Cross-model OOD: Qwen2.5-7B success 8/24 → 24/24; observed violations 2 → 0.
- Browser transfer: Phi-4 success 0/40 → 25/40; observed state-corruption
  violations 11 → 0; generated tokens reduced by 53.9%.

### Scope

All benchmark tasks, portal states and identities are synthetic. Chromium
experiments use a real browser engine but local synthetic pages. Version 1.0.0
does not claim performance on live public-service websites or real users.
