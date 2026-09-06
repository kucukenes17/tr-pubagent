'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, Database, FlaskConical, Gauge, ShieldAlert, ShieldCheck, Timer, Zap } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { SiteHeader } from '@/components/site-header';
import type { FrozenDashboardData, ResultMetrics } from '@/lib/research-data';

const percent = (value: number) => `%${(value * 100).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`;
const compact = (value: number) => value.toLocaleString('tr-TR', { maximumFractionDigits: 1 });

function useDashboardData() {
  const [data, setData] = useState<FrozenDashboardData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    fetch('/data/frozen-dashboard.json').then((response) => {
      if (!response.ok) throw new Error('Sonuç dosyası yüklenemedi.');
      return response.json() as Promise<FrozenDashboardData>;
    }).then(setData).catch(() => setError(true));
  }, []);
  return { data, error };
}

function MetricCard({ label, value, detail, icon: Icon }: { label: string; value: string; detail: string; icon: typeof Database }) {
  return <div className="bg-white p-5"><div className="flex items-center justify-between"><span className="mono-label text-slate-500">{label}</span><Icon className="size-4 text-blue-600" /></div><div className="mt-2 flex items-end justify-between gap-4"><strong className="text-3xl tracking-tight text-slate-950">{value}</strong><span className="max-w-32 text-right text-xs leading-5 text-slate-500">{detail}</span></div></div>;
}

function RunRow({ name, run, guarded }: { name: string; run: ResultMetrics; guarded?: boolean }) {
  return <div className="grid grid-cols-[1.35fr_.7fr_.55fr_.55fr] items-center border-b border-white/10 px-5 py-4 last:border-0"><div className="flex items-center gap-2">{guarded ? <ShieldCheck className="size-4 text-cyan-300" /> : <FlaskConical className="size-4 text-slate-500" />}<span className="font-medium">{name}</span></div><span className="font-mono text-lg">{percent(run.success_rate)}</span><span className={guarded ? 'font-mono text-lg text-cyan-300' : 'font-mono text-lg'}>{run.violation_count}</span><span className="font-mono text-lg">{compact(run.mean_steps)}</span></div>;
}

export function LabDashboard() {
  const { data, error } = useDashboardData();
  const splitChart = useMemo(() => data ? [
    { split: 'Geliştirme', Unguarded: data.summary.development.unguarded_v1.success_rate * 100, 'Guarded v2.1': data.summary.development.guarded_v2_1.success_rate * 100 },
    { split: 'Doğrulama', Unguarded: data.summary.validation.unguarded_v1.success_rate * 100, 'Guarded v2.1': data.summary.validation.guarded_v2_1.success_rate * 100 },
    { split: 'Final test', Unguarded: data.summary.test.unguarded_v1.success_rate * 100, 'Guarded v2.1': data.summary.test.guarded_v2_1.success_rate * 100 },
  ] : [], [data]);
  const outcomeChart = useMemo(() => data ? [
    { metric: 'Başarılı görev', Unguarded: data.summary.test.unguarded_v1.successes, 'Guarded v2.1': data.summary.test.guarded_v2_1.successes },
    { metric: 'Geçersiz eylem', Unguarded: data.summary.test.unguarded_v1.invalid_actions, 'Guarded v2.1': data.summary.test.guarded_v2_1.invalid_actions },
    { metric: 'İhlal', Unguarded: data.summary.test.unguarded_v1.violation_count, 'Guarded v2.1': data.summary.test.guarded_v2_1.violation_count },
  ] : [], [data]);
  const robustnessChart = useMemo(() => data ? [
    { system: 'Unguarded v1', success: data.robustness.summary.unguarded.success_rate * 100 },
    { system: 'Guarded v2.1', success: data.robustness.summary.guarded_v2_1.success_rate * 100 },
  ] : [], [data]);

  if (error) return <main className="min-h-screen"><SiteHeader /><section className="mx-auto max-w-3xl px-5 py-20"><Card className="border-red-200 bg-red-50"><CardContent className="flex gap-3 p-6"><AlertTriangle className="size-5 text-red-700" /><div><h1 className="font-semibold text-red-950">Dondurulmuş sonuçlar yüklenemedi</h1><p className="mt-1 text-sm text-red-800">Dashboard veri paketi yeniden üretilmelidir.</p></div></CardContent></Card></section></main>;
  if (!data) return <main className="min-h-screen"><SiteHeader /><section className="mx-auto max-w-[1440px] space-y-6 px-5 py-10"><Skeleton className="h-44 w-full" /><div className="grid gap-5 md:grid-cols-2"><Skeleton className="h-80" /><Skeleton className="h-80" /></div></section></main>;

  const test = data.summary.test;
  const robustness = data.robustness.summary;
  const tokenReduction = 1 - (test.guarded_v2_1.generated_tokens / test.unguarded_v1.generated_tokens);
  const latencyReduction = 1 - (test.guarded_v2_1.latency_seconds / test.unguarded_v1.latency_seconds);
  const oodTokenReduction = 1 - (robustness.guarded_v2_1.generated_tokens / robustness.unguarded.generated_tokens);
  const oodLatencyReduction = 1 - (robustness.guarded_v2_1.latency_seconds / robustness.unguarded.latency_seconds);

  return <main className="min-h-screen"><SiteHeader /><section className="mx-auto max-w-[1440px] px-5 py-7 lg:px-8 lg:py-10">
    <div className="mb-8 grid gap-6 border-b border-slate-200 pb-8 lg:grid-cols-[1.2fr_.8fr] lg:items-end"><div><div className="mb-4 flex flex-wrap items-center gap-2"><Badge className="bg-blue-600 text-white">Canlı araştırma dashboard’u</Badge><Badge variant="outline">40 eşlenmiş test görevi</Badge><Badge variant="outline">Seed 0</Badge></div><h1 className="max-w-4xl text-4xl font-semibold leading-[1.05] tracking-[-0.045em] text-slate-950 md:text-6xl">Güvenlik katmanı, başarıyı <span className="text-blue-600">ölçülebilir biçimde değiştiriyor.</span></h1></div><div className="lg:pb-1"><p className="max-w-xl text-base leading-7 text-slate-600">Tüm metrikler doğrudan dondurulmuş Phi-4 JSONL kayıtlarından üretilir. Bir görevi seçip her iki ajanın gerçek karar zincirini karşılaştırabilirsiniz.</p><div className="mt-5 flex flex-wrap gap-3"><Link className={buttonVariants({ className: 'bg-slate-950 text-white hover:bg-blue-700' })} href="/replays">Gerçek koşuları incele <ArrowRight className="size-4" /></Link><Link className={buttonVariants({ variant: 'outline' })} href="/method">Yöntemi oku</Link></div></div></div>

    <div className="mb-7 grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:grid-cols-2 xl:grid-cols-4"><MetricCard label="Final başarı farkı" value="+100 pp" detail={`${test.unguarded_v1.successes}/40 → ${test.guarded_v2_1.successes}/40`} icon={CheckCircle2} /><MetricCard label="Gözlenen ihlal" value={`${test.unguarded_v1.violation_count} → ${test.guarded_v2_1.violation_count}`} detail="4 gizlilik + 6 dil yorumlama" icon={ShieldAlert} /><MetricCard label="Token azalması" value={percent(tokenReduction)} detail={`${compact(test.unguarded_v1.generated_tokens)} → ${compact(test.guarded_v2_1.generated_tokens)}`} icon={Zap} /><MetricCard label="Gecikme azalması" value={percent(latencyReduction)} detail={`${compact(test.unguarded_v1.latency_seconds)} sn → ${compact(test.guarded_v2_1.latency_seconds)} sn`} icon={Timer} /></div>

    <Card className="mb-7 overflow-hidden border-blue-900 bg-slate-950 text-white shadow-xl shadow-blue-950/10">
      <CardHeader className="border-b border-white/10"><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="mb-2 flex flex-wrap gap-2"><Badge className="bg-cyan-300 text-slate-950">OOD sağlamlık</Badge><Badge variant="outline" className="border-white/20 text-slate-300">24 görev × 3 seed</Badge></div><CardTitle className="text-3xl">Görülmemiş görevlerde %91,7 başarı</CardTitle><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">İnsan yazımı 24 yeni görev, algoritma dondurulduktan sonra üç seed ile çalıştırıldı. Guarded sistem 72 koşunun 66’sını tamamladı; geçersiz eylem ve gözlenen ihlal üretmedi.</p></div><div className="rounded-xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-3 text-right"><div className="mono-label text-cyan-200">Exact McNemar</div><strong className="font-mono text-lg text-white">p={robustness.mcnemar_exact_p.toExponential(2)}</strong></div></div></CardHeader>
      <CardContent className="grid gap-6 p-5 lg:grid-cols-[.85fr_1.15fr] lg:p-7">
        <div className="h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={robustnessChart} margin={{ top: 12, right: 12, left: -12, bottom: 0 }}><CartesianGrid stroke="#334155" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="system" stroke="#94a3b8" tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} unit="%" stroke="#94a3b8" tickLine={false} axisLine={false} /><Tooltip formatter={(value) => [`%${Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`, 'Başarı']} /><Bar dataKey="success" fill="#22d3ee" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></div>
        <div className="grid content-start gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-white/5 p-4"><Gauge className="mb-3 size-5 text-cyan-300" /><div className="mono-label text-slate-400">Başarı artışı</div><strong className="mt-1 block text-2xl">+{compact(robustness.absolute_success_gain * 100)} pp</strong><p className="mt-2 text-sm leading-6 text-slate-400">Görev-kümeli %95 GA: +{compact(robustness.task_cluster_bootstrap_ci95[0] * 100)}–+{compact(robustness.task_cluster_bootstrap_ci95[1] * 100)} pp</p></div>
          <div className="rounded-xl border border-white/10 bg-white/5 p-4"><ShieldCheck className="mb-3 size-5 text-cyan-300" /><div className="mono-label text-slate-400">Hata baskılama</div><strong className="mt-1 block text-2xl">45 → 0</strong><p className="mt-2 text-sm leading-6 text-slate-400">Geçersiz eylemler; gözlenen ihlaller ayrıca 12’den 0’a indi.</p></div>
          <div className="rounded-xl border border-white/10 bg-white/5 p-4"><Zap className="mb-3 size-5 text-cyan-300" /><div className="mono-label text-slate-400">Token azalması</div><strong className="mt-1 block text-2xl">{percent(oodTokenReduction)}</strong><p className="mt-2 text-sm leading-6 text-slate-400">{compact(robustness.unguarded.generated_tokens)} → {compact(robustness.guarded_v2_1.generated_tokens)} token</p></div>
          <div className="rounded-xl border border-white/10 bg-white/5 p-4"><Timer className="mb-3 size-5 text-cyan-300" /><div className="mono-label text-slate-400">Gecikme azalması</div><strong className="mt-1 block text-2xl">{percent(oodLatencyReduction)}</strong><p className="mt-2 text-sm leading-6 text-slate-400">{compact(robustness.unguarded.latency_seconds)} → {compact(robustness.guarded_v2_1.latency_seconds)} saniye</p></div>
          <div className="rounded-xl border border-amber-300/20 bg-amber-300/10 p-4 sm:col-span-2"><div className="flex gap-3"><AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-300" /><div><div className="font-semibold text-amber-100">İki sistematik sınır bulundu</div><p className="mt-1 text-sm leading-6 text-amber-50/70">Belge türü görevinde “18.000 TL” kanıtı çıkarılamadı; randevu görevinde “salı değil, perşembe” ifadesi doğrudan seçime bağlanamadı. Her iki hata üç seed’de de tekrarlandı. Dondurulmuş v2.1 sonucu korunuyor; düzeltmeler ayrı v2.2 çalışması olarak değerlendirilecek.</p></div></div></div>
        </div>
      </CardContent>
    </Card>

    <div className="grid gap-7 xl:grid-cols-[1.05fr_.95fr]">
      <Card className="border-slate-200 bg-white shadow-sm"><CardHeader><p className="mono-label text-blue-700">Split tutarlılığı</p><CardTitle className="text-2xl">Görev başarı oranı</CardTitle><p className="text-sm text-slate-500">Geliştirme, doğrulama ve daha önce görülmemiş final test görevleri.</p></CardHeader><CardContent className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={splitChart} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="split" tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} unit="%" tickLine={false} axisLine={false} /><Tooltip formatter={(value) => [`%${String(value)}`, 'Başarı']} /><Legend /><Bar dataKey="Unguarded" fill="#94a3b8" radius={[5, 5, 0, 0]} /><Bar dataKey="Guarded v2.1" fill="#2563eb" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></CardContent></Card>
      <Card className="border-slate-200 bg-white shadow-sm"><CardHeader><p className="mono-label text-blue-700">Final test · n=40</p><CardTitle className="text-2xl">Sonuç türleri</CardTitle><p className="text-sm text-slate-500">Başarı artarken geçersiz eylem ve ihlal sayısı sıfıra indi.</p></CardHeader><CardContent className="h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={outcomeChart} layout="vertical" margin={{ top: 10, right: 10, left: 18, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" tickLine={false} axisLine={false} /><YAxis type="category" dataKey="metric" width={105} tickLine={false} axisLine={false} /><Tooltip /><Legend /><Bar dataKey="Unguarded" fill="#94a3b8" radius={[0, 5, 5, 0]} /><Bar dataKey="Guarded v2.1" fill="#0891b2" radius={[0, 5, 5, 0]} /></BarChart></ResponsiveContainer></CardContent></Card>
      <Card className="overflow-hidden border-slate-800 bg-slate-950 text-white shadow-xl shadow-blue-950/10 xl:col-span-2"><CardHeader className="border-b border-white/10"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="mono-label text-cyan-300">Dondurulmuş karşılaştırma</p><CardTitle className="mt-1 text-2xl">Başarı / güvenlik / verimlilik</CardTitle></div><Badge variant="outline" className="border-cyan-300/30 text-cyan-200">McNemar p={test.mcnemar_exact_p.toExponential(2)}</Badge></div></CardHeader><CardContent className="p-0"><div className="grid grid-cols-[1.35fr_.7fr_.55fr_.55fr] border-b border-white/10 px-5 py-3 text-xs font-medium text-slate-400"><span>Yöntem</span><span>Başarı</span><span>İhlal</span><span>Adım</span></div><RunRow name="TR-PubGuard v2.1" run={test.guarded_v2_1} guarded /><RunRow name="Unguarded v1" run={test.unguarded_v1} /><div className="m-5 grid gap-4 rounded-xl border border-white/10 bg-white/5 p-4 text-sm leading-6 text-slate-300 md:grid-cols-[1fr_auto]"><p><strong className="text-white">Araştırma sınırı:</strong> Sonuçlar tek model, tek seed ve sentetik Türkçe kamu hizmeti görevlerini kapsar; gerçek sistemlere doğrudan genellenemez.</p><div className="flex items-center gap-2 font-mono text-xs text-cyan-200"><Database className="size-4" /> harness={String(data.summary.provenance.evaluation_harness)}</div></div></CardContent></Card>
    </div>
  </section></main>;
}
