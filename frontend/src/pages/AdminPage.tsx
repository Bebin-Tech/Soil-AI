import {t,useLanguage} from '../i18n';
import { useState } from 'react';
import { useAuth } from '../contexts/Auth';
import { useApi } from '../hooks/useApi';
import { api, errorMessage, type User } from '../services/api';
import type { Farm } from '../types/domain';
import { PageHeading, ErrorNotice, Loading, Empty } from '../components/Common';
export default function AdminPage() { useLanguage(); const { user } = useAuth(); if (!user?.roles.includes('ADMIN'))
    return <ErrorNotice message="Administrator access required"/>; return <Administration />; }
function Administration() {
    useLanguage();
    const analytics = useApi<Record<string, number>>('/admin/analytics'), users = useApi<User[]>('/admin/users'), farms = useApi<Farm[]>('/farms'), logs = useApi<{
        id: string;
        action: string;
        resource: string;
        created_at: string;
    }[]>('/admin/audit-logs'), models = useApi<unknown[]>('/admin/models');
    const [tab, setTab] = useState('Users'), [error, setError] = useState('');
    async function updateUser(target: User, role: string) { setError(''); try {
        await api.put(`/admin/users/${target.id}`, { roles: [role], active: target.active });
        users.reload();
        logs.reload();
    }
    catch (e) {
        setError(errorMessage(e));
    } }
    return <><PageHeading eyebrow={t("SYSTEM GOVERNANCE")} title={t("Administration")} description={t("Manage access, officer assignments and the integrity of your workspace.")}/><ErrorNotice message={error || analytics.error || users.error || farms.error || logs.error || models.error}/><div className="stats-grid">{Object.entries(analytics.data || {}).map(([key, value]) => <div className="stat-card" key={key}><span>{t(key.replaceAll('_', ' '))}</span><strong>{value}</strong></div>)}</div><div className="tabs">{['Users', 'Officer assignments', 'Model registry', 'Audit log'].map(tabName => <button key={tabName} className={tab === tabName ? 'active' : ''} onClick={() => setTab(tabName)}>{t(tabName)}</button>)}</div><section className="panel">{users.loading ? <Loading /> : tab === 'Users' ? <div className="table-scroll"><table><thead><tr><th>{t("Name")}</th><th>{t("Email")}</th><th>{t("Role")}</th><th>{t("Account")}</th></tr></thead><tbody>{users.data?.map(u => <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td><select aria-label={`Role for ${u.name}`} value={u.roles[0]} onChange={e => void updateUser(u, e.target.value)}>{['FARMER', 'AGRICULTURAL_OFFICER', 'ADMIN'].map(r => <option key={r}>{r}</option>)}</select></td><td><button className="text-button" onClick={async () => { try {
        await api.put(`/admin/users/${u.id}`, { roles: u.roles, active: !u.active });
        users.reload();
    }
    catch (e) {
        setError(errorMessage(e));
    } }}>{u.active ? t('Deactivate') : t('Activate')}</button></td></tr>)}</tbody></table></div> : tab === 'Officer assignments' ? <div className="table-scroll"><table><thead><tr><th>{t("Farm")}</th><th>{t("District")}</th><th>{t("Assigned officer")}</th></tr></thead><tbody>{farms.data?.map(f => <tr key={f.id}><td>{f.name}</td><td>{f.district}</td><td><select aria-label={`Officer for ${f.name}`} value={f.officer_id || ''} onChange={async (e) => { try {
        await api.put(`/admin/farms/${f.id}/officer`, { officer_id: e.target.value || null });
        farms.reload();
    }
    catch (e) {
        setError(errorMessage(e));
    } }}><option value="">{t("Unassigned")}</option>{users.data?.filter(u => u.active && u.roles.includes('AGRICULTURAL_OFFICER')).map(u => <option key={u.id} value={u.id}>{u.name}</option>)}</select></td></tr>)}</tbody></table></div> : tab === 'Model registry' ? <Empty title={models.data?.length ? 'Model versions registered' : 'No validated models deployed'}><p>{t("Training and activation are gated on verified data, evaluation and approval. No demonstration predictions are served.")}</p><p>{t("Dataset onboarding and scientific requirements are documented in the project\u2019s dataset guide.")}</p></Empty> : <div className="table-scroll"><table><thead><tr><th>{t("Time")}</th><th>{t("Action")}</th><th>{t("Resource")}</th></tr></thead><tbody>{logs.data?.map(log => <tr key={log.id}><td>{new Date(log.created_at).toLocaleString()}</td><td>{log.action}</td><td>{log.resource || '—'}</td></tr>)}</tbody></table></div>}</section></>;
}
