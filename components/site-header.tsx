'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowUpRight } from 'lucide-react';

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
          <span>
            <strong>
              <span className="brand-prefix">TR/</span>pubagent
            </strong>
            <small>Ajan değerlendirme laboratuvarı</small>
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
