'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { BallMark } from '@/components/Logo';
import { api, ApiError } from '@/lib/api';
import { storeSession } from '@/lib/auth';

type Mode = 'login' | 'forgot' | 'reset';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  async function run(fn: () => Promise<void>) {
    setErr(null); setBusy(true);
    try { await fn(); }
    catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  const login = () => run(async () => {
    const r = await api.post<{ access_token: string; user: unknown }>(
      '/auth/login', { email, password });
    storeSession(r.access_token, r.user);
    router.push('/dashboard');
  });

  const forgot = () => run(async () => {
    const r = await api.post<{ dev_otp?: string }>('/auth/forgot-password', { email });
    setDevOtp(r.dev_otp ?? null);
    setNote(`If ${email} is registered, a reset code is on its way.`);
    setMode('reset');
  });

  const reset = () => run(async () => {
    const r = await api.post<{ access_token: string; user: unknown }>(
      '/auth/reset-password', { email, code, new_password: newPassword });
    storeSession(r.access_token, r.user);
    router.push('/dashboard');
  });

  return (
    <div className="mx-auto max-w-md">
      <div className="mb-6 flex flex-col items-center text-center">
        <BallMark size={56} />
        <h1 className="mt-3 font-display text-2xl">
          {mode === 'login' ? 'Sign in to GOLAZO' : mode === 'forgot' ? 'Reset your password' : 'Enter your code'}
        </h1>
        <p className="text-sm text-muted">
          {mode === 'login'
            ? 'Private league — accounts are created by invitation.'
            : 'We email a one-time code to verify it’s you.'}
        </p>
      </div>

      <div className="card space-y-4">
        {mode === 'login' && (
          <>
            <Field label="Email" type="email" value={email} set={setEmail} placeholder="you@example.com" />
            <Field label="Password" type="password" value={password} set={setPassword}
                   onEnter={login} />
            <button className="btn-primary w-full" disabled={busy || !email || !password} onClick={login}>
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
            <button className="text-xs text-muted hover:text-ink" onClick={() => { setMode('forgot'); setErr(null); }}>
              Forgot password? · First time? Use your invite link, then reset here.
            </button>
          </>
        )}

        {mode === 'forgot' && (
          <>
            <Field label="Email" type="email" value={email} set={setEmail}
                   placeholder="you@example.com" onEnter={forgot} />
            <button className="btn-primary w-full" disabled={busy || !email} onClick={forgot}>
              {busy ? 'Sending…' : 'Email me a code'}
            </button>
            <button className="text-xs text-muted hover:text-ink" onClick={() => setMode('login')}>← back to sign in</button>
          </>
        )}

        {mode === 'reset' && (
          <>
            {note && <div className="rounded-xl border border-grass-500/30 bg-grass-500/10 p-2 text-xs text-grass-400">{note}</div>}
            {devOtp && (
              <div className="rounded-xl border border-gold-500/40 bg-gold-500/10 p-2 text-sm">
                <span className="text-gold-400 font-semibold">Dev mode code:</span>{' '}
                <code className="font-display tracking-widest">{devOtp}</code>
              </div>
            )}
            <Field label="Code" value={code} set={(v) => setCode(v.replace(/\D/g, ''))} placeholder="6-digit code" />
            <Field label="New password" type="password" value={newPassword} set={setNewPassword}
                   placeholder="min 8 chars, letters + numbers" onEnter={reset} />
            <button className="btn-primary w-full" disabled={busy || code.length < 4 || newPassword.length < 8} onClick={reset}>
              {busy ? 'Saving…' : 'Set password & sign in'}
            </button>
            <button className="text-xs text-muted hover:text-ink" onClick={() => setMode('login')}>← back to sign in</button>
          </>
        )}

        {err && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-300">{err}</div>}
      </div>
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
