'use client';

import { useEffect, useState } from 'react';

const TOKEN_KEY = 'golazo_token';
const USER_KEY = 'golazo_user';

export function storeSession(token: string, user: unknown) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new Event('golazo-auth'));
}

export function readToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function clearSession() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new Event('golazo-auth'));
}

/** React hook: returns the current token (null until hydrated). */
export function useToken(): { token: string | null; ready: boolean } {
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const sync = () => setToken(readToken());
    sync();
    setReady(true);
    window.addEventListener('golazo-auth', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('golazo-auth', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);
  return { token, ready };
}
