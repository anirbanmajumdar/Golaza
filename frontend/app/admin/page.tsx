'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Async, ErrorBox } from '@/components/State';
import { api, ApiError, fmtCoins, type MatchRow, type Profile } from '@/lib/api';
import { useFetch } from '@/lib/hooks';
import { useToken } from '@/lib/auth';

interface AdminUser {
  id: number; email: string; display_name: string; status: string;
  is_admin: boolean; balance: number; bets: number; has_password: boolean;
}
interface Overview {
  users: { total: number; active: number; invited: number; disabled: number; admins: number };
  matches: { total: number; finished: number; scheduled: number };
  bets: { total: number; open: number; coins_in_play: number };
}

export default function AdminPage() {
  const { token, ready } = useToken();
  const router = useRouter();
  const [tab, setTab] = useState<'overview' | 'players' | 'results' | 'settings'>('overview');
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    if (ready && !token) { router.replace('/login'); return; }
    if (!token) return;
    api.get<Profile>('/me', token).then(p => {
      if (!p.is_admin) { router.replace('/dashboard'); } else setAllowed(true);
    }).catch(() => router.replace('/login'));
  }, [ready, token, router]);

  if (!allowed) return <p className="text-muted">Checking admin access…</p>;

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">⚙️ Admin Console</h1>
      <div className="flex gap-2">
        {(['overview', 'players', 'results', 'settings'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`pill capitalize ${tab === t ? '!bg-grass-500 !text-pitch-900' : ''}`}>{t}</button>
        ))}
      </div>
      {tab === 'overview' && <OverviewTab token={token!} />}
      {tab === 'players' && <PlayersTab token={token!} />}
      {tab === 'results' && <ResultsTab token={token!} />}
      {tab === 'settings' && <SettingsTab token={token!} />}
    </div>
  );
}

function OverviewTab({ token }: { token: string }) {
  const s = useFetch<Overview>(() => api.get('/admin/overview', token), []);
  return (
    <Async state={s}>
      {(o) => (
        <div className="space-y-4">
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
            <Card label="Players" value={`${o.users.total}`} sub={`${o.users.active} active · ${o.users.invited} invited`} />
            <Card label="Admins" value={`${o.users.admins}`} sub={`${o.users.disabled} disabled`} />
            <Card label="Matches settled" value={`${o.matches.finished}/${o.matches.total}`} sub={`${o.matches.scheduled} scheduled`} />
            <Card label="Coins in play" value={fmtCoins(o.bets.coins_in_play)} sub={`${o.bets.open} open bets`} />
          </div>
        </div>
      )}
    </Async>
  );
}

function PlayersTab({ token }: { token: string }) {
  const users = useFetch<AdminUser[]>(() => api.get('/admin/users', token), []);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [asAdmin, setAsAdmin] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function act(p: Promise<unknown>, ok: string) {
    setErr(null); setMsg(null);
    try { await p; setMsg(ok); users.reload(); }
    catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
  }
  const invite = () => act(
    api.post<{ invite_link?: string; emailed: boolean }>('/admin/users/invite',
      { email, display_name: name || undefined, is_admin: asAdmin }, token)
      .then(r => { setEmail(''); setName(''); setAsAdmin(false);
        setMsg(r.emailed ? `Invite emailed to ${email}.` : `Invite link: ${r.invite_link}`);
        users.reload(); throw { handled: true }; })
      .catch(e => { if (!(e as any)?.handled) throw e; }),
    '');

  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <h2 className="font-display text-lg">Invite a player</h2>
        <div className="grid gap-2 sm:grid-cols-3">
          <input className="input" placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="input" placeholder="display name (optional)" value={name} onChange={e => setName(e.target.value)} />
          <label className="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={asAdmin} onChange={e => setAsAdmin(e.target.checked)} className="accent-grass-500" /> make admin
          </label>
        </div>
        <button className="btn-primary" disabled={!email} onClick={invite}>Send invite</button>
        {msg && <div className="rounded-xl border border-grass-500/30 bg-grass-500/10 p-2 text-sm text-grass-400 break-all">{msg}</div>}
        {err && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-300">{err}</div>}
      </div>

      <Async state={users}>
        {(list) => (
          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted">
                <tr><th className="py-1">Player</th><th>Status</th><th className="text-right">Balance</th>
                  <th className="text-right">Bets</th><th className="text-right">Actions</th></tr>
              </thead>
              <tbody>
                {list.map(u => (
                  <tr key={u.id} className="border-t border-white/5">
                    <td className="py-2">
                      <div className="font-medium">{u.display_name} {u.is_admin && <span className="pill-gold !py-0">admin</span>}</div>
                      <div className="text-[11px] text-muted">{u.email}</div>
                    </td>
                    <td><StatusPill s={u.status} /></td>
                    <td className="text-right text-gold-400">{fmtCoins(u.balance)}</td>
                    <td className="text-right text-muted">{u.bets}</td>
                    <td className="text-right">
                      <div className="flex flex-wrap justify-end gap-1">
                        {u.status === 'disabled'
                          ? <Act onClick={() => act(api.post(`/admin/users/${u.id}/status`, { status: 'active' }, token), 'enabled')}>enable</Act>
                          : <Act onClick={() => act(api.post(`/admin/users/${u.id}/status`, { status: 'disabled' }, token), 'disabled')}>disable</Act>}
                        <Act onClick={() => act(api.post(`/admin/users/${u.id}/admin`, { is_admin: !u.is_admin }, token), 'updated')}>
                          {u.is_admin ? 'unadmin' : 'admin'}</Act>
                        {!u.has_password &&
                          <Act onClick={() => act(
                            api.post<{ invite_link?: string; emailed: boolean }>(`/admin/users/${u.id}/resend-invite`, undefined, token)
                              .then(r => { setMsg(r.emailed ? 'invite re-sent' : `link: ${r.invite_link}`); throw { handled: true }; })
                              .catch(e => { if (!(e as any)?.handled) throw e; }), '')}>resend</Act>}
                        <Act onClick={() => { const a = prompt('Grant coins (+/-):'); if (a) act(api.post(`/admin/users/${u.id}/grant`, { amount: Number(a) }, token), 'granted'); }}>±₲</Act>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Async>
    </div>
  );
}

function ResultsTab({ token }: { token: string }) {
  const matches = useFetch<MatchRow[]>(() => api.get('/matches?status=scheduled'), []);
  const [scores, setScores] = useState<Record<number, { h: string; a: string }>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function settle(id: number, auto: boolean) {
    setErr(null); setBusy(id);
    try {
      if (auto) await api.post(`/admin/matches/${id}/auto-settle`, undefined, token);
      else {
        const s = scores[id] || { h: '', a: '' };
        await api.post(`/admin/matches/${id}/settle`, { home_goals: Number(s.h || 0), away_goals: Number(s.a || 0) }, token);
      }
      matches.reload();
    } catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
    finally { setBusy(null); }
  }

  return (
    <Async state={matches}>
      {(list) => {
        const playable = list.filter(m => m.home && m.away);
        if (!playable.length) return <ErrorBox message="No scheduled matches with both teams set." />;
        return (
          <div className="space-y-3">
            {err && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-300">{err}</div>}
            <p className="text-sm text-muted">Enter a final score to settle all bets + update Elo, or auto-settle from the model.</p>
            <div className="grid gap-2">
              {playable.slice(0, 40).map(m => {
                const s = scores[m.id] || { h: '', a: '' };
                return (
                  <div key={m.id} className="card flex flex-wrap items-center justify-between gap-3">
                    <div className="text-sm">
                      <span className="pill mr-2">{m.group ? `Grp ${m.group}` : m.stage}</span>
                      {m.home!.flag} {m.home!.name} <span className="text-muted">vs</span> {m.away!.name} {m.away!.flag}
                    </div>
                    <div className="flex items-center gap-2">
                      <input className="input !w-14 text-center" inputMode="numeric" value={s.h}
                        onChange={e => setScores({ ...scores, [m.id]: { ...s, h: e.target.value.replace(/\D/g, '') } })} />
                      <span className="text-muted">–</span>
                      <input className="input !w-14 text-center" inputMode="numeric" value={s.a}
                        onChange={e => setScores({ ...scores, [m.id]: { ...s, a: e.target.value.replace(/\D/g, '') } })} />
                      <button className="btn-primary" disabled={busy === m.id || s.h === '' || s.a === ''} onClick={() => settle(m.id, false)}>Settle</button>
                      <button className="btn-ghost" disabled={busy === m.id} onClick={() => settle(m.id, true)} title="Random scoreline from the model">🎲</button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      }}
    </Async>
  );
}

interface SmtpPublic {
  smtp_host: string; smtp_port: number; smtp_user: string; smtp_from: string;
  password_set: boolean; configured: boolean; source: string;
}
function SettingsTab({ token }: { token: string }) {
  const s = useFetch<SmtpPublic>(() => api.get('/admin/settings', token), []);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [testTo, setTestTo] = useState('');

  useEffect(() => {
    if (s.data) setForm({
      smtp_host: s.data.smtp_host || 'smtp.gmail.com',
      smtp_port: String(s.data.smtp_port || 587),
      smtp_user: s.data.smtp_user || 'admin@example.com',
      smtp_from: s.data.smtp_from || 'GOLAZO 2026 <admin@example.com>',
      smtp_password: '',
    });
  }, [s.data]);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  async function save() {
    setErr(null); setMsg(null);
    try {
      const body: Record<string, unknown> = {
        smtp_host: form.smtp_host, smtp_port: Number(form.smtp_port),
        smtp_user: form.smtp_user, smtp_from: form.smtp_from,
      };
      if (form.smtp_password) body.smtp_password = form.smtp_password;
      await api.post('/admin/settings', body, token);
      setForm({ ...form, smtp_password: '' });
      setMsg('Saved.'); s.reload();
    } catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
  }
  async function sendTest() {
    setErr(null); setMsg(null);
    try {
      const r = await api.post<{ ok: boolean; message: string }>(
        '/admin/settings/test-email', { to: testTo || undefined }, token);
      if (r.ok) setMsg(`✅ ${r.message}`); else setErr(r.message);
    } catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
  }

  return (
    <Async state={s}>
      {(cfg) => (
        <div className="max-w-xl space-y-4">
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg">📧 Email (Gmail SMTP)</h2>
              <span className={cfg.configured ? 'pill-grass' : 'pill-gold'}>
                {cfg.configured ? 'configured' : 'not configured'}
              </span>
            </div>
            <p className="text-sm text-muted">
              Create an <b>App Password</b> at{' '}
              <a className="underline" href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer">
                myaccount.google.com/apppasswords</a>{' '}
              (Google account → 2-Step Verification → App passwords) and paste the
              16-character code below. Invites &amp; password codes send from here.
            </p>
            <FieldRow label="SMTP host" value={form.smtp_host || ''} onChange={set('smtp_host')} />
            <FieldRow label="Port" value={form.smtp_port || ''} onChange={set('smtp_port')} />
            <FieldRow label="Gmail address (user)" value={form.smtp_user || ''} onChange={set('smtp_user')} />
            <FieldRow label="From" value={form.smtp_from || ''} onChange={set('smtp_from')} />
            <div>
              <label className="text-xs text-muted">
                Gmail App Password {cfg.password_set && <span className="text-grass-400">(saved — leave blank to keep)</span>}
              </label>
              <input className="input mt-1" type="password" value={form.smtp_password || ''}
                placeholder={cfg.password_set ? '••••••••••••••••' : 'paste 16-char app password'}
                onChange={set('smtp_password')} />
            </div>
            <button className="btn-primary" onClick={save}>Save email settings</button>
          </div>

          <div className="card space-y-2">
            <h3 className="font-display">Send a test email</h3>
            <div className="flex gap-2">
              <input className="input" placeholder={'to (default: your admin email)'} value={testTo} onChange={e => setTestTo(e.target.value)} />
              <button className="btn-ghost whitespace-nowrap" onClick={sendTest}>Send test</button>
            </div>
          </div>

          {msg && <div className="rounded-xl border border-grass-500/30 bg-grass-500/10 p-2 text-sm text-grass-400 break-all">{msg}</div>}
          {err && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-300 break-all">{err}</div>}
        </div>
      )}
    </Async>
  );
}
function FieldRow({ label, value, onChange }:
  { label: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void }) {
  return (
    <div>
      <label className="text-xs text-muted">{label}</label>
      <input className="input mt-1" value={value} onChange={onChange} />
    </div>
  );
}

function Card({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return <div className="card"><div className="text-xs text-muted">{label}</div>
    <div className="font-display text-2xl text-gold-400">{value}</div>
    {sub && <div className="text-[11px] text-muted">{sub}</div>}</div>;
}
function Act({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return <button onClick={onClick} className="rounded-lg border border-white/15 px-2 py-1 text-xs hover:bg-white/10">{children}</button>;
}
function StatusPill({ s }: { s: string }) {
  const c = s === 'active' ? 'pill-grass' : s === 'disabled' ? 'pill' : 'pill-gold';
  return <span className={c}>{s}</span>;
}
