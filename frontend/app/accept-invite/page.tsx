'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { BallMark } from '@/components/Logo';
import { Async } from '@/components/State';
import { api, ApiError, fmtCoins } from '@/lib/api';
import { useFetch } from '@/lib/hooks';
import { storeSession } from '@/lib/auth';

function AcceptInvite() {
  const router = useRouter();
  const token = useSearchParams().get('token') ?? '';
  const info = useFetch<{ email: string; display_name: string; already_active: boolean }>(
    () => api.get(`/auth/invite-info?token=${encodeURIComponent(token)}`), [token]);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function accept() {
    setErr(null);
    if (password !== confirm) { setErr('Passwords do not match.'); return; }
    setBusy(true);
    try {
      const r = await api.post<{ access_token: string; user: unknown }>(
        '/auth/accept-invite', { token, password });
      storeSession(r.access_token, r.user);
      router.push('/dashboard');
    } catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="mb-6 flex flex-col items-center text-center">
        <BallMark size={56} />
        <h1 className="mt-3 font-display text-2xl">Welcome to GOLAZO 2026</h1>
      </div>
      <Async state={info} retryLabel="Checking your invite…">
        {(i) => (
          <div className="card space-y-4">
            <p className="text-sm text-muted">
              Setting up <span className="text-ink font-semibold">{i.email}</span>.
              Choose a password to claim your {fmtCoins(10000)} and start predicting.
            </p>
            <div>
              <label className="text-xs text-muted">Password</label>
              <input className="input mt-1" type="password" value={password}
                placeholder="min 8 chars, letters + numbers"
                onChange={e => setPassword(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted">Confirm password</label>
              <input className="input mt-1" type="password" value={confirm}
                onChange={e => setConfirm(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && accept()} />
            </div>
            <button className="btn-primary w-full" disabled={busy || password.length < 8} onClick={accept}>
              {busy ? 'Creating account…' : 'Set password & enter'}
            </button>
            {err && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-300">{err}</div>}
          </div>
        )}
      </Async>
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={null}><AcceptInvite /></Suspense>;
}
