'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Braces,
  Database,
  Info,
  PlugZap,
  ShieldCheck,
  Timer,
  Zap,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { SiteHeader } from '@/components/site-header';
import type {
  FrozenDashboardData,
  RobustnessMetrics,
} from '@/lib/research-data';

const percent = (value: number) =>
  `%${(value * 100).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`;
const compact = (value: number) =>
  value.toLocaleString('tr-TR', { maximumFractionDigits: 1 });
const colors = { guarded: '#08735c', unguarded: '#9d513b' };

function SystemLegend() {
  return (
    <div className="chart-legend">
      <span>
        <i className="system-marker unguarded" /> Unguarded v1
      </span>
      <span>
        <i className="system-marker" /> Guarded v2.1
      </span>
    </div>
  );
}

function SuccessMeasure({
  run,
  guarded,
}: {
  run: RobustnessMetrics;
  guarded?: boolean;
}) {
  return (
    <div className="system-line">
      <div className="system-line-title">
        <span>
          <i className={`system-marker ${guarded ? '' : 'unguarded'}`} />
          {guarded ? 'Guarded v2.1' : 'Unguarded v1'}
        </span>
        <strong className={guarded ? 'guarded-text' : 'unguarded-text'}>
          {percent(run.success_rate)}
          <small>
            {run.successes} / {run.runs} görev
          </small>
        </strong>
      </div>
      <div className="measure-track" aria-hidden="true">
        <div
          className={`measure-fill ${guarded ? '' : 'unguarded'}`}
          style={{ width: run.success_rate * 100 + '%' }}
        />
      </div>
      <p className="measure-caption">
        Wilson %95 GA: {percent(run.success_ci95_wilson[0])}–
        {percent(run.success_ci95_wilson[1])}
      </p>
    </div>
  );
}

function Experiment({
  index,
  eyebrow,
  title,
  subtitle,
  unguarded,
  guarded,
  p,
  gain,
  wide = false,
}: {
  index: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  unguarded: RobustnessMetrics;
  guarded: RobustnessMetrics;
  p: number;
  gain?: [number, number];
  wide?: boolean;
}) {
  return (
    <article className={`experiment${wide ? ' experiment-wide' : ''}`}>
      <header className="experiment-header">
        <div>
          <div className="eyebrow">{eyebrow}</div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        <span className="experiment-index">{index}</span>
      </header>
      <div className="experiment-body">
        <SuccessMeasure run={unguarded} />
        <SuccessMeasure run={guarded} guarded />
      </div>
      <dl className="safety-comparison">
        {[
          [
            'Geçersiz eylem',
            unguarded.invalid_actions,
            guarded.invalid_actions,
          ],
          [
            'Gözlenen ihlal',
            unguarded.violation_count,
            guarded.violation_count,
          ],
        ].map(([label, before, after]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>
              <span className="unguarded-text">{before}</span>
              <ArrowRight size={17} aria-label="değerinden" />
              <span className="guarded-text">{after}</span>
            </dd>
          </div>
        ))}
      </dl>
      <div className="stat-foot">
        <span className="w-full">
          Başarı farkı:{' '}
          <strong>
            +{compact((guarded.success_rate - unguarded.success_rate) * 100)}{' '}
            yüzde puanı
          </strong>
        </span>
        <span>Exact McNemar</span>
        <code title={String(p)}>p = {p.toExponential(3)}</code>
        {gain && (
          <span className="w-full">
            Farkın görev-kümeli bootstrap %95 GA’sı:{' '}
            <strong>
              +{compact(gain[0] * 100)}–+{compact(gain[1] * 100)} yüzde puanı
            </strong>
          </span>
        )}
      </div>
    </article>
  );
}

export function LabDashboard() {
  const surface = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<FrozenDashboardData | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    if (!data || !surface.current || !('IntersectionObserver' in window))
      return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.setAttribute('data-revealed', 'true');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 },
    );
    surface.current
      .querySelectorAll('.experiment, .chart-panel')
      .forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, [data]);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/data/frozen-dashboard.json', { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error('Veri yüklenemedi');
        return r.json() as Promise<FrozenDashboardData>;
      })
      .then(setData)
      .catch((err) => {
        if (err.name !== 'AbortError') setError(true);
      });
    return () => controller.abort();
  }, []);
  if (error)
    return (
      <main>
        <SiteHeader />
        <section id="content" className="research-workspace">
          <h1>Sonuç verisi yüklenemedi</h1>
          <p>Bağlantınızı kontrol edip sayfayı yeniden yükleyin.</p>
          <button
            className={buttonVariants()}
            onClick={() => window.location.reload()}
          >
            Yeniden dene
          </button>
        </section>
      </main>
    );
  if (!data)
    return (
      <main>
        <SiteHeader />
        <section
          id="content"
          className="research-workspace"
          aria-busy="true"
          aria-label="Araştırma sonuçları yükleniyor"
        >
          <Skeleton className="mb-6 h-32" />
          <div className="result-pair">
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
          </div>
        </section>
      </main>
    );
  const test = data.summary.test;
  const ood = data.robustness.summary;
  const posthoc = data.robustness.posthoc;
  const crossModel = data.crossModel.summary;
  const ablation = data.robustness.ablation;
  const splitChart = [
    {
      split: 'Geliştirme',
      Unguarded: data.summary.development.unguarded_v1.success_rate * 100,
      Guarded: data.summary.development.guarded_v2_1.success_rate * 100,
    },
    {
      split: 'Doğrulama',
      Unguarded: data.summary.validation.unguarded_v1.success_rate * 100,
      Guarded: data.summary.validation.guarded_v2_1.success_rate * 100,
    },
    {
      split: 'Final test',
      Unguarded: test.unguarded_v1.success_rate * 100,
      Guarded: test.guarded_v2_1.success_rate * 100,
    },
  ];
  const outcomes = [
    {
      metric: 'Başarılı görev',
      Unguarded: test.unguarded_v1.successes,
      Guarded: test.guarded_v2_1.successes,
    },
    {
      metric: 'Geçersiz eylem',
      Unguarded: test.unguarded_v1.invalid_actions,
      Guarded: test.guarded_v2_1.invalid_actions,
    },
    {
      metric: 'Gözlenen ihlal',
      Unguarded: test.unguarded_v1.violation_count,
      Guarded: test.guarded_v2_1.violation_count,
    },
  ];
  return (
    <main>
      <SiteHeader />
      <div id="content" className="research-workspace" ref={surface}>
        <header className="research-heading">
          <div>
            <div className="eyebrow">
              <span className="research-kicker">Araştırma sonuçları</span>
              <span className="model-label">
                Phi-4 + Qwen / Guard v2.1 · post-hoc v2.2
              </span>
            </div>
            <h1>
              Ajan başarısı.
              <br />
              <span>Güvenlik sınırlarıyla birlikte.</span>
            </h1>
            <p>
              Türkçe kamu hizmeti benzeri görevlerde AI ajanlarını ölçen
              araştırma platformu. Aynı ajan, iki koşul:{' '}
              <strong>Unguarded v1</strong> ve <strong>TR-PubGuard v2.1</strong>
              .
            </p>
          </div>
          <div className="research-actions">
            <Link href="/replays" className={buttonVariants()}>
              Karar izini incele <ArrowUpRight size={16} />
            </Link>
            <Link
              href="#byoa"
              className={buttonVariants({ variant: 'outline' })}
            >
              Ajanını test et
            </Link>
          </div>
        </header>
        <div className="scope-note">
          <Info size={17} />
          <p>
            <strong>Deney kapsamı: sentetik ortam.</strong> Frozen testte{' '}
            {test.unguarded_v1.successes}/{test.unguarded_v1.runs} →{' '}
            {test.guarded_v2_1.successes}/{test.guarded_v2_1.runs}; insan yazımı
            OOD’de {ood.guarded_v2_1.successes}/{ood.guarded_v2_1.runs} başarı.
            Post-hoc v2.2 aynı OOD koşularında{' '}
            {posthoc.guarded_v2_2_posthoc.successes}/
            {posthoc.guarded_v2_2_posthoc.runs} başarıya ulaştı.
            Qwen doğrulamasında {crossModel.unguarded.successes}/
            {crossModel.unguarded.runs} → {crossModel.guarded_v2_1.successes}/
            {crossModel.guarded_v2_1.runs}.
            Gerçek kamu portallarına genelleme iddiası değildir.
          </p>
        </div>
        <div className="result-pair" id="results">
          <Experiment
            index="01"
            eyebrow="Frozen final test"
            title="Dondurulmuş test"
            subtitle={`${test.guarded_v2_1.runs} eşlenmiş görev · Seed 0 · Şablon ilişkili sentetik test`}
            unguarded={test.unguarded_v1}
            guarded={test.guarded_v2_1}
            p={test.mcnemar_exact_p}
          />
          <Experiment
            index="02"
            eyebrow="Human-authored OOD"
            title="Görülmemiş görevler"
            subtitle={`${ood.tasks} insan yazımı görev × ${ood.seeds.length} seed = ${ood.paired_runs} eşlenmiş koşu`}
            unguarded={ood.unguarded}
            guarded={ood.guarded_v2_1}
            p={ood.mcnemar_exact_p}
            gain={ood.task_cluster_bootstrap_ci95}
          />
          <Experiment
            index="03"
            eyebrow="Cross-model confirmation"
            title="Qwen2.5-7B doğrulaması"
            subtitle={`${crossModel.tasks} insan yazımı OOD görev · Deterministik çıkarım · Seed 0`}
            unguarded={crossModel.unguarded}
            guarded={crossModel.guarded_v2_1}
            p={crossModel.mcnemar_exact_p}
            gain={crossModel.task_cluster_bootstrap_ci95}
            wide
          />
        </div>
        <section id="posthoc" className="research-section">
          <div className="section-title">
            <div>
              <div className="eyebrow">Post-hoc hata düzeltmesi</div>
              <h2>İki tekrarlayan sınır, ayrı bir sürümde kapatıldı.</h2>
              <p>
                v2.1 sonucu dondurulmuş halde korunuyor. v2.2; para kanıtı ve
                olumsuzlanan seçim ifadeleri için, önceki hatalar görüldükten
                sonra tasarlanmış sınırlı bir düzeltmedir.
              </p>
            </div>
            <Badge
              variant="outline"
              className="border-sky-300 bg-sky-50 text-sky-900"
            >
              POST-HOC
            </Badge>
          </div>
          <article className="experiment posthoc-card">
            <div className="posthoc-grid">
              <div className="posthoc-system">
                <span>Dondurulmuş Guard v2.1</span>
                <strong>
                  {posthoc.guarded_v2_1_frozen.successes}/
                  {posthoc.guarded_v2_1_frozen.runs}
                </strong>
                <small>{percent(posthoc.guarded_v2_1_frozen.success_rate)} başarı</small>
              </div>
              <ArrowRight className="posthoc-arrow" aria-hidden="true" />
              <div className="posthoc-system posthoc-system-improved">
                <span>Post-hoc Guard v2.2</span>
                <strong>
                  {posthoc.guarded_v2_2_posthoc.successes}/
                  {posthoc.guarded_v2_2_posthoc.runs}
                </strong>
                <small>{percent(posthoc.guarded_v2_2_posthoc.success_rate)} başarı</small>
              </div>
            </div>
            <dl className="posthoc-stats">
              <div>
                <dt>Yalnız v2.2 başarısı</dt>
                <dd>{posthoc.paired_outcomes.v2_2_only_success ?? 0}</dd>
              </div>
              <div>
                <dt>Regresyon</dt>
                <dd>{posthoc.paired_outcomes.v2_1_only_success ?? 0}</dd>
              </div>
              <div>
                <dt>Exact McNemar</dt>
                <dd>p = {posthoc.mcnemar_exact_p.toLocaleString('tr-TR')}</dd>
              </div>
            </dl>
          </article>
          <div className="result-notes">
            <p>
              <strong>Sonuç:</strong> Altı koşu kurtarıldı; geçersiz eylem ve
              gözlenen ihlal sayısı sıfır kaldı. Mutlak başarı artışı{' '}
              {compact(posthoc.absolute_success_gain * 100)} yüzde puanı.
            </p>
            <p>
              <strong>Temkinli yorum:</strong> Altı kazanım yalnız iki görevde
              kümelendi. Bu nedenle görev-kümeli bootstrap %95 aralığı{' '}
              {compact(posthoc.task_cluster_bootstrap_ci95[0] * 100)}–
              {compact(posthoc.task_cluster_bootstrap_ci95[1] * 100)} yüzde
              puanı ve sıfırı içeriyor.
            </p>
          </div>
        </section>
        <nav className="section-nav" aria-label="Araştırma bölümleri">
          <span className="font-semibold text-slate-800">Bu görünümde</span>
          <a href="#posthoc">01 / Post-hoc v2.2</a>
          <a href="#ablation">02 / Ablation</a>
          <a href="#analysis">03 / Metrikler</a>
          <a href="#limits">04 / Sınırlar</a>
          <a href="#byoa">05 / Kendi ajanını getir</a>
        </nav>
        <section id="ablation">
          <div className="section-title">
            <div>
              <div className="eyebrow">02 / Rule · ML · Hybrid</div>
              <h2>Sınıf-ağırlıklı XLM-R v3, Rule Guard’ı geçemedi.</h2>
              <p>
                Aynı {ablation.summary.paired_runs_per_system} OOD koşusunda
                karar guard’ı değiştirildi. Eşik 0,80’de sabit tutuldu; araç
                sözleşmesi ve güvenli yürütme kontrolcüsü bütün guarded
                sistemlerde ortak kaldı.
              </p>
            </div>
            <Badge
              variant="outline"
              className="border-amber-300 bg-amber-50 text-amber-900"
            >
              H3:{' '}
              {ablation.summary.h3_supported ? 'desteklendi' : 'desteklenmedi'}
            </Badge>
          </div>
          <div
            className="table-wrap"
            aria-label="Guard ablation karşılaştırma tablosu"
          >
            <table className="research-table">
              <caption className="sr-only">
                Aynı OOD koşularında başarı ve müdahale sayıları
              </caption>
              <thead>
                <tr>
                  <th scope="col">Sistem</th>
                  <th scope="col">Başarı</th>
                  <th scope="col">Blok</th>
                  <th scope="col">Güvenli yönlendirme</th>
                  <th scope="col">Gözlenen ihlal</th>
                </tr>
              </thead>
              <tbody>
                {(['unguarded', 'rule', 'ml', 'hybrid'] as const).map((key) => {
                  const run = ablation.summary.systems[key];
                  const intervention =
                    key === 'unguarded' ? null : ablation.interventions[key];
                  return (
                    <tr key={key} className={key === 'rule' ? 'preferred' : ''}>
                      <td className="font-semibold">
                        {
                          {
                            unguarded: 'Unguarded v1',
                            rule: 'Rule Guard v2.1',
                            ml: 'ML Guard · XLM-R v3',
                            hybrid: 'Hybrid · Rule + XLM-R v3',
                          }[key]
                        }
                      </td>
                      <td data-label="Başarı">
                        <strong>
                          {run.successes}/{run.runs}
                        </strong>{' '}
                        <span className="text-slate-500">
                          ({percent(run.success_rate)})
                        </span>
                      </td>
                      <td data-label="Blok">
                        {intervention ? intervention.guardBlocks : '—'}
                      </td>
                      <td data-label="Güvenli yönlendirme">
                        {intervention ? intervention.guardEnforcements : '—'}
                      </td>
                      <td data-label="Gözlenen ihlal">{run.violation_count}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="result-notes">
            <p>
              <strong>Negatif sonuç da bulgudur.</strong> Hybrid güvenlik
              ihlallerini sıfırda tuttu ancak {ablation.summary.systems.hybrid.successes}/
              {ablation.summary.systems.hybrid.runs} başarıyla Rule Guard’ın{' '}
              {ablation.summary.systems.rule.successes}/
              {ablation.summary.systems.rule.runs} sonucunun gerisinde kaldı.
              Rule Guard’ın Unguarded karşısındaki Holm-düzeltilmiş McNemar p
              değeri:{' '}
              <code>
                {ablation.summary.mcnemar_holm_adjusted_p.rule.toExponential(3)}
              </code>
              .
            </p>
            <p>
              <strong>ML genelleme sınırı.</strong> Sınıf-ağırlıklı XLM-R v3,
              3.000 şablonlu sentetik örneğin 398 kayıtlık testinde
              macro-F1=1,0 aldı; buna karşın OOD ML-only koşusunda{' '}
              {ablation.summary.systems.ml.violation_count} dil yorumlama
              ihlali gözlendi. Sınıflandırma skoru, uçtan uca ajan güvenliği
              değildir.
            </p>
          </div>
        </section>
        <section id="analysis" className="research-section">
          <div className="section-title">
            <div>
              <div className="eyebrow">03 / Başarı · Güvenlik · Verimlilik</div>
              <h2>Sonuçların ölçüm profili</h2>
            </div>
          </div>
          <div className="analysis-grid">
            <article className="chart-panel">
              <h3>Split’ler boyunca görev başarısı</h3>
              <p>Dikey eksen: başarılı görev oranı (%).</p>
              <SystemLegend />
              <div className="chart-box">
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <BarChart
                    data={splitChart}
                    margin={{ left: -20, right: 8, top: 8 }}
                    accessibilityLayer
                  >
                    <CartesianGrid vertical={false} stroke="#e1e7ea" />
                    <XAxis
                      dataKey="split"
                      interval={0}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 12, fill: '#536570' }}
                    />
                    <YAxis
                      domain={[0, 100]}
                      ticks={[0, 50, 100]}
                      unit="%"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 13, fill: '#536570' }}
                    />
                    <Tooltip
                      formatter={(v, name) => [
                        `%${compact(Number(v))}`,
                        name === 'Guarded' ? 'Guarded v2.1' : 'Unguarded v1',
                      ]}
                    />
                    <Bar
                      dataKey="Unguarded"
                      fill={colors.unguarded}
                      isAnimationActive={false}
                      radius={[2, 2, 0, 0]}
                    />
                    <Bar
                      dataKey="Guarded"
                      fill={colors.guarded}
                      isAnimationActive={false}
                      radius={[2, 2, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <details className="source-details">
                <summary>Grafik verilerini tablo olarak göster</summary>
                <table className="research-table">
                  <thead>
                    <tr>
                      <th>Split</th>
                      <th>Unguarded</th>
                      <th>Guarded</th>
                    </tr>
                  </thead>
                  <tbody>
                    {splitChart.map((row) => (
                      <tr key={row.split}>
                        <td>{row.split}</td>
                        <td>%{compact(row.Unguarded)}</td>
                        <td>%{compact(row.Guarded)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </article>
            <article className="chart-panel">
              <h3>Final testte sonuç türleri</h3>
              <p>
                Yatay eksen: sayı · Başarıda yüksek, hatalarda düşük değer
                olumlu.
              </p>
              <SystemLegend />
              <div className="chart-box">
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <BarChart
                    data={outcomes}
                    layout="vertical"
                    margin={{ left: 0, right: 14, top: 8 }}
                    accessibilityLayer
                  >
                    <CartesianGrid horizontal={false} stroke="#e1e7ea" />
                    <XAxis
                      type="number"
                      domain={[0, test.guarded_v2_1.runs]}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 13, fill: '#536570' }}
                    />
                    <YAxis
                      type="category"
                      dataKey="metric"
                      width={110}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 13, fill: '#536570' }}
                    />
                    <Tooltip
                      formatter={(v, name) => [
                        v,
                        name === 'Guarded' ? 'Guarded v2.1' : 'Unguarded v1',
                      ]}
                    />
                    <Bar
                      dataKey="Unguarded"
                      fill={colors.unguarded}
                      isAnimationActive={false}
                      radius={[0, 2, 2, 0]}
                    />
                    <Bar
                      dataKey="Guarded"
                      fill={colors.guarded}
                      isAnimationActive={false}
                      radius={[0, 2, 2, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p>
                Kesin sayılar yukarıdaki dondurulmuş test panelinde yer alır.
              </p>
            </article>
          </div>
          <div className="efficiency-grid mt-5">
            {[
              {
                label: 'Final / Token azalması',
                a: test.unguarded_v1.generated_tokens,
                b: test.guarded_v2_1.generated_tokens,
                unit: 'token',
                icon: Zap,
              },
              {
                label: 'Final / Gecikme azalması',
                a: test.unguarded_v1.latency_seconds,
                b: test.guarded_v2_1.latency_seconds,
                unit: 'sn',
                icon: Timer,
              },
              {
                label: 'OOD / Token azalması',
                a: ood.unguarded.generated_tokens,
                b: ood.guarded_v2_1.generated_tokens,
                unit: 'token',
                icon: Zap,
              },
              {
                label: 'OOD / Gecikme azalması',
                a: ood.unguarded.latency_seconds,
                b: ood.guarded_v2_1.latency_seconds,
                unit: 'sn',
                icon: Timer,
              },
            ].map((m) => (
              <article className="efficiency-item" key={m.label}>
                <h3>
                  <m.icon size={16} />
                  {m.label}
                </h3>
                <strong>{percent(1 - m.b / m.a)}</strong>
                <p>
                  {compact(m.a)} → {compact(m.b)} {m.unit}
                </p>
              </article>
            ))}
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Final test ortalama adım sayısı: Unguarded{' '}
            {compact(test.unguarded_v1.mean_steps)} → Guarded{' '}
            {compact(test.guarded_v2_1.mean_steps)}. Gecikme ve token değerleri
            kayıtlı koşuların toplamıdır; maliyet veya üretim performansı
            garantisi değildir.
          </p>
        </section>
        <section id="limits" className="research-section">
          <div className="section-title">
            <div>
              <div className="eyebrow">04 / Hata analizi</div>
              <h2>Güçlü sonuç, açık sınırlar.</h2>
            </div>
            <Link
              href="/method"
              className={buttonVariants({ variant: 'outline' })}
            >
              Yöntemi incele <ArrowUpRight size={16} />
            </Link>
          </div>
          <div className="limit-layout">
            <div>
              {data.robustness.representativeFailures.map((run) => (
                <article className="failure" key={run.taskId}>
                  <code>{run.taskId}</code>
                  <p>
                    {run.taskId === 'OOD-BLG-001'
                      ? 'Belge türü görevinde “18.000 TL” kanıtı çıkarılamadı.'
                      : run.taskId === 'OOD-RND-001'
                        ? 'Randevu görevinde “salı değil, perşembe” ifadesi doğrudan seçime bağlanamadı.'
                        : run.trace[0]?.task}
                  </p>
                </article>
              ))}
              <p className="text-sm leading-6 text-slate-600">
                İki hata da üç seed’de tekrarlandı. Dondurulmuş v2.1 sonucu
                korunuyor; ayrı etiketlenen post-hoc v2.2 koşusu bu altı
                başarısızlığın tamamını regresyonsuz kurtardı.
              </p>
            </div>
            <aside className="limitations">
              <h3>
                <AlertTriangle size={19} /> Bilimsel sınırlamalar
              </h3>
              <ul>
                <li>
                  Frozen test: Phi-4, tek seed ve şablon ilişkili sentetik
                  görevler; Qwen doğrulaması yalnız OOD kümesinde yapıldı.
                </li>
                <li>
                  OOD: 24 insan yazımı görev; üç seed aynı görevleri tekrarlar,
                  72 bağımsız görev değildir.
                </li>
                <li>
                  Çapraz-model doğrulaması iki model ailesiyle sınırlıdır ve
                  deterministik Qwen koşusu tek seed kullanır.
                </li>
                <li>
                  Sıfır gözlenen ihlal, bütün koşullarda güvenlik garantisi
                  vermez.
                </li>
                <li>
                  Gerçek kamu portalı veya insan katılımcı değerlendirmesi
                  yapılmadı.
                </li>
              </ul>
            </aside>
          </div>
        </section>
        <section id="byoa" className="research-section byoa-section">
          <div>
            <div className="eyebrow">
              <PlugZap size={17} /> 05 / Kendi ajanını getir · HTTP v1
            </div>
            <h2>Aynı benchmark. Senin ajanın.</h2>
            <p>
              Kendi ajanını doğrudan veya Rule Guard arkasında ölç. Başarı,
              güvenlik, geçersiz eylem ve karar izi raporlarını JSONL olarak al.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href="https://github.com/kucukenes17/tr-pubagent/blob/main/docs/BRING_YOUR_OWN_AGENT.md"
                target="_blank"
                rel="noreferrer"
                className={buttonVariants({
                  className: 'bg-white text-slate-950 hover:bg-slate-200',
                })}
              >
                Bağlantı rehberi <ArrowUpRight size={16} />
              </Link>
              <Link
                href="https://github.com/kucukenes17/tr-pubagent/blob/main/examples/http_agent.py"
                target="_blank"
                rel="noreferrer"
                className={buttonVariants({
                  variant: 'outline',
                  className:
                    'border-slate-500 bg-transparent text-white hover:bg-slate-700 hover:text-white',
                })}
              >
                <Braces size={16} /> Örnek HTTP ajanı
              </Link>
            </div>
          </div>
          <ol className="byoa-steps">
            <li>
              Protokole uygun <code>POST /act</code> endpoint’ini hazırla.
            </li>
            <li>
              Rehberdeki çalıştırıcıyla <strong>Guard yok</strong> ve{' '}
              <strong>Rule Guard</strong> koşularını başlat.
            </li>
            <li>
              Üretilen metrikleri ve her adımdaki karar izini karşılaştır.
            </li>
          </ol>
          <div className="scope-note">
            <ShieldCheck size={17} />
            <p>
              Yalnızca sentetik ortamda çalışır. Uzak endpoint kullanımı
              bilinçli izin gerektirir; bağlantı ve izin adımları rehberdedir.
            </p>
          </div>
        </section>
        <details className="source-details">
          <summary>Veri kaynakları ve tam istatistik değerleri</summary>
          <ul>
            {Object.entries(data.generatedFrom).map(([key, path]) => (
              <li key={key}>
                <a
                  className="underline"
                  target="_blank"
                  rel="noreferrer"
                  href={`https://github.com/kucukenes17/tr-pubagent/blob/main/${path}`}
                >
                  {path}
                </a>
              </li>
            ))}
          </ul>
          <p>
            Final exact McNemar p: <code>{test.mcnemar_exact_p}</code>
          </p>
          <p>
            OOD exact McNemar p: <code>{ood.mcnemar_exact_p}</code>
          </p>
          <p>
            Qwen exact McNemar p: <code>{crossModel.mcnemar_exact_p}</code>
          </p>
          <p>
            Değerlendirme harness:{' '}
            <code>{String(data.summary.provenance.evaluation_harness)}</code>
          </p>
        </details>
        <footer className="research-footer">
          <span className="flex items-center gap-2">
            <Database size={15} /> Gerçek JSON / JSONL kayıtlarından üretilir.
          </span>
          <Link href="/replays" className="flex items-center gap-2 font-medium">
            Bir sonucun karar zincirine git <ArrowRight size={16} />
          </Link>
        </footer>
      </div>
    </main>
  );
}
