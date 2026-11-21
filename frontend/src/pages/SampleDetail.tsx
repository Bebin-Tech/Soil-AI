import {t,useLanguage} from '../i18n';
import { Link, useParams } from 'react-router-dom';
import { Pencil, FlaskConical } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import type { SoilSample } from '../types/domain';
import { PageHeading, Loading, ErrorNotice } from '../components/Common';
import { useState, type FormEvent } from 'react';
import { api, errorMessage } from '../services/api';
import { useAuth } from '../contexts/Auth';
export default function SampleDetail() {
    useLanguage();
    const { id } = useParams();
    const { data, error, loading, reload } = useApi<SoilSample>(`/soil-samples/${id}`);
    const { user } = useAuth();
    const [notice, setNotice] = useState(''), [busy, setBusy] = useState(false), [language, setLanguage] = useState('en');
    async function download(format: 'pdf' | 'xlsx') {
        setBusy(true);
        setNotice('');
        try {
            const report = await api.post('/reports', { sample_id: id, format, language });
            const r = await api.get(report.data.download_url.replace('/api/v1', ''), { responseType: 'blob' });
            const url = URL.createObjectURL(r.data);
            const a = document.createElement('a');
            a.href = url;
            a.download = `SoilAI-${id}.${format}`;
            a.click();
            URL.revokeObjectURL(url);
        }
        catch (e) {
            setNotice(errorMessage(e));
        }
        finally {
            setBusy(false);
        }
    }
    async function review(e: FormEvent<HTMLFormElement>) { e.preventDefault(); const target = e.currentTarget; const remarks = new FormData(target).get('remarks'); setBusy(true); try {
        await api.post(`/soil-samples/${id}/reviews`, { remarks });
        target.reset();
        reload();
    }
    catch (e) {
        setNotice(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    if (loading)
        return <Loading />;
    if (!data)
        return <ErrorNotice message={error}/>;
    return <><PageHeading eyebrow={t("SOIL SAMPLE RECORD")} title={data.sample_code} description={`${t('Collected')} ${data.collected_on} · ${data.laboratory || t('Laboratory not recorded')}`} action={<Link className="button" to={`/samples/${id}/edit`}><Pencil />{t("Edit sample")}</Link>}/><ErrorNotice message={notice}/><div className="report-toolbar"><label>{t("Report language")}<select value={language} onChange={e => setLanguage(e.target.value)}><option value="en">{t("English")}</option><option value="ta">{t("\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD")}</option></select></label><button className="button" disabled={busy} onClick={() => void download('pdf')}>{t("Download PDF")}</button><button className="button" disabled={busy} onClick={() => void download('xlsx')}>{t("Export Excel")}</button><button className="button" onClick={() => window.print()}>{t("Print record")}</button></div><div className="info-strip"><FlaskConical /><p>{t("Measurements are laboratory records. Scientific classifications and model predictions will appear only when a compatible validated model is approved.")}</p></div><section className="panel"><div className="panel-heading"><h3>{t("Recorded parameters")}</h3><span className="pill">{t(data.status)}</span></div><div className="table-scroll"><table><thead><tr><th>{t("Parameter")}</th><th>{t("Measured value")}</th><th>{t("Unit")}</th><th>{t("Laboratory method")}</th></tr></thead><tbody>{data.measurements.map(m => <tr key={m.parameter}><td>{t(m.parameter.replaceAll('_', ' '))}</td><td><strong>{m.value}</strong></td><td>{m.unit}</td><td>{m.method}</td></tr>)}</tbody></table></div></section>{data.reviews?.length ? <section className="panel form-panel"><h3>{t("Officer remarks")}</h3>{data.reviews.map(r => <blockquote key={r.id}>{r.remarks}<small>{new Date(r.created_at).toLocaleDateString()}</small></blockquote>)}</section> : null}{user?.roles.some(r => ['AGRICULTURAL_OFFICER', 'ADMIN'].includes(r)) && <section className="panel form-panel"><h3>{t("Add expert remarks")}</h3><form onSubmit={review}><label>{t("Remarks")}<textarea name="remarks" minLength={5} maxLength={5000} required/></label><button className="button primary" disabled={busy}>{t("Save remarks")}</button></form></section>}</>;
}
