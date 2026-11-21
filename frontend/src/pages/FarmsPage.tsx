import {t,useLanguage} from '../i18n';
import { useState, type FormEvent } from 'react';
import { MapPin, Plus, Pencil, Trash2, Sprout } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { api, errorMessage } from '../services/api';
import { useAuth } from '../contexts/Auth';
import type { Farm, Field } from '../types/domain';
import { Empty, ErrorNotice, Loading, PageHeading } from '../components/Common';
const blank = { name: '', state: 'Tamil Nadu', district: '', village: '', location: '', survey_number: '', area: 1, area_unit: 'acre' };
export default function FarmsPage() {
    useLanguage();
    const { data, error, loading, reload } = useApi<Farm[]>('/farms');
    const { user } = useAuth();
    const [editing, setEditing] = useState<string | null>(null), [form, setForm] = useState(blank), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false), [fieldsFarm, setFieldsFarm] = useState<Farm | null>(null);
    const canWrite = (farm: Farm) => farm.owner_id === user?.id || user?.roles.includes('ADMIN');
    async function submit(e: FormEvent) {
        e.preventDefault();
        setNotice('');
        setBusy(true);
        try {
            if (editing === 'new')
                await api.post('/farms', form);
            else
                await api.put(`/farms/${editing}`, form);
            setEditing(null);
            reload();
        }
        catch (e) {
            setNotice(errorMessage(e));
        }
        finally {
            setBusy(false);
        }
    }
    async function remove(farm: Farm) {
        if (!confirm(`Archive ${farm.name}? Its history will be retained.`))
            return;
        try {
            await api.delete(`/farms/${farm.id}`);
            reload();
        }
        catch (e) {
            setNotice(errorMessage(e));
        }
    }
    return <><PageHeading eyebrow={t("YOUR LAND, CONNECTED")} title={t("My farms")} description={t("A clear view of every farm and field you manage.")} action={user?.roles.some(r => ['FARMER', 'ADMIN'].includes(r)) && <button className="button primary" onClick={() => { setForm(blank); setEditing('new'); }}><Plus />{t("Add farm")}</button>}/><ErrorNotice message={error || notice}/>{loading ? <Loading /> : data?.length ? <div className="farm-grid">{data.map(farm => <article className="panel farm-card" key={farm.id}><div className="farm-illustration"><Sprout /><span>{farm.area} {farm.area_unit}</span></div><div className="farm-card-body"><div className="card-title"><h3>{farm.name}</h3><span className="pill">{t("Active farm")}</span></div><p className="muted location"><MapPin size={15}/>{[farm.village, farm.district, farm.state].filter(Boolean).join(', ')}</p><div className="farm-meta"><span>{t("Survey number")}<strong>{farm.survey_number || t('Not recorded')}</strong></span><span>{t("Area")}<strong>{farm.area} {farm.area_unit}</strong></span></div><div className="card-actions"><button className="button" onClick={() => setFieldsFarm(farm)}>{t("Manage fields")}</button>{canWrite(farm) && <><button className="icon-button" title={t("Edit farm")} onClick={() => { const { name, state, district, village, location, survey_number, area, area_unit } = farm; setForm({ name, state, district, village, location, survey_number, area, area_unit }); setEditing(farm.id); }}><Pencil size={17}/></button><button className="icon-button danger" title={t("Archive farm")} onClick={() => void remove(farm)}><Trash2 size={17}/></button></>}</div></div></article>)}</div> : <div className="panel"><Empty title={t("Your farm journey starts here")}><p>{t("Add your first farm to organize fields and soil samples.")}</p></Empty></div>}
  {editing && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="farm-title"><h2 id="farm-title">{editing === 'new' ? t('Add farm') : t('Edit farm')}</h2><form onSubmit={submit}><div className="form-grid">{(['name', 'state', 'district', 'village', 'location', 'survey_number'] as const).map(key => <label key={key}>{t(key.replaceAll('_', ' '))}<input value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} required={['name', 'state', 'district'].includes(key)} maxLength={key === 'location' ? 250 : 100}/></label>)}<label>{t("Farm area")}<input type="number" value={form.area} step="any" min="0.0001" required onChange={e => setForm({ ...form, area: Number(e.target.value) })}/></label><label>{t("Area unit")}<select value={form.area_unit} onChange={e => setForm({ ...form, area_unit: e.target.value })}>{['acre', 'hectare', 'cent', 'm²'].map(u => <option key={u}>{u}</option>)}</select></label></div><ErrorNotice message={notice}/><div className="form-actions"><button type="button" className="button" onClick={() => setEditing(null)}>{t("Cancel")}</button><button className="button primary" disabled={busy}>{t("Save farm")}</button></div></form></section></div>}
  {fieldsFarm && <Fields farm={fieldsFarm} canWrite={!!canWrite(fieldsFarm)} close={() => setFieldsFarm(null)}/>}
  </>;
}
function Fields({ farm, canWrite, close }: {
    farm: Farm;
    canWrite: boolean;
    close: () => void;
}) {
    useLanguage();
    const { data, error, reload } = useApi<Field[]>(`/farms/${farm.id}/fields`);
    const [notice, setNotice] = useState(''), [busy, setBusy] = useState(false);
    async function submit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const target = e.currentTarget, form = new FormData(target);
        setBusy(true);
        try {
            await api.post(`/farms/${farm.id}/fields`, { name: form.get('name'), area: Number(form.get('area')), soil_type: form.get('soil_type') });
            target.reset();
            reload();
        }
        catch (e) {
            setNotice(errorMessage(e));
        }
        finally {
            setBusy(false);
        }
    }
    return <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="fields-title"><h2 id="fields-title">{farm.name}{t("\u00B7 fields")}</h2><ErrorNotice message={error || notice}/><div className="field-list">{data?.length ? data.map(f => <div key={f.id}><strong>{f.name}</strong><span>{f.area} {farm.area_unit}{t("\u00B7")}{f.soil_type || t('Soil type not recorded')}</span></div>) : <p className="muted">{t("No fields registered yet.")}</p>}</div>{canWrite && <form onSubmit={submit}><label>{t("Field name")}<input name="name" required maxLength={100}/></label><div className="form-grid"><label>{t("Area (")}{farm.area_unit}{t(")")}<input name="area" type="number" min="0.0001" max={farm.area} step="any" required/></label><label>{t("Soil type")}<input name="soil_type" maxLength={100}/></label></div><button className="button primary" disabled={busy}>{t("Add field")}</button></form>}<button className="button full" onClick={close}>{t("Close")}</button></section></div>;
}
