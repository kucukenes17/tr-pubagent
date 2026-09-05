import Link from 'next/link';
import { Activity, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export function SiteHeader() {
  return (
    <header className="border-b border-slate-200/80 bg-white/85 backdrop-blur-xl">
      <div className="mx-auto flex min-h-16 max-w-[1440px] items-center justify-between gap-5 px-5 lg:px-8">
        <Link href="/" className="flex items-center gap-3 rounded-lg">
          <span className="grid size-9 place-items-center rounded-xl bg-slate-950 text-cyan-300 shadow-lg shadow-blue-950/15"><ShieldCheck className="size-5" aria-hidden="true" /></span>
          <span><span className="block text-[15px] font-bold tracking-tight">TR PubAgent</span><span className="mono-label block text-[10px] text-slate-500">Safety research lab</span></span>
        </Link>
        <nav aria-label="Ana navigasyon" className="hidden items-center gap-1 md:flex">
          <Link className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100" href="/">Laboratuvar</Link>
          <Link className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100" href="/portal">Sentetik portal</Link>
          <Link className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100" href="/replays">Koşu kayıtları</Link>
          <Link className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100" href="/method">Yöntem</Link>
        </nav>
        <Badge variant="outline" className="gap-1.5 border-emerald-200 bg-emerald-50 text-emerald-800"><Activity className="size-3" aria-hidden="true" /> v0.1 araştırma MVP</Badge>
      </div>
    </header>
  );
}
