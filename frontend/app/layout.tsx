import type { Metadata } from 'next';
import './globals.css';
import { NavBar } from '@/components/NavBar';

export const metadata: Metadata = {
  title: 'GOLAZO 2026 — World Cup Prediction League',
  description: 'A play-money World Cup 2026 prediction league for friends, '
    + 'powered by an Elo + Dixon–Coles goal model, Monte-Carlo simulation '
    + 'and proper-scoring skill rankings.',
  icons: { icon: '/logo.svg' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NavBar />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        <footer className="border-t border-white/10 py-8 text-center text-xs text-muted">
          GOLAZO 2026 · Play-money only — no real wagering. Built for friends.
          <span className="mx-2">·</span>
          Elo · Dixon–Coles · Monte-Carlo · Kelly · Brier
        </footer>
      </body>
    </html>
  );
}
