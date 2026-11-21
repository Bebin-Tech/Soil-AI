import {createContext, useContext, useEffect, useState, type ReactNode} from 'react';
import {api, session, saveSession, type User} from '../services/api';

const AuthContext = createContext<{user: User|null; logout: () => Promise<void>}>({user: null, logout: async () => {}});
export function AuthProvider({children}: {children: ReactNode}) {
  const [user, setUser] = useState(session()?.user || null);
  useEffect(() => {
    const update = () => setUser(session()?.user || null);
    window.addEventListener('session-change', update);
    if (session()) api.get('/users/me').then(r => {
      const existing = session();
      if (existing) saveSession({...existing, user: r.data});
    }).catch(() => saveSession(null));
    return () => window.removeEventListener('session-change', update);
  }, []);
  async function logout() {
    try { await api.post('/auth/logout', {refresh_token: session()?.refresh_token}); }
    finally { saveSession(null); }
  }
  return <AuthContext.Provider value={{user, logout}}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
