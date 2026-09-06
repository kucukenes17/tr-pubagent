'use client';

import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, CircleHelp, Pause, Play, ShieldCheck, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { SiteHeader } from '@/components/site-header';
import type { FrozenDashboardData, FrozenRun, FrozenTraceStep } from '@/lib/research-data';

type AgentKey = 'unguarded' | 'guarded';

const toolNames: Record<string, string> = { fill: 'Alanı doldur', select: 'Seçim yap', ask_user: 'Kullanıcıya sor', request_confirmation: 'Onay iste', submit: 'Gönder', finish: 'Bitir', upload_fixture: 'Dosya yükle' };
const labelViolation = (value: string) => value === 'PRIVACY_VIOLATION' ? 'Gizlilik ihlali' : value === 'LANGUAGE_INTERPRETATION_ERROR' ? 'Dil yorumlama hatası' : value;

function stepStatus(step: FrozenTraceStep) {
  if (step.guard?.decision === 'BLOCK') return { label: 'Guard engelledi', icon: AlertTriangle, cls: 'border-amber-200 bg-amber-50 text-amber-900' };
  if (step.environmentResult?.applied === false) return { label: 'Eylem uygulanmadı', icon: XCircle, cls: 'border-red-200 bg-red-50 text-red-800' };
  if (step.action?.tool === 'ask_user' || step.action?.tool === 'request_confirmation') return { label: 'Bilgi / onay istedi', icon: CircleHelp, cls: 'border-blue-200 bg-blue-50 text-blue-800' };
  if (step.action?.tool === 'finish') return { label: 'Tamamlandı', icon: ShieldCheck, cls: 'border-cyan-200 bg-cyan-50 text-cyan-900' };
  return { label: 'Uygulandı', icon: CheckCircle2, cls: 'border-emerald-200 bg-emerald-50 text-emerald-800' };
}

function RunSummary({ run, guarded, selected, onSelect }: { run: FrozenRun; guarded: boolean; selected: boolean; onSelect: () => void }) {
  const name = guarded ? 'Guarded v2.1' : 'Unguarded v1';
  return <button type="button" aria-label={`${name} koşusunu göster`} onClick={onSelect} className={`w-full rounded-xl border p-4 text-left ${selected ? 'border-blue-400 bg-blue-50 ring-2 ring-blue-100' : 'border-slate-200 bg-white'}`}><div className="mb-3 flex items-center justify-between"><span className="font-semibold text-slate-950">{name}</span><Badge className={run.taskSuccess ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'}>{run.taskSuccess ? 'Başarılı' : 'Başarısız'}</Badge></div><div className="grid grid-cols-3 gap-3 text-sm"><div><span className="block text-xs text-slate-500">Sonlanma</span><strong className="mt-1 block font-mono text-xs">{run.termination}</strong></div><div><span className="block text-xs text-slate-500">Adım</span><strong className="mt-1 block">{run.steps}</strong></div><div><span className="block text-xs text-slate-500">İhlal</span><strong className="mt-1 block">{run.violations.length}</strong></div></div></button>;
}

export function ReplayExplorer() {
  const [data, setData] = useState<FrozenDashboardData | null>(null);
  const [failed, setFailed] = useState(false);
  const [taskId, setTaskId] = useState('');
  const [agent, setAgent] = useState<AgentKey>('unguarded');
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => { fetch('/data/frozen-dashboard.json').then((r) => { if (!r.ok) throw new Error(); return r.json() as Promise<FrozenDashboardData>; }).then((payload) => { setData(payload); const illustrative = payload.pairedRuns.find((pair) => (pair.unguarded?.violations.length ?? 0) > 0 && (pair.guarded?.guardBlocks ?? 0) > 0) ?? payload.pairedRuns.find((pair) => (pair.unguarded?.violations.length ?? 0) > 0) ?? payload.pairedRuns[0]; setTaskId(illustrative?.taskId ?? ''); }).catch(() => setFailed(true)); }, []);
  const pair = useMemo(() => data?.pairedRuns.find((item) => item.taskId === taskId) ?? null, [data, taskId]);
  const run = pair?.[agent] ?? null;
  const trace = run?.trace ?? [];
  const step = trace[Math.min(active, Math.max(0, trace.length - 1))];

  useEffect(() => { if (!playing || trace.length < 2) return; const timer = window.setInterval(() => setActive((current) => { if (current >= trace.length - 1) { setPlaying(false); return current; } return current + 1; }), 1500); return () => window.clearInterval(timer); }, [playing, trace.length]);

  if (failed) return <main className="min-h-screen"><SiteHeader /><section className="mx-auto max-w-3xl px-5 py-20"><Card className="border-red-200 bg-red-50"><CardContent className="p-6 text-red-900">Dondurulmuş replay verisi yüklenemedi.</CardContent></Card></section></main>;
  if (!data || !pair || !run || !step) return <main className="min-h-screen"><SiteHeader /><section className="mx-auto max-w-[1400px] space-y-5 px-5 py-8"><Skeleton className="h-36" /><Skeleton className="h-[520px]" /></section></main>;

  const status = stepStatus(step); const StatusIcon = status.icon;
  const taskText = step.task ?? pair.guarded?.trace[0]?.task ?? pair.unguarded?.trace[0]?.task ?? '';
  const action = step.action;

  return <main className="min-h-screen"><SiteHeader /><section className="mx-auto max-w-[1450px] px-5 py-8 lg:px-8">
    <div className="mb-7 grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end"><div><p className="mono-label text-blue-700">Dondurulmuş final test · gerçek JSONL izi</p><h1 className="mt-1 text-4xl font-semibold tracking-tight text-slate-950">Karar zinciri karşılaştırması</h1><p className="mt-2 max-w-3xl leading-7 text-slate-600">Aynı görevin korumasız ve korumalı koşularını seçin; model çıktısını, eylemi, ortam yanıtını ve Guard kararını adım adım inceleyin.</p></div><div><label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="task-select">Final test görevi</label><NativeSelect className="w-full min-w-60" id="task-select" value={taskId} onChange={(event) => { setTaskId(event.target.value); setActive(0); setPlaying(false); }}>{data.pairedRuns.map((item) => <NativeSelectOption value={item.taskId} key={item.taskId}>{item.taskId}</NativeSelectOption>)}</NativeSelect></div></div>

    <Card className="mb-6 border-slate-200 bg-white"><CardContent className="p-5"><div className="grid gap-5 xl:grid-cols-[1fr_460px]"><div><span className="mono-label text-slate-500">Görev talimatı</span><p className="mt-2 text-lg font-medium leading-7 text-slate-950">{taskText}</p></div><div className="grid grid-cols-2 gap-3"><RunSummary run={pair.unguarded!} guarded={false} selected={agent === 'unguarded'} onSelect={() => { setAgent('unguarded'); setActive(0); setPlaying(false); }} /><RunSummary run={pair.guarded!} guarded selected={agent === 'guarded'} onSelect={() => { setAgent('guarded'); setActive(0); setPlaying(false); }} /></div></div></CardContent></Card>

    <div className="mb-6 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 md:grid-cols-[auto_1fr_auto] md:items-center"><div className="flex rounded-xl bg-slate-100 p-1"><Button size="sm" variant={agent === 'unguarded' ? 'default' : 'ghost'} onClick={() => { setAgent('unguarded'); setActive(0); setPlaying(false); }}>Unguarded</Button><Button size="sm" variant={agent === 'guarded' ? 'default' : 'ghost'} onClick={() => { setAgent('guarded'); setActive(0); setPlaying(false); }}>Guarded v2.1</Button></div><div><div className="mb-2 flex justify-between text-sm"><span className="font-medium">Koşu ilerlemesi</span><span className="font-mono text-slate-500">{active + 1} / {trace.length}</span></div><Progress value={((active + 1) / trace.length) * 100} /></div><div className="flex gap-2"><Button variant="outline" disabled={active === 0} onClick={() => setActive((v) => v - 1)}>Önceki</Button><Button variant="outline" disabled={active === trace.length - 1} onClick={() => setActive((v) => v + 1)}>Sonraki <ArrowRight className="size-4" /></Button><Button aria-label={playing ? 'Duraklat' : 'Oynat'} onClick={() => setPlaying((v) => !v)} className="bg-slate-950 text-white">{playing ? <Pause className="size-4" /> : <Play className="size-4" />}</Button></div></div>

    <div className="grid gap-6 lg:grid-cols-[300px_1fr]"><Card className="h-fit border-slate-200 bg-white"><CardHeader><CardTitle className="text-lg">Zaman çizgisi</CardTitle></CardHeader><CardContent className="space-y-2">{trace.map((item, index) => { const itemStatus = stepStatus(item); return <button key={`${item.step}-${index}`} onClick={() => { setActive(index); setPlaying(false); }} className={`w-full rounded-xl border p-3 text-left transition-colors ${index === active ? 'border-blue-300 bg-blue-50' : 'border-transparent hover:bg-slate-50'}`}><span className="flex items-center gap-2 text-sm font-semibold"><span className={`grid size-6 shrink-0 place-items-center rounded-full text-xs ${index === active ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-500'}`}>{index + 1}</span><span className="truncate">{toolNames[item.action?.tool ?? ''] ?? item.action?.tool ?? 'Model denemesi'}</span></span><span className="mt-1 block pl-8 text-xs text-slate-500">{itemStatus.label}</span></button>; })}</CardContent></Card>

      <div className="grid gap-5 md:grid-cols-2"><Card className="border-slate-200 bg-white md:col-span-2"><CardHeader className="flex-row items-start justify-between"><div><p className="mono-label text-slate-500">Adım {active + 1} · {step.route}</p><CardTitle className="mt-1 text-2xl">{toolNames[action?.tool ?? ''] ?? action?.tool ?? 'Ayrıştırılamayan çıktı'}</CardTitle></div><Badge variant="outline" className={status.cls}><StatusIcon className="size-3.5" />{status.label}</Badge></CardHeader></Card>
        <Card className="border-slate-200 bg-white"><CardHeader><p className="mono-label text-blue-700">01 · Gözlem</p><CardTitle className="text-lg">Ajan ne gördü?</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><div><span className="text-slate-500">Sayfa</span><p className="mt-1 font-medium">{step.pageTitle}</p></div><div><span className="text-slate-500">Kalan zorunlu alanlar</span><p className="mt-1 font-mono">{step.remainingRequiredFields.join(', ') || 'Yok'}</p></div><div><span className="text-slate-500">Aday eylemler</span><div className="mt-2 flex flex-wrap gap-1">{step.candidateActions.map((item) => <Badge variant="secondary" key={item}>{item}</Badge>)}</div></div></CardContent></Card>
        <Card className="border-slate-200 bg-white"><CardHeader><p className="mono-label text-blue-700">02 · Eylem</p><CardTitle className="text-lg">Model ne önerdi?</CardTitle></CardHeader><CardContent><code className="block max-h-56 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-4 text-sm leading-6 text-cyan-200">{action ? JSON.stringify(action, null, 2) : step.rawModelOutput ?? 'Eylem yok'}</code>{action?.reason && <p className="mt-3 text-sm leading-6 text-slate-600">{action.reason}</p>}</CardContent></Card>
        <Card className="border-slate-800 bg-slate-950 text-white md:col-span-2"><CardHeader><p className="mono-label text-cyan-300">03 · Güvenlik ve ortam kararı</p><CardTitle className="text-xl">{step.guard ? `${step.guard.decision} · ${(step.guard.risk_labels ?? []).join(', ')}` : 'Guard kullanılmadı'}</CardTitle></CardHeader><CardContent className="grid gap-4 md:grid-cols-[1fr_auto]"><div><p className="leading-7 text-slate-300">{step.guard?.explanation ?? step.environmentResult?.error ?? (step.environmentResult?.applied ? 'Eylem ortam tarafından uygulandı.' : 'Eylem ortam tarafından uygulanmadı.')}</p>{run.violations.length > 0 && <div className="mt-4 flex flex-wrap gap-2">{run.violations.map((v) => <Badge key={v} className="bg-red-500/20 text-red-200">{labelViolation(v)}</Badge>)}</div>}</div><div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 font-mono text-xs text-slate-300"><div>applied={String(step.environmentResult?.applied ?? false)}</div><div>status={step.environmentStatus ?? '—'}</div><div>guard_blocks={run.guardBlocks}</div></div></CardContent></Card>
      </div></div>
  </section></main>;
}
