import axios from 'axios';

export type User = {id: string; name: string; email: string; roles: string[]; language: 'en'|'ta'; active: boolean};
type Tokens = {access_token: string; refresh_token: string; user: User};
// Session storage limits token persistence to this tab. Production should use an HttpOnly-cookie BFF.
let tokens: Tokens | null = JSON.parse(sessionStorage.getItem('soilai-session') || 'null');
export const api = axios.create({baseURL: '/api/v1', timeout: 30000});
export function saveSession(value: Tokens | null) {
  tokens = value;
  if (value) sessionStorage.setItem('soilai-session', JSON.stringify(value));
  else sessionStorage.removeItem('soilai-session');
  window.dispatchEvent(new Event('session-change'));
}
export const session = () => tokens;
api.interceptors.request.use(config => {
  if (tokens) config.headers.Authorization = `Bearer ${tokens.access_token}`;
  return config;
});
let refreshing: Promise<void> | null = null;
api.interceptors.response.use(r => r, async error => {
  const config = error.config;
  if (error.response?.status === 401 && tokens && !config._retry && !config.url.startsWith('/auth/')) {
    config._retry = true;
    refreshing ||= axios.post('/api/v1/auth/refresh', {refresh_token: tokens.refresh_token})
      .then(r => saveSession(r.data)).catch(e => {saveSession(null); throw e;}).finally(() => {refreshing = null;});
    await refreshing;
    return api(config);
  }
  return Promise.reject(error);
});
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    return typeof detail === 'string' ? detail : typeof detail?.message === 'string' ? detail.message : Array.isArray(detail) ? detail.map(x => `${x.loc.slice(1).join('.')}: ${x.msg}`).join('; ') : error.message;
  }
  return error instanceof Error ? error.message : 'Unable to complete this request';
}
