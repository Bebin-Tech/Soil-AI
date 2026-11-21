import {t,useLanguage} from '../i18n';
import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Save, FlaskConical } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { api, errorMessage } from '../services/api';
import type { Farm, Field, SoilSample } from '../types/domain';
import { PageHeading, ErrorNotice, Loading } from '../components/Common';
const labels: Record<string, string> = { nitrogen: 'Nitrogen (N)', phosphorus: 'Phosphorus (P)', potassium: 'Potassium (K)', ph: 'Soil pH', ec: 'Electrical conductivity', organic_carbon: 'Organic carbon', organic_matter: 'Organic matter', moisture: 'Soil moisture', temperature: 'Soil temperature', sulphur: 'Sulphur', zinc: 'Zinc', iron: 'Iron', boron: 'Boron', copper: 'Copper', manganese: 'Manganese', calcium: 'Calcium', magnesium: 'Magnesium' };
type Entry = {
    value: string;
    unit: string;
    method: string;
};
export default function SampleForm() {
    useLanguage();
    const { id } = useParams();
    const navigate = useNavigate();
    const farms = useApi<Farm[]>('/farms'), parameters = useApi<Record<string, {
        min: number;
        max: number;
        units: string[];
    }>>('/soil-parameters');
    const [meta, setMeta] = useState({ farm_id: '', field_id: '', sample_code: '', collected_on: new Date().toLocaleDateString('en-CA'), location: '', laboratory: '' });
    const [measurements, setMeasurements] = useState<Record<string, Entry>>({});
    const [climate, setClimate] = useState({ temperature: '', humidity: '', rainfall: '', rainfall_period: 'annual', season: '', irrigation: 'unknown', growth_stage: '' });
    const [fields, setFields] = useState<Field[]>([]), [error, setError] = useState(''), [busy, setBusy] = useState(false), [initializing, setInitializing] = useState(!!id);
    useEffect(() => { if (id)
        api.get<SoilSample>(`/soil-samples/${id}`).then(r => { const s = r.data; setMeta({ farm_id: s.farm_id, field_id: s.field_id || '', sample_code: s.sample_code, collected_on: s.collected_on, location: s.location, laboratory: s.laboratory }); setMeasurements(Object.fromEntries(s.measurements.map(m => [m.parameter, { value: String(m.value), unit: m.unit, method: m.method }]))); setClimate(c => Object.fromEntries(Object.entries(c).map(([k, v]) => [k, String(s.climate[k] ?? v)])) as typeof c); }).catch(e => setError(errorMessage(e))).finally(() => setInitializing(false)); }, [id]);
    useEffect(() => { if (meta.farm_id)
        api.get(`/farms/${meta.farm_id}/fields`).then(r => setFields(r.data)).catch(e => setError(errorMessage(e))); }, [meta.farm_id]);
    function update(parameter: string, key: keyof Entry, value: string) { setMeasurements(prev => ({ ...prev, [parameter]: { ...(prev[parameter] ?? { value: '', unit: parameters.data?.[parameter].units[0] || '', method: '' }), [key]: value } })); }
    async function submit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const status = (e.nativeEvent as SubmitEvent).submitter?.getAttribute('value') === 'draft' ? 'draft' : 'submitted';
        setBusy(true);
        setError('');
        const payload = { ...meta, field_id: meta.field_id || null, status, climate: { ...climate, temperature: climate.temperature === '' ? null : Number(climate.temperature), humidity: climate.humidity === '' ? null : Number(climate.humidity), rainfall: climate.rainfall === '' ? null : Number(climate.rainfall) }, measurements: Object.entries(measurements).filter(([, m]) => m.value !== '').map(([parameter, m]) => ({ parameter, value: Number(m.value), unit: m.unit, method: m.method })) };
        try {
            const r = id ? await api.put(`/soil-samples/${id}`, payload) : await api.post('/soil-samples', payload);
            navigate(`/samples/${r.data.id}`);
        }
        catch (e) {
            setError(errorMessage(e));
        }
        finally {
            setBusy(false);
        }
    }
    if (initializing || parameters.loading)
        return <Loading />;
    return <><PageHeading eyebrow={t("SOIL TESTING WORKSPACE")} title={id ? t('Edit soil sample') : t('Record a soil sample')} description={t("Capture laboratory measurements with their original units and test methods.")} action={<Link className="button" to="/samples">{t("Back to samples")}</Link>}/><ErrorNotice message={error || farms.error || parameters.error}/><form onSubmit={submit}><section className="panel form-panel"><div className="section-title"><span className="section-icon"><FlaskConical /></span><div><h3>{t("Sample information")}</h3><p className="muted">{t("Connect this test to the right farm and field.")}</p></div></div><div className="form-grid thirds"><label>{t("Farm")}<select value={meta.farm_id} required onChange={e => setMeta({ ...meta, farm_id: e.target.value, field_id: '' })}><option value="">{t("Select a farm")}</option>{farms.data?.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}</select></label><label>{t("Field (optional)")}<select value={meta.field_id} onChange={e => setMeta({ ...meta, field_id: e.target.value })}><option value="">{t("Whole farm / unspecified")}</option>{fields.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}</select></label>{(['sample_code', 'collected_on', 'location', 'laboratory'] as const).map(k => <label key={k}>{t(k.replaceAll('_', ' '))}<input type={k === 'collected_on' ? 'date' : 'text'} value={meta[k]} required={['sample_code', 'collected_on'].includes(k)} onChange={e => setMeta({ ...meta, [k]: e.target.value })}/></label>)}</div></section><section className="panel form-panel"><h3>{t("Soil measurements")}</h3><p className="muted">{t("All nine primary parameters are needed to submit. Partial tests can be saved as drafts.")}</p><div className="measurement-grid">{Object.entries(parameters.data || {}).map(([p, definition], index) => <div className="measurement-input" key={p}><h4>{t(labels[p])} {index >= 9 && <small className="muted">{t("optional")}</small>}</h4><div className="value-unit"><label><span className="sr-only">{t(labels[p])}{t("value")}</span><input type="number" step="any" min={definition.min} max={definition.max} value={measurements[p]?.value || ''} onChange={e => update(p, 'value', e.target.value)} placeholder={t("Measured value")}/></label><label><span className="sr-only">{t(labels[p])}{t("unit")}</span><select value={measurements[p]?.unit || definition.units[0]} onChange={e => update(p, 'unit', e.target.value)}>{definition.units.map(u => <option key={u}>{u}</option>)}</select></label></div><label><span className="sr-only">{t(labels[p])}{t("method")}</span><input placeholder={t("Laboratory test method")} value={measurements[p]?.method || ''} onChange={e => update(p, 'method', e.target.value)} required={!!measurements[p]?.value} minLength={2} maxLength={150}/></label></div>)}</div></section><section className="panel form-panel"><h3>{t("Growing conditions")}</h3><p className="muted">{t("Climate and seasonal context are essential for responsible crop recommendations.")}</p><div className="form-grid thirds">{(['temperature', 'humidity', 'rainfall', 'season', 'growth_stage'] as const).map(k => <label key={k}>{k === 'temperature' ? 'Air temperature (°C)' : k === 'humidity' ? 'Humidity (%)' : k === 'rainfall' ? 'Rainfall (mm)' : k.replaceAll('_', ' ')}<input type={['temperature', 'humidity', 'rainfall'].includes(k) ? 'number' : 'text'} step="any" value={climate[k]} onChange={e => setClimate({ ...climate, [k]: e.target.value })}/></label>)}<label>{t("Rainfall period")}<select value={climate.rainfall_period} onChange={e => setClimate({ ...climate, rainfall_period: e.target.value })}>{['annual', 'seasonal', 'monthly'].map(v => <option key={v} value={v}>{t(v)}</option>)}</select></label><label>{t("Irrigation")}<select value={climate.irrigation} onChange={e => setClimate({ ...climate, irrigation: e.target.value })}>{['unknown', 'available', 'limited', 'rainfed'].map(v => <option key={v} value={v}>{t(v)}</option>)}</select></label></div></section><ErrorNotice message={error}/><div className="form-actions"><button className="button" value="draft" disabled={busy}><Save />{t("Save draft")}</button><button className="button primary" value="submitted" disabled={busy}>{t("Submit soil sample")}</button></div></form></>;
}
