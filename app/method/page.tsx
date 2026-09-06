import { Database, FlaskConical, GitCompareArrows, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SiteHeader } from '@/components/site-header';

const stages = [
  { icon: Database, label: 'Girdi', title: 'Doğuştan Türkçe görev', body: 'Görev, başlangıç durumu, sabit kullanıcı cevapları ve gizli doğrulama koşullarıyla tanımlanır.' },
  { icon: FlaskConical, label: 'Ajan', title: 'Phi-4 + araç çağırma', body: 'Ajan görünür görev ve form durumunu okur, yapılandırılmış portal araçlarından tek bir eylem önerir.' },
  { icon: ShieldCheck, label: 'Koruma', title: 'TR-PubGuard v2.1', body: 'Kanıt bağlama, yetki sözleşmesi ve deterministik yürütme kuralları eylemi uygular, engeller veya güvenli bir adıma yönlendirir.' },
  { icon: GitCompareArrows, label: 'Ölçüm', title: 'Deterministik değerlendirici', body: 'Son ekran yerine veri tabanı durumu denetlenir; başarı, ihlal, açıklama ve durum koruma puanları üretilir.' },
] as const;

export default function MethodPage() {
  return <main className="min-h-screen"><SiteHeader /><section className="mx-auto max-w-6xl px-5 py-10 lg:px-8"><Badge className="bg-blue-600 text-white">Dondurulmuş deney tamamlandı</Badge><h1 className="mt-5 max-w-4xl text-4xl font-semibold tracking-tight text-slate-950 md:text-6xl">Sonuca değil, karar zincirine bakıyoruz.</h1><p className="mt-5 max-w-3xl text-lg leading-8 text-slate-600">TR PubAgent, “işlem tamamlandı” ölçümünün sakladığı kritik güvenlik hatalarını görünür ve tekrar üretilebilir hâle getirir.</p><div className="mt-10 grid gap-5 md:grid-cols-2">{stages.map((stage, index) => <Card key={stage.title} className="border-slate-200 bg-white"><CardHeader><div className="flex items-center justify-between"><span className="grid size-11 place-items-center rounded-xl bg-blue-50 text-blue-700"><stage.icon className="size-5" /></span><span className="font-mono text-sm text-slate-400">0{index + 1}</span></div><p className="mono-label pt-4 text-blue-700">{stage.label}</p><CardTitle className="text-2xl">{stage.title}</CardTitle></CardHeader><CardContent><p className="leading-7 text-slate-600">{stage.body}</p></CardContent></Card>)}</div><div className="mt-8 rounded-2xl border border-slate-800 bg-slate-950 p-6 text-white"><p className="mono-label text-cyan-300">Dondurulmuş final test</p><p className="mt-2 max-w-4xl text-xl leading-8">Guarded v2.1 başarıyı 0/40’tan 40/40’a çıkardı; gözlenen ihlalleri 10’dan 0’a ve üretilen token sayısını %92,7 azalttı. Sonuç yalnızca sentetik test split’i kapsamındadır.</p></div></section></main>;
}
