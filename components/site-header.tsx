'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowUpRight, ShieldCheck } from 'lucide-react';

const links = [
  ['/', 'Araştırma'],
  ['/replays', 'Karar izleri'],
  ['/method', 'Yöntem'],
  ['/portal', 'Sentetik portal'],
] as const;

export function SiteHeader() {
  const pathname = usePathname();
  return (
    <header className="site-header">
      <a href="#content" className="skip-link">
        İçeriğe geç
      </a>
      <div className="header-inner">
        <Link href="/" className="site-brand">
          <span className="brand-mark">
            <ShieldCheck aria-hidden="true" size={23} />
          </span>
          <span>
            <strong>
              TR-PubAgent<span className="brand-dot">.</span>
            </strong>
            <small>AJAN GÜVENLİĞİ ARAŞTIRMASI</small>
          </span>
        </Link>
        <nav aria-label="Ana navigasyon">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              aria-current={pathname === href ? 'page' : undefined}
            >
              {label}
            </Link>
          ))}
        </nav>
        <Link href="/#byoa" className="header-agent">
          Kendi ajanını getir <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
      </div>
    </header>
  );
}
