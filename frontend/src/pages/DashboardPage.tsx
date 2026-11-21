import {t,useLanguage} from '../i18n';
import { Link } from 'react-router-dom';
import { Plus, MapPinned, FlaskConical, ScanLine, Leaf, Upload, ClipboardList, CalendarDays } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { useState } from 'react';
import { useAuth } from '../contexts/Auth';
import { useApi } from '../hooks/useApi';
import type { SoilSample, Measurement } from '../types/domain';
import { PageHeading, ErrorNotice, Loading, Empty } from '../components/Common';
type Dashboard = {
    farms: number;
    samples: number;
    submitted: number;
    completed_analyses: number;
    fertility_distribution: Record<string, number>;
    model_status: string;
    recent_samples: SoilSample[];
    trends: {
        sample_id: string;
        sample_code: string;
        date: string;
        measurements: Measurement[];
    }[];
    activity: {
        id: string;
        action: string;
        created_at: string;
    }[];
};
export default function DashboardPage() {
    useLanguage();
    const { user } = useAuth();
    const { data, error, loading } = useApi<Dashboard>('/dashboard');
    const [parameter, setParameter] = useState('ph');
    if (loading)
        return <Loading />;
    if (!data)
        return <ErrorNotice message={error}/>;
    // Separate series by unit AND method: never present incompatible measurements as one trend.
    const groups = [...new Set(data.trends.flatMap(t => t.measurements.filter(m => m.parameter === parameter).map(m => `${m.unit} · ${m.method}`)))];
    const selectedGroup = groups[0];
    const chartData = data.trends.map(t => ({ date: t.date, name: t.sample_code, value: t.measurements.find(m => m.parameter === parameter && `${m.unit} · ${m.method}` === selectedGroup)?.value })).filter(p => p.value !== undefined);
    return <><PageHeading eyebrow={t("A LITTLE KNOWLEDGE. A BETTER HARVEST.")} title={`${t('Welcome back,')} ${user?.name.split(' ')[0]}.`} description={t("Let\u2019s take a closer look at what\u2019s growing beneath the surface.")} action={<Link className="button primary" to="/samples/new"><Plus />{t("New soil sample")}</Link>}/><div className="welcome-banner"><div><span className="banner-tag"><Leaf size={13}/>{t("YOUR FIELD INTELLIGENCE")}</span><h3>{t("Healthy soil starts")}<br />{t("with understanding.")}</h3><p>{t("Turn your laboratory records into a clearer picture of your land.")}</p><Link className="button" to="/farms">{t("Explore your farms")}</Link></div><div className="soil-art" aria-hidden="true"><div className="soil-rings"><Leaf /><span className="soil-line"/><span className="soil-layer a"/><span className="soil-layer b"/><span className="soil-layer c"/></div><span className="art-label">{t("ROOTED IN SCIENCE")}</span></div></div><div className="stats-grid">{[{ label: 'Registered farms', value: data.farms, icon: MapPinned, caption: 'Your agricultural footprint' }, { label: 'Soil samples', value: data.samples, icon: FlaskConical, caption: `${data.submitted} ${t('submitted for review')}` }, { label: 'Completed analyses', value: data.completed_analyses, icon: ScanLine, caption: 'Validated model results' }, { label: 'Awaiting analysis', value: data.samples - data.completed_analyses, icon: Leaf, caption: 'Records awaiting model evaluation' }].map(({ label, value, icon: Icon, caption }) => <div className="stat-card" key={label}><div><span>{t(label)}</span><Icon /></div><strong>{value}</strong><small>{t(caption)}</small></div>)}</div><div className="dashboard-grid"><section className="panel"><div className="panel-heading"><div><h3>{t("Soil measurement history")}</h3><p className="muted">{t("Original measurements, grouped by test method")}</p></div><select aria-label={t("Chart parameter")} className="compact-select" value={parameter} onChange={e => setParameter(e.target.value)}>{['ph', 'nitrogen', 'phosphorus', 'potassium', 'organic_carbon', 'ec'].map(p => <option value={p} key={p}>{t(p.replaceAll('_', ' '))}</option>)}</select></div>{chartData.length ? <div className="chart-body"><p className="chart-caption">{selectedGroup}</p><ResponsiveContainer width="100%" height={220}><LineChart data={chartData}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e1e9f4"/><XAxis dataKey="name" fontSize={11} stroke="#71849f" tickLine={false} axisLine={false}/><YAxis fontSize={11} stroke="#71849f" tickLine={false} axisLine={false}/><Tooltip /><Line type="linear" dataKey="value" name={parameter} stroke="#397bd6" strokeWidth={2.5} dot={{ r: 4, fill: '#397bd6' }} connectNulls={false}/></LineChart></ResponsiveContainer>{groups.length > 1 && <small className="muted">{t("Other units/methods are omitted from this series. Inspect sample records for all results.")}</small>}</div> : <Empty title={t("Watch your soil story unfold")}><p>{t("Your recorded measurements will appear here as you add soil samples.")}</p></Empty>}</section><section className="panel fertility-panel"><div className="panel-heading"><h3>{t("Fertility overview")}</h3><Leaf size={18}/></div><div className="fertility-body"><span className="fertility-ring"><strong>{data.completed_analyses}</strong><small>{t("analysed samples")}</small></span><div className="fertility-legend">{Object.entries(data.fertility_distribution).map(([label, count]) => <div key={label}><span className={`legend-dot ${label}`}/><span>{t(label)}{t("fertility")}</span><strong>{count}</strong></div>)}</div><div className="model-note">{data.model_status === 'unavailable' ? t('Awaiting a validated model. No fertility labels are assigned to your records.') : t('Results reflect approved model predictions.')}</div></div></section></div><div className="dashboard-grid lower"><section className="panel"><div className="panel-heading"><h3>{t("Recent soil samples")}</h3><Link className="subtle-link" to="/samples">{t("View all samples")}</Link></div>{data.recent_samples.length ? <div className="table-scroll"><table><thead><tr><th>{t("Sample")}</th><th>{t("Collected")}</th><th>{t("Status")}</th></tr></thead><tbody>{data.recent_samples.map(s => <tr key={s.id}><td><Link className="sample-link" to={`/samples/${s.id}`}><FlaskConical size={16}/>{s.sample_code}</Link></td><td>{s.collected_on}</td><td><span className="pill">{t(s.status)}</span></td></tr>)}</tbody></table></div> : <Empty title={t("A clean slate for your soil records")}><p>{t("Add your first sample to get started.")}</p></Empty>}</section><section className="panel"><div className="panel-heading"><h3>{t("Quick actions")}</h3><ClipboardList size={18}/></div><div className="quick-actions"><Link to="/samples/new"><span><FlaskConical /></span><div><strong>{t("Record a soil test")}</strong><small>{t("Capture a new laboratory result")}</small></div><Plus size={17}/></Link><Link to="/imports"><span><Upload /></span><div><strong>{t("Import your data")}</strong><small>{t("Upload CSV or Excel soil records")}</small></div><Plus size={17}/></Link><Link to="/farms"><span><MapPinned /></span><div><strong>{t("Manage farms & fields")}</strong><small>{t("Keep your land records connected")}</small></div><Plus size={17}/></Link></div><div className="activity-note"><CalendarDays size={16}/><span>{data.activity[0] ? `${t('Last activity')}: ${t(data.activity[0].action.replaceAll('.', ' '))} · ${new Date(data.activity[0].created_at).toLocaleDateString()}` : t('Your workspace activity will appear here.')}</span></div></section></div></>;
}
