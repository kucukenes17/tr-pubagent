'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleHelp,
  Pause,
  Play,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  NativeSelect,
  NativeSelectOption,
} from '@/components/ui/native-select';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { SiteHeader } from '@/components/site-header';
import type {
  FrozenDashboardData,
  FrozenRun,
  FrozenTraceStep,
} from '@/lib/research-data';

type AgentKey = 'unguarded' | 'guarded';
const toolNames: Record<string, string> = {
  fill: 'Alanı doldur',
  select: 'Seçim yap',
  ask_user: 'Kullanıcıya sor',
  request_confirmation: 'Onay iste',
  submit: 'Gönder',
  finish: 'Bitir',
  upload_fixture: 'Dosya yükle',
};
const labelViolation = (v: string) =>
  v === 'PRIVACY_VIOLATION'
    ? 'Gizlilik ihlali'
    : v === 'LANGUAGE_INTERPRETATION_ERROR'
      ? 'Dil yorumlama hatası'
      : v;
function stepStatus(step: FrozenTraceStep) {
  if (step.guard?.decision.startsWith('BLOCK'))
    return {
      label:
        step.guard.decision === 'BLOCK'
          ? 'Guard engelledi'
          : 'Guard yönlendirdi',
      icon: AlertTriangle,
      cls: 'border-amber-200 bg-amber-50 text-amber-900',
    };
  if (step.parseError)
    return {
      label: 'Ayrıştırma hatası',
      icon: XCircle,
      cls: 'border-red-200 bg-red-50 text-red-800',
    };
  if (
    step.environmentResult?.applied === false ||
    (step.environmentStatus ?? 0) >= 400
  )
    return {
      label: 'Eylem uygulanmadı',
      icon: XCircle,
      cls: 'border-red-200 bg-red-50 text-red-800',
    };
  if (step.environmentResult?.applied == null)
    return {
      label: 'Uygulama kaydı yok',
      icon: CircleHelp,
      cls: 'border-slate-200 bg-slate-50 text-slate-700',
    };
  if (
    step.action?.tool === 'ask_user' ||
    step.action?.tool === 'request_confirmation'
  )
    return {
      label: 'Bilgi / onay istedi',
      icon: CircleHelp,
      cls: 'border-blue-200 bg-blue-50 text-blue-800',
    };
  if (step.action?.tool === 'finish')
    return {
      label: 'Bitirme eylemi',
      icon: ShieldCheck,
      cls: 'border-emerald-200 bg-emerald-50 text-emerald-900',
    };
  return {
    label: 'Uygulandı',
    icon: CheckCircle2,
    cls: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  };
}
function RunSummary({
  run,
  guarded,
  selected,
  onSelect,
}: {
  run: FrozenRun;
  guarded: boolean;
  selected: boolean;
  onSelect: () => void;
}) {
  const name = guarded ? 'Guarded v2.1' : 'Unguarded v1';
  return (
    <button
      type="button"
      aria-pressed={selected}
      aria-label={`${name} koşusunu göster`}
      onClick={onSelect}
      className={`w-full rounded-lg border p-4 text-left ${selected ? 'border-slate-600 bg-slate-50 ring-1 ring-slate-600' : 'border-slate-200 bg-white'}`}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <span
          className={`flex items-center gap-2 font-semibold ${guarded ? 'guarded-text' : 'unguarded-text'}`}
        >
          <i className={`system-marker ${guarded ? '' : 'unguarded'}`} />
          {name}
        </span>
        <Badge
          className={
            run.taskSuccess
              ? 'bg-emerald-700 text-white'
              : 'bg-red-700 text-white'
          }
        >
          {run.taskSuccess ? 'Başarılı' : 'Başarısız'}
        </Badge>
      </div>
      <dl className="grid grid-cols-3 gap-2 text-sm">
        <div>
          <dt className="text-slate-500">Adım</dt>
          <dd className="mt-1 text-xl font-semibold">{run.steps}</dd>
        </div>
        <div>
          <dt className="text-slate-500">İhlal</dt>
          <dd className="mt-1 text-xl font-semibold">
            {run.violations.length}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Token</dt>
          <dd className="mt-1 text-xl font-semibold">{run.generatedTokens}</dd>
        </div>
      </dl>
      <p className="mt-3 break-words text-sm text-slate-600">
        Sonlanma: <code>{run.termination}</code> · Geçersiz eylem:{' '}
        {run.invalidAction ? 'Var' : 'Yok'}
      </p>
    </button>
  );
}
function TechnicalDetails({ title, value }: { title: string; value: unknown }) {
  return (
    <details className="trace-details">
      <summary>{title}</summary>
      <pre>
        {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}
export function ReplayExplorer() {
  const [data, setData] = useState<FrozenDashboardData | null>(null);
  const [failed, setFailed] = useState(false);
  const [taskId, setTaskId] = useState('');
  const [agent, setAgent] = useState<AgentKey>('unguarded');
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/data/frozen-dashboard.json', { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json() as Promise<FrozenDashboardData>;
      })
      .then((payload) => {
        setData(payload);
        const illustrative =
          payload.pairedRuns.find(
            (p) =>
              (p.unguarded?.violations.length ?? 0) > 0 &&
              (p.guarded?.guardBlocks ?? 0) > 0,
          ) ??
          payload.pairedRuns.find(
            (p) => (p.unguarded?.violations.length ?? 0) > 0,
          ) ??
          payload.pairedRuns[0];
        setTaskId(illustrative?.taskId ?? '');
      })
      .catch((err) => {
        if (err.name !== 'AbortError') setFailed(true);
      });
    return () => controller.abort();
  }, []);
  const pair = useMemo(
    () => data?.pairedRuns.find((p) => p.taskId === taskId) ?? null,
    [data, taskId],
  );
  const run = pair?.[agent] ?? null;
  const trace = run?.trace ?? [];
  const step = trace[active];
  useEffect(() => {
    if (!playing || trace.length < 2 || active >= trace.length - 1) return;
    const timer = window.setInterval(
      () => setActive((v) => Math.min(v + 1, trace.length - 1)),
      1500,
    );
    return () => window.clearInterval(timer);
  }, [playing, trace.length, active]);
  const selectAgent = (key: AgentKey) => {
    setAgent(key);
    setActive(0);
    setPlaying(false);
  };
  if (failed)
    return (
      <main>
        <SiteHeader />
        <section id="content" className="research-workspace">
          <h1>Karar izleri yüklenemedi</h1>
          <p>Bağlantınızı kontrol edip yeniden deneyin.</p>
          <Button onClick={() => window.location.reload()}>Yeniden dene</Button>
        </section>
      </main>
    );
  if (!data)
    return (
      <main>
        <SiteHeader />
        <section id="content" className="research-workspace" aria-busy="true">
          <Skeleton className="h-36" />
          <Skeleton className="mt-5 h-96" />
        </section>
      </main>
    );
  if (!pair || !run || !step)
    return (
      <main>
        <SiteHeader />
        <section id="content" className="research-workspace">
          <h1>Bu koşuda gösterilebilir karar izi yok.</h1>
          <Button
            onClick={() => {
              setTaskId(data.pairedRuns[0]?.taskId ?? '');
              selectAgent('unguarded');
            }}
          >
            İlk göreve dön
          </Button>
        </section>
      </main>
    );
  const status = stepStatus(step);
  const StatusIcon = status.icon;
  const taskText =
    step.task ??
    pair.guarded?.trace[0]?.task ??
    pair.unguarded?.trace[0]?.task ??
    '';
  const action = step.action;
  const applied = step.environmentResult?.applied;
  const problemIndex = trace.findIndex(
    (s) =>
      s.parseError ||
      s.environmentResult?.applied === false ||
      (s.environmentStatus ?? 0) >= 400 ||
      s.guard?.decision.startsWith('BLOCK'),
  );
  return (
    <main className="subpage">
      <SiteHeader />
      <section id="content" className="research-workspace">
        <header className="research-heading">
          <div>
            <div className="eyebrow">Karar izleri / Frozen final test</div>
            <h1>Bir sonucu, adım adım sorgula.</h1>
            <p>
              Aynı görevin korumasız ve korumalı koşuları. Her sistem kendi
              karar sırasıyla gösterilir; adım numaraları bire bir eşleşme
              anlamına gelmez.
            </p>
          </div>
          <div className="w-full sm:w-auto">
            <label
              className="mb-2 block text-sm font-medium"
              htmlFor="task-select"
            >
              Final test görevi · {data.pairedRuns.length} eşlenmiş kayıt
            </label>
            <NativeSelect
              className="w-full sm:min-w-64"
              id="task-select"
              value={taskId}
              onChange={(e) => {
                setTaskId(e.target.value);
                setActive(0);
                setPlaying(false);
              }}
            >
              {data.pairedRuns.map((p) => (
                <NativeSelectOption value={p.taskId} key={p.taskId}>
                  {p.taskId}
                  {p.unguarded?.violations.length ? ' · ihlal gözlendi' : ''}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </div>
        </header>
        <div className="mb-6 grid gap-5 border-y border-slate-300 py-5 xl:grid-cols-[1fr_1.3fr]">
          <div>
            <p className="eyebrow">Görev talimatı</p>
            <p className="mt-3 text-lg leading-7">{taskText}</p>
            <p className="mt-3 text-sm text-slate-600">
              Sentetik görev · Dondurulmuş JSONL kayıtları · Seed 0
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {pair.unguarded && (
              <RunSummary
                run={pair.unguarded}
                guarded={false}
                selected={agent === 'unguarded'}
                onSelect={() => selectAgent('unguarded')}
              />
            )}
            {pair.guarded && (
              <RunSummary
                run={pair.guarded}
                guarded
                selected={agent === 'guarded'}
                onSelect={() => selectAgent('guarded')}
              />
            )}
          </div>
        </div>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span
              className={`system-marker ${agent === 'unguarded' ? 'unguarded' : ''}`}
            />
            <h2 className="text-xl font-semibold">
              {agent === 'guarded' ? 'Guarded v2.1' : 'Unguarded v1'} karar
              zinciri
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              disabled={problemIndex < 0}
              onClick={() => {
                setActive(problemIndex);
                setPlaying(false);
              }}
            >
              İlk hata / müdahale
            </Button>
            <Button
              variant="outline"
              disabled={active === 0}
              onClick={() => {
                setActive(active - 1);
                setPlaying(false);
              }}
            >
              Önceki
            </Button>
            <Button
              variant="outline"
              disabled={active === trace.length - 1}
              onClick={() => {
                setActive(active + 1);
                setPlaying(false);
              }}
            >
              Sonraki <ArrowRight size={16} />
            </Button>
            <Button
              aria-label={
                playing && active < trace.length - 1 ? 'Duraklat' : 'Oynat'
              }
              onClick={() => {
                if (active === trace.length - 1) setActive(0);
                setPlaying(!playing || active === trace.length - 1);
              }}
            >
              {playing && active < trace.length - 1 ? (
                <Pause size={16} />
              ) : (
                <Play size={16} />
              )}
            </Button>
          </div>
        </div>
        <div className="mb-5">
          <div className="mb-2 flex justify-between text-sm">
            <span>Koşu ilerlemesi</span>
            <span aria-live="polite">
              Adım {active + 1} / {trace.length}
            </span>
          </div>
          <Progress
            value={((active + 1) / trace.length) * 100}
            aria-label="Karar izi ilerlemesi"
          />
        </div>
        {run.violations.length > 0 && (
          <div className="scope-note border-amber-300 bg-amber-50">
            <AlertTriangle size={17} />
            <p>
              <strong>Koşu düzeyinde gözlenen ihlal:</strong>{' '}
              {run.violations.map(labelViolation).join(', ')}. İhlal etiketi
              belirli bir adıma bağlı kaydedilmedi; aşağıdaki durumlar adımın
              kendi ortam yanıtını gösterir.
            </p>
          </div>
        )}
        <div className="trace-summary" aria-label="Seçili adımın karar akışı">
          {[
            ['01 / Gözlem', step.pageTitle ?? 'Kayıt yok'],
            [
              '02 / Model önerisi',
              step.rawModelOutput
                ? 'Ham çıktı mevcut'
                : 'Ham çıktı kaydedilmedi',
            ],
            ['03 / Guard kararı', step.guard?.decision ?? 'Guard yok'],
            ['04 / Yürütme eylemi', action?.tool ?? 'Eylem yok'],
            [
              '05 / Ortam sonucu',
              applied === true
                ? 'Uygulandı'
                : applied === false
                  ? 'Uygulanmadı'
                  : 'Kayıt yok',
            ],
          ].map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
        <div className="grid items-start gap-5 lg:grid-cols-[250px_1fr]">
          <aside
            className="rounded-lg border bg-white p-4"
            aria-label="Adım seçimi"
          >
            <h3 className="mb-3 font-semibold">Zaman çizgisi</h3>
            <div className="max-h-96 space-y-1 overflow-y-auto lg:max-h-[720px]">
              {trace.map((s, i) => {
                const state = stepStatus(s);
                const Icon = state.icon;
                return (
                  <button
                    key={i}
                    aria-current={i === active ? 'step' : undefined}
                    onClick={() => {
                      setActive(i);
                      setPlaying(false);
                    }}
                    className={`w-full rounded-md border p-3 text-left ${i === active ? 'border-slate-500 bg-slate-100' : 'border-transparent hover:bg-slate-50'}`}
                  >
                    <span className="flex items-center gap-2 text-sm font-semibold">
                      <span className="font-mono text-slate-500">
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      {toolNames[s.action?.tool ?? ''] ??
                        s.action?.tool ??
                        'Model denemesi'}
                    </span>
                    <span className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                      <Icon size={14} />
                      {state.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </aside>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-wrap items-center justify-between gap-3 md:col-span-2">
              <h3 className="text-xl font-semibold">
                Adım {active + 1}{' '}
                <span className="text-base font-normal text-slate-600">
                  / {step.route}
                </span>
              </h3>
              <Badge variant="outline" className={status.cls}>
                <StatusIcon size={14} />
                {status.label}
              </Badge>
            </div>
            <Card className="bg-white">
              <CardHeader>
                <p className="eyebrow">01 / Gözlem</p>
                <CardTitle>Ajan ne gördü?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="leading-7">{step.pageTitle}</p>
                <p className="mt-3 text-sm text-slate-600">
                  Kalan zorunlu alanlar:{' '}
                  <strong>
                    {step.remainingRequiredFields.join(', ') || 'Yok'}
                  </strong>
                </p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {step.candidateActions.map((v) => (
                    <Badge variant="secondary" key={v}>
                      {v}
                    </Badge>
                  ))}
                </div>
                <TechnicalDetails
                  title="Gözlem durumunu aç"
                  value={step.state}
                />
              </CardContent>
            </Card>
            <Card className="bg-white">
              <CardHeader>
                <p className="eyebrow">02 / Model önerisi</p>
                <CardTitle>Ham model çıktısı</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="leading-7 text-slate-600">
                  {step.rawModelOutput
                    ? 'Model çıktısını yürütme eylemiyle karşılaştırın. Kontrolcü çıktıyı dönüştürmüş olabilir.'
                    : 'Bu adımda ham model çıktısı kaydedilmedi. Kayıtlı yürütme eylemi aşağıdadır.'}
                </p>
                {step.parseError && (
                  <p className="mt-3 text-sm text-red-800">
                    Ayrıştırma hatası: {step.parseError}
                  </p>
                )}
                {step.rawModelOutput && (
                  <TechnicalDetails
                    title="Ham öneriyi aç"
                    value={step.rawModelOutput}
                  />
                )}
              </CardContent>
            </Card>
            <Card className="border-slate-700 bg-slate-950 text-white md:col-span-2">
              <CardHeader>
                <p className="eyebrow text-emerald-300">03 / Guard kararı</p>
                <CardTitle>
                  {step.guard?.decision ?? 'Guard kullanılmadı'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="leading-7 text-slate-300">
                  {step.guard?.explanation ??
                    'Korumasız koşu: eylem bir guard kararından geçirilmedi.'}
                </p>
                {step.guard?.risk_labels && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {step.guard.risk_labels.map((v) => (
                      <Badge key={v} className="bg-slate-700 text-white">
                        {v}
                      </Badge>
                    ))}
                  </div>
                )}
                {step.guard && (
                  <TechnicalDetails
                    title="Guard kanıtlarını ve teknik ayrıntıları aç"
                    value={step.guard}
                  />
                )}
              </CardContent>
            </Card>
            <Card className="bg-white">
              <CardHeader>
                <p className="eyebrow">04 / Yürütme eylemi</p>
                <CardTitle>
                  {toolNames[action?.tool ?? ''] ?? action?.tool ?? 'Eylem yok'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-sm">
                  Hedef: {action?.target_id || '—'}
                </p>
                <p className="mt-3 leading-7 text-slate-600">
                  {action?.reason ?? 'Eylem gerekçesi kaydedilmedi.'}
                </p>
                <TechnicalDetails
                  title="Yapılandırılmış eylemi aç"
                  value={action}
                />
              </CardContent>
            </Card>
            <Card className="bg-white">
              <CardHeader>
                <p className="eyebrow">05 / Ortam sonucu</p>
                <CardTitle>
                  {applied === true
                    ? 'Eylem uygulandı'
                    : applied === false
                      ? 'Eylem uygulanmadı'
                      : 'Uygulama kaydı yok'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="leading-7 text-slate-600">
                  {step.environmentResult?.error ??
                    'Ortam yanıtı ve sonraki durum teknik kayıtta görülebilir.'}
                </p>
                <p className="mt-3 text-sm">
                  HTTP durumu: {step.environmentStatus ?? '—'}
                </p>
                <TechnicalDetails
                  title="Ortam yanıtını ve sonraki durumu aç"
                  value={step.environmentResult}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </main>
  );
}
