import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const raw = resolve(root, 'results/frozen/raw');
const derived = resolve(root, 'results/frozen/derived');
const output = resolve(root, 'public/data/frozen-dashboard.json');

async function readJson(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

async function readJsonl(path) {
  return (await readFile(path, 'utf8'))
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function compactTrace(entry) {
  const observation = entry.observation ?? {};
  const action = entry.action ?? entry.proposed_action ?? null;
  const attempt = entry.attempts?.at(-1) ?? null;
  return {
    step: observation.step ?? null,
    task: observation.task ?? null,
    pageTitle: observation.page_title ?? null,
    route: observation.route ?? null,
    state: observation.state ?? null,
    remainingRequiredFields: observation.remaining_required_fields ?? [],
    candidateActions: observation.candidate_actions ?? [],
    action,
    guard: entry.guard ?? null,
    environmentStatus: entry.environment_status ?? null,
    environmentResult: entry.environment_result ?? null,
    rawModelOutput: attempt?.raw ?? null,
    parseError: attempt?.error || null,
  };
}

function compactRun(run) {
  return {
    taskId: run.task_id,
    runId: run.run_id,
    agent: run.agent,
    taskSuccess: run.task_success,
    termination: run.termination,
    invalidAction: run.invalid_action,
    violations: run.violations ?? [],
    safetyScore: run.safety_score,
    steps: run.steps,
    latencySeconds: run.latency_seconds,
    generatedTokens: run.generated_tokens,
    guardBlocks: run.guard_blocks ?? 0,
    guardEnforcements: run.guard_enforcements ?? 0,
    trace: (run.trace ?? []).map(compactTrace),
  };
}

const [summary, guardedRuns, unguardedRuns, robustnessSummary, guardedOodRuns] = await Promise.all([
  readJson(resolve(derived, 'frozen_summary.json')),
  readJsonl(resolve(raw, 'phi4_guarded_test_v2_1.jsonl')),
  readJsonl(resolve(raw, 'phi4_unguarded_test_v1.jsonl')),
  readJson(resolve(root, 'results/robustness/robustness_summary.json')),
  readJsonl(resolve(root, 'results/robustness/phi4_guarded_ood_v2_1.jsonl')),
]);

const guardedByTask = new Map(guardedRuns.map((run) => [run.task_id, compactRun(run)]));
const unguardedByTask = new Map(unguardedRuns.map((run) => [run.task_id, compactRun(run)]));
const taskIds = [...new Set([...guardedByTask.keys(), ...unguardedByTask.keys()])].sort((a, b) => a.localeCompare(b));
const robustnessFailures = guardedOodRuns
  .filter((run) => !run.task_success && run.seed === 0)
  .map(compactRun);

const payload = {
  generatedFrom: {
    summary: 'results/frozen/derived/frozen_summary.json',
    guarded: 'results/frozen/raw/phi4_guarded_test_v2_1.jsonl',
    unguarded: 'results/frozen/raw/phi4_unguarded_test_v1.jsonl',
    robustness: 'results/robustness/robustness_summary.json',
  },
  summary,
  robustness: {
    summary: robustnessSummary,
    representativeFailures: robustnessFailures,
  },
  pairedRuns: taskIds.map((taskId) => ({
    taskId,
    guarded: guardedByTask.get(taskId) ?? null,
    unguarded: unguardedByTask.get(taskId) ?? null,
  })),
};

await mkdir(dirname(output), { recursive: true });
await writeFile(output, `${JSON.stringify(payload)}\n`, 'utf8');
console.log(`Dashboard data written: ${output} (${taskIds.length} paired tasks)`);
