'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { BallMark } from '@/components/Logo';
import { Async } from '@/components/State';
import { api, ApiError, fmtCoins } from '@/lib/api';
import { useFetch } from '@/lib/hooks';
import { storeSession } from '@/lib/auth';

function JoinLeague() {
  const router = useRouter();
  const token = useSearchParams().get('token') ?? '';
  const info = useFetch<{ league: string; members: number }>(
    () => api.get(`/leagues/invite/info?token=${encodeURIComponent(token)}`), [token]);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function join() {
    setErr(null); setBusy(true);
    try {
      const r = await api.post<{ access_token: string; user: unknown; league: { name: string } }>(
        '/leagues/invite/accept',
        { token, email, display_name: name || undefined, password });
      storeSession(r.access_token, r.user);
      router.push('/dashboard');
    } catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="mb-6 flex flex-col items-center text-center">
        <BallMark size={56} />
        <h1 className="mt-3 font-display text-2xl">Join the league</h1>
      </div>
      <Async state={info} retryLabel="Checking your invite…">
        {(i) => (
          <div className="card space-y-4">
            <p className="text-sm text-muted">
              You&apos;re joining <span className="text-grass-400 font-semibold">{i.league}</span>
              {' '}({i.members} {i.members === 1 ? 'member' : 'members'}). Create your account
              to claim {fmtCoins(10000)} and you&apos;ll be added automatically.
            </p>
            <Field label="Email" type="email" value={email} set={setEmail} placeholder="you@example.com" />
            <Field label="Display name" value={name} set={setName} placeholder="e.g. The Gaffer" />
            <Field label="Password" type="password" value={password} set={setPassword}
              placeholder="min 8 chars, letters + numbers" onEnter={join} />
            <button className="btn-primary w-full" disabled={busy || !email || password.length < 8} onClick={join}>
              {busy ? 'Joining…' : 'Create account & join'}
            </button>
            <p className="text-xs text-muted">
              Already have a GOLAZO account? Enter the same email + your existing
              password and you&apos;ll just be added to the league.
            </p>
            {err && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-300">{err}</div>}
          </div>
        )}
      </Async>
    </div>
  );
}

function Field({ label, value, set, type = 'text', placeholder, onEnter }:
  { label: string; value: string; set: (v: string) => void; type?: string;
    placeholder?: string; onEnter?: () => void }) {
  return (
    <div>
      <label className="text-xs text-muted">{label}</label>
      <input className="input mt-1" type={type} value={value} placeholder={placeholder}
        onChange={e => set(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && onEnter) onEnter(); }} />
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={null}><JoinLeague /></Suspense>;
}
