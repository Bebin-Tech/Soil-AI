import {t,useLanguage} from '../i18n';
import { useState, type FormEvent } from 'react';
import { Upload, CheckCircle2, FileSpreadsheet, Download, Check } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { api, errorMessage } from '../services/api';
import type { Farm } from '../types/domain';
import { PageHeading, ErrorNotice, Empty } from '../components/Common';
type ImportRecord = {
    id: string;
    filename: string;
    status: string;
    headers: string[];
    row_count: number;
    preview: Record<string, string>[];
    valid_count: number;
    errors: {
        row: number;
        message: string;
    }[];
    imported_ids: string[];
};
type Specification = {
    columns: Record<string, string>;
    units: Record<string, string>;
    methods: Record<string, string>;
};
export default function ImportsPage() {
    useLanguage();
    const farms = useApi<Farm[]>('/farms'), parameters = useApi<Record<string, {
        units: string[];
    }>>('/soil-parameters'), history = useApi<ImportRecord[]>('/imports');
    const [farm, setFarm] = useState(''), [item, setItem] = useState<ImportRecord | null>(null), [mapping, setMapping] = useState<Specification>({ columns: {}, units: {}, methods: {} }), [error, setError] = useState(''), [busy, setBusy] = useState(false);
    async function upload(e: FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError('');
        setBusy(true);
        const data = new FormData(e.currentTarget);
        data.set('farm_id', farm);
        try {
            const r = await api.post<ImportRecord>('/imports/upload', data);
            setItem(r.data);
            setMapping({ columns: Object.fromEntries(r.data.headers.map(h => [h, h])), units: {}, methods: {} });
            history.reload();
        }
        catch (e) {
            setError(errorMessage(e));
        }
        finally {
            setBusy(false);
        }
    }
    function map(target: string, source: string) { setMapping(m => ({ ...m, columns: { ...m.columns, [target]: source } })); setItem(i => i ? { ...i, status: 'uploaded', valid_count: 0, errors: [] } : null); }
    async function action(kind: 'validate' | 'confirm') { if (!item)
        return; setBusy(true); setError(''); try {
        const clean = { ...mapping, columns: Object.fromEntries(Object.entries(mapping.columns).filter(([key, value]) => value && (['sample_code', 'collected_on', 'location', 'laboratory', ...Object.keys(parameters.data || {}), ...Object.keys(parameters.data || {}).flatMap(k => [k + '_unit', k + '_method'])].includes(key)))) };
        setItem((await api.post(`/imports/${item.id}/${kind}`, kind === 'validate' ? clean : undefined)).data);
        history.reload();
    }
    catch (e) {
        setError(errorMessage(e));
    }
    finally {
        setBusy(false);
    } }
    async function downloadErrors() { if (!item)
        return; try {
        const r = await api.get(`/imports/${item.id}/errors`, { responseType: 'blob' });
        const url = URL.createObjectURL(r.data);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'import-errors.csv';
        a.click();
        URL.revokeObjectURL(url);
    }
    catch (e) {
        setError(errorMessage(e));
    } }
    return <><PageHeading eyebrow={t("LESS DATA ENTRY, MORE CLARITY")} title={t("Import laboratory data")} description={t("Bring your CSV and Excel records into one reliable workspace.")}/><div className="import-steps">{['Upload file', 'Map columns', 'Validate rows', 'Confirm import'].map((s, index) => <span className={item && (index === 0 || index === 1 || (index === 2 && ['validated', 'confirmed'].includes(item.status)) || (index === 3 && item.status === 'confirmed')) ? 'done' : ''} key={s}><Check size={14}/>{s}</span>)}</div><ErrorNotice message={error || farms.error || parameters.error}/><section className="panel form-panel"><div className="section-title"><span className="section-icon"><Upload /></span><div><h3>{t("Upload your soil test results")}</h3><p className="muted">{t("UTF-8 CSV or a single-sheet XLSX \u00B7 up to 5 MiB \u00B7 5,000 rows")}</p></div></div><form onSubmit={upload}><div className="form-grid"><label>{t("Destination farm")}<select required value={farm} onChange={e => setFarm(e.target.value)}><option value="">{t("Select a farm")}</option>{farms.data?.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}</select></label><label>{t("Laboratory file")}<input type="file" name="file" required accept=".csv,.xlsx"/></label></div><div className="form-actions"><button className="button primary" disabled={busy}><Upload />{t("Upload & preview")}</button></div></form></section>
  {item && item.status !== 'confirmed' && <><section className="panel"><div className="panel-heading"><h3>{item.filename}</h3><span className="pill">{item.row_count}{t("rows \u00B7 first 20 previewed")}</span></div><div className="table-scroll"><table><thead><tr>{item.headers.map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{item.preview.map((r, index) => <tr key={index}>{item.headers.map(h => <td key={h}>{r[h] || <span className="error">{t("Missing")}</span>}</td>)}</tr>)}</tbody></table></div></section><section className="panel form-panel"><h3>{t("Column mapping & measurement context")}</h3><p className="muted">{t("Map each required parameter. Select units and enter the laboratory method only when they apply to every row. Alternatively map per-row unit and method columns.")}</p><div className="form-grid">{['sample_code', 'collected_on', 'location', 'laboratory'].map(k => <label key={k}>{t(k.replaceAll('_', ' '))}<select value={mapping.columns[k] || ''} onChange={e => map(k, e.target.value)}><option value="">{t("Not mapped")}</option>{item.headers.map(h => <option key={h}>{h}</option>)}</select></label>)}</div><div className="mapping-list">{Object.entries(parameters.data || {}).map(([p, definition]) => <div key={p}><strong>{t(p.replaceAll('_', ' '))}</strong><label>{t("Value column")}<select value={mapping.columns[p] || ''} onChange={e => map(p, e.target.value)}><option value="">{t("Not mapped")}</option>{item.headers.map(h => <option key={h}>{h}</option>)}</select></label><label>{t("Unit")}<select value={mapping.units[p] || ''} onChange={e => { setMapping(m => ({ ...m, units: { ...m.units, [p]: e.target.value } })); setItem({ ...item, status: 'uploaded' }); }}><option value="">{t("Select explicitly")}</option>{definition.units.map(u => <option key={u}>{u}</option>)}</select></label><label>{t("Method")}<input placeholder={t("Laboratory method")} value={mapping.methods[p] || ''} onChange={e => { setMapping(m => ({ ...m, methods: { ...m.methods, [p]: e.target.value } })); setItem({ ...item, status: 'uploaded' }); }}/></label><details><summary>{t("Per-row unit / method columns")}</summary>{['unit', 'method'].map(s => <label key={s}>{s}<select value={mapping.columns[p + '_' + s] || ''} onChange={e => map(p + '_' + s, e.target.value)}><option value="">{t("Use value above")}</option>{item.headers.map(h => <option key={h}>{h}</option>)}</select></label>)}</details></div>)}</div><div className="form-actions"><button className="button" disabled={busy} onClick={() => void action('validate')}>{t("Validate all rows")}</button><button className="button primary" disabled={busy || item.status !== 'validated'} onClick={() => void action('confirm')}><CheckCircle2 />{t("Confirm")}{item.valid_count}{t("samples")}</button></div></section>{item.status === 'validated' && <div className="alert">{t("All")}{item.valid_count}{t("rows passed validation. Confirm to save these records to your farm.")}</div>}{item.errors.length > 0 && <section className="panel form-panel"><div className="card-title"><h3 className="error">{item.errors.length}{t("invalid rows")}</h3><button className="button" onClick={() => void downloadErrors()}><Download />{t("Error report")}</button></div>{item.errors.slice(0, 20).map((e, i) => <pre className="import-error" key={i}>{t("Row")}{e.row}{t(":")}{e.message}</pre>)}</section>}</>}
  {item?.status === 'confirmed' && <div className="alert"><CheckCircle2 size={20}/> {item.imported_ids.length}{t("soil samples imported successfully.")}<Link to="/samples">{t("View soil samples")}</Link></div>}
  <section className="panel"><div className="panel-heading"><h3>{t("Import history")}</h3><FileSpreadsheet size={18}/></div>{history.data?.length ? <div className="table-scroll"><table><thead><tr><th>{t("File")}</th><th>{t("Rows")}</th><th>{t("Status")}</th></tr></thead><tbody>{history.data.map(i => <tr key={i.id}><td><button className="text-button" onClick={async () => { try {
        const r = await api.get(`/imports/${i.id}`);
        setItem(r.data);
        setMapping(r.data.mapping?.columns ? r.data.mapping : { columns: {}, units: {}, methods: {} });
    }
    catch (e) {
        setError(errorMessage(e));
    } }}>{i.filename}</button></td><td>{i.row_count}</td><td><span className="pill">{i.status}</span></td></tr>)}</tbody></table></div> : <Empty title={t("Your imports will appear here")}><p>{t("Every upload is validated before any soil record is saved.")}</p></Empty>}</section></>;
}
