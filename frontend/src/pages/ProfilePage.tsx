import {t,useLanguage} from '../i18n';
import { useState, type FormEvent } from 'react';
import { useAuth } from '../contexts/Auth';
import { useApi } from '../hooks/useApi';
import { api, session, saveSession, errorMessage } from '../services/api';
import { PageHeading, ErrorNotice } from '../components/Common';
export default function ProfilePage() {
    useLanguage();
    const { user } = useAuth();
    const [name, setName] = useState(user?.name || ''), [language, setLanguage] = useState<'en' | 'ta'>(user?.language || 'en'), [error, setError] = useState(''), [saved, setSaved] = useState(false), [busy, setBusy] = useState(false);
    const sessions = useApi<{
        id: string;
        created_at: string;
        expires_at: string;
    }[]>('/auth/sessions');
    async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setError(''); try {
        const r = await api.put('/users/me', { name, language });
        const existing = session();
        if (existing)
            saveSession({ ...existing, user: r.data });
        setSaved(true);
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    return <><PageHeading eyebrow={t("MAKE YOURSELF AT HOME")} title={t("Workspace settings")} description={t("Manage your profile, preferred language and active sessions.")}/><section className="panel form-panel"><h3>{t("Your profile")}</h3><form onSubmit={submit} style={{ marginTop: 25, maxWidth: 550 }}><label>{t("Full name")}<input value={name} onChange={e => setName(e.target.value)} required minLength={2} maxLength={100}/></label><label>{t("Email")}<input value={user?.email} readOnly/></label><label>{t("Preferred language")}<select value={language} onChange={e => setLanguage(e.target.value as 'en' | 'ta')}><option value="en">{t("English")}</option><option value="ta">{t("\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD")}</option></select></label><ErrorNotice message={error}/>{saved && <p role="status" className="alert">{t("Profile saved.")}</p>}<button className="button primary" disabled={busy}>{t("Save changes")}</button></form></section><section className="panel"><div className="panel-heading"><h3>{t("Active sessions")}</h3></div><ErrorNotice message={sessions.error}/><div className="table-scroll"><table><thead><tr><th>{t("Started")}</th><th>{t("Expires")}</th><th>{t("Action")}</th></tr></thead><tbody>{sessions.data?.map(s => <tr key={s.id}><td>{new Date(s.created_at).toLocaleString()}</td><td>{new Date(s.expires_at).toLocaleString()}</td><td><button className="text-button danger" onClick={async () => { try {
        await api.delete(`/auth/sessions/${s.id}`);
        sessions.reload();
    }
    catch (e) {
        setError(errorMessage(e));
    } }}>{t("Revoke session")}</button></td></tr>)}</tbody></table></div></section></>;
}
