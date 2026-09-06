import Link from 'next/link';
import { ArrowRight, CheckCircle2, Database, FlaskConical, ShieldAlert, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { SiteHeader } from '@/components/site-header';
import { leaderboard, metrics, services } from '@/lib/research-data';

export function LabDashboard() {
  return (
    <main className="min-h-screen">
      <SiteHeader />
      <section className="mx-auto max-w-[1440px] px-5 py-7 lg:px-8 lg:py-10">
        <div className="mb-8 grid gap-6 border-b border-slate-200 pb-8 lg:grid-cols-[1.25fr_.75fr] lg:items-end">
          <div>
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <Badge className="bg-blue-600 text-white">Türkçe web ajanı benchmarkı</Badge>
              <Badge variant="outline">Sentetik veri</Badge>
              <Badge variant="outline">Dondurulmuş final test</Badge>
            </div>
            <h1 className="max-w-4xl text-4xl font-semibold leading-[1.05] tracking-[-0.045em] text-slate-950 md:text-6xl">
              Ajanın işi bitirmesi yetmez. <span className="text-blue-600">Yetkisini aşmaması gerekir.</span>
            </h1>
          </div>
          <div className="lg:pb-1">
            <p className="max-w-xl text-base leading-7 text-slate-600">Kamu hizmeti benzeri Türkçe görevlerde görev başarısını, eksik bilgiyle ilerlemeyi ve geri döndürülemez işlem güvenliğini aynı deneyde ölçer.</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link className={buttonVariants({ className: 'bg-slate-950 text-white hover:bg-blue-700' })} href="/replays">Örnek koşuyu incele <ArrowRight className="size-4" /></Link>
              <Link className={buttonVariants({ variant: 'outline' })} href="/portal">Portal görevini aç</Link>
            </div>
          </div>
        </div>

        <div className="mb-7 grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <div className="bg-white p-5" key={metric.label}>
              <span className="mono-label text-slate-500">{metric.label}</span>
              <div className="mt-2 flex items-end justify-between gap-4"><strong className="text-3xl tracking-tight text-slate-950">{metric.value}</strong><span className="text-right text-xs text-slate-500">{metric.detail}</span></div>
            </div>
          ))}
        </div>

        <div className="grid gap-7 xl:grid-cols-[1.1fr_.9fr]">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="flex-row items-center justify-between border-b border-slate-100">
              <div><p className="mono-label text-blue-700">Deney yüzeyi</p><CardTitle className="mt-1 text-2xl">Hizmet ve görev dağılımı</CardTitle></div>
              <Database className="size-6 text-slate-400" aria-hidden="true" />
            </CardHeader>
            <CardContent className="p-0">
              {services.map((service, index) => (
                <div className="grid grid-cols-[56px_1fr_auto] items-center gap-4 border-b border-slate-100 px-5 py-4 last:border-0" key={service.code}>
                  <span className="font-mono text-xs font-bold text-blue-700">{service.code}-{String(index + 1).padStart(2, '0')}</span>
                  <div><div className="mb-2 flex items-center justify-between gap-3"><span className="font-medium text-slate-900">{service.name}</span><span className="text-xs text-slate-500">{service.tasks} görev</span></div><Progress value={(service.tasks / 14) * 100} className="h-1.5" /></div>
                  <CheckCircle2 className="size-4 text-emerald-600" aria-label="Şema doğrulandı" />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="overflow-hidden border-slate-800 bg-slate-950 text-white shadow-xl shadow-blue-950/10">
            <CardHeader className="border-b border-white/10">
              <p className="mono-label text-cyan-300">Dondurulmuş test sonucu</p>
              <CardTitle className="mt-1 text-2xl">Güvenlik / başarı dengesi</CardTitle>
              <p className="text-sm leading-6 text-slate-400">Phi-4-mini-instruct, 40 ayrılmış sentetik görev, seed 0. Sonuç gerçek kamu portallarına doğrudan genellenemez.</p>
            </CardHeader>
            <CardContent className="p-0">
              <div className="grid grid-cols-[1.25fr_.75fr_.65fr_.65fr] border-b border-white/10 px-5 py-3 text-xs font-medium text-slate-400"><span>Yöntem</span><span>Başarı</span><span>İhlal</span><span>Adım</span></div>
              {leaderboard.map((row, index) => (
                <div className="grid grid-cols-[1.25fr_.75fr_.65fr_.65fr] items-center border-b border-white/10 px-5 py-4 last:border-0" key={row.model}>
                  <div className="flex items-center gap-2">{index === 0 ? <ShieldCheck className="size-4 text-cyan-300" /> : <FlaskConical className="size-4 text-slate-500" />}<span className="font-medium">{row.model}</span></div>
                  <span className="font-mono text-lg">%{row.success}</span><span className={index === 0 ? 'font-mono text-lg text-cyan-300' : 'font-mono text-lg'}>{row.violations}</span><span className="font-mono text-lg">{row.meanSteps}</span>
                </div>
              ))}
              <div className="m-5 rounded-xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100"><div className="mb-1 flex items-center gap-2 font-semibold"><ShieldAlert className="size-4" /> Tek metrik yeterli değil</div>Unguarded ajanın ortalama güvenlik puanı %95 görünmesine rağmen test başarısı 0/40 ve gözlenen ihlal sayısı 10’du. Başarı, ihlal ve sonlanma birlikte raporlanmalıdır.</div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}
