'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, CircleHelp, Pause, Play, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { SiteHeader } from '@/components/site-header';
import { replaySteps } from '@/lib/research-data';

const statusMeta = {
  allowed: { label: 'İzin verildi', icon: CheckCircle2, className: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
  blocked: { label: 'Engellendi', icon: AlertTriangle, className: 'bg-amber-50 text-amber-900 border-amber-200' },
  asked: { label: 'Açıklama istedi', icon: CircleHelp, className: 'bg-blue-50 text-blue-800 border-blue-200' },
  complete: { label: 'Tamamlandı', icon: ShieldCheck, className: 'bg-cyan-50 text-cyan-900 border-cyan-200' },
} as const;

export function ReplayExplorer() {
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);
  const step = replaySteps[active];
  const meta = statusMeta[step.status];
  const StatusIcon = meta.icon;

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setActive((current) => {
      if (current >= replaySteps.length - 1) { setPlaying(false); return current; }
      return current + 1;
    }), 1700);
    return () => window.clearInterval(timer);
  }, [playing]);

  return (
    <main className="min-h-screen">
      <SiteHeader />
      <section className="mx-auto max-w-[1400px] px-5 py-8 lg:px-8">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-5">
          <div><p className="mono-label text-blue-700">BUR-01 · tr-pubguard · seed 0</p><h1 className="mt-1 text-4xl font-semibold tracking-tight text-slate-950">Ajan koşusu tekrar oynatma</h1><p className="mt-2 max-w-2xl leading-7 text-slate-600">Ajanın gördüğü durumu, önerdiği eylemi ve güvenlik katmanının kararını aynı zaman çizgisinde inceleyin.</p></div>
          <Button onClick={() => setPlaying((value) => !value)} className="min-w-36 bg-slate-950 text-white">{playing ? <Pause className="size-4" /> : <Play className="size-4" />}{playing ? 'Duraklat' : 'Baştan oynat'}</Button>
        </div>

        <Card className="mb-6 border-slate-200 bg-white">
          <CardContent className="grid gap-5 p-5 md:grid-cols-[1fr_auto] md:items-center">
            <div><div className="mb-2 flex justify-between text-sm"><span className="font-medium">Koşu ilerlemesi</span><span className="font-mono text-slate-500">{active + 1} / {replaySteps.length}</span></div><Progress value={((active + 1) / replaySteps.length) * 100} /></div>
            <div className="flex gap-2"><Button variant="outline" disabled={active === 0} onClick={() => setActive((value) => value - 1)}>Önceki</Button><Button variant="outline" disabled={active === replaySteps.length - 1} onClick={() => setActive((value) => value + 1)}>Sonraki <ArrowRight className="size-4" /></Button></div>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <Card className="border-slate-200 bg-white"><CardHeader><CardTitle className="text-lg">Zaman çizgisi</CardTitle></CardHeader><CardContent className="space-y-2">{replaySteps.map((item, index) => <button key={item.id} onClick={() => { setActive(index); setPlaying(false); }} className={`w-full rounded-xl border p-3 text-left transition-colors ${index === active ? 'border-blue-300 bg-blue-50' : 'border-transparent hover:bg-slate-50'}`}><span className="mb-1 flex items-center gap-2 text-sm font-semibold"><span className={`grid size-6 place-items-center rounded-full text-xs ${index === active ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-500'}`}>{item.id}</span>{item.title}</span><span className="block pl-8 text-xs text-slate-500">{item.status === 'blocked' ? 'Risk kararı' : 'Ajan adımı'}</span></button>)}</CardContent></Card>

          <div className="grid gap-5 md:grid-cols-2">
            <Card className="border-slate-200 bg-white md:col-span-2"><CardHeader className="flex-row items-start justify-between"><div><p className="mono-label text-slate-500">Adım {step.id}</p><CardTitle className="mt-1 text-2xl">{step.title}</CardTitle></div><Badge variant="outline" className={meta.className}><StatusIcon className="size-3.5" />{meta.label}</Badge></CardHeader></Card>
            <Card className="border-slate-200 bg-white"><CardHeader><p className="mono-label text-blue-700">01 · Gözlem</p><CardTitle className="text-lg">Ajan ne gördü?</CardTitle></CardHeader><CardContent><p className="leading-7 text-slate-600">{step.observation}</p></CardContent></Card>
            <Card className="border-slate-200 bg-white"><CardHeader><p className="mono-label text-blue-700">02 · Eylem</p><CardTitle className="text-lg">Ajan ne önerdi?</CardTitle></CardHeader><CardContent><code className="block overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm leading-6 text-cyan-200">{step.action}</code></CardContent></Card>
            <Card className="border-slate-800 bg-slate-950 text-white md:col-span-2"><CardHeader><p className="mono-label text-cyan-300">03 · Guard kararı</p><CardTitle className="text-xl">{step.risk ?? 'SAFE'}</CardTitle></CardHeader><CardContent><p className="leading-7 text-slate-300">{step.guard}</p>{step.risk && <div className="mt-4 rounded-xl border border-amber-300/20 bg-amber-300/10 px-4 py-3 font-mono text-xs text-amber-200">decision=BLOCK · confidence=0.91 · evidence=user_request</div>}</CardContent></Card>
          </div>
        </div>
      </section>
    </main>
  );
}
