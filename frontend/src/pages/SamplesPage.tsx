import {t,useLanguage} from '../i18n';
import { Link } from 'react-router-dom';
import { Plus, FlaskConical, Search } from 'lucide-react';
import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import type { SoilSample, Farm } from '../types/domain';
import { PageHeading, ErrorNotice, Loading, Empty } from '../components/Common';
export default function SamplesPage() {
    useLanguage();
    const { data, error, loading } = useApi<SoilSample[]>('/soil-samples');
    const farms = useApi<Farm[]>('/farms');
    const [search, setSearch] = useState('');
    const filtered = data?.filter(s => s.sample_code.toLowerCase().includes(search.toLowerCase()));
    return <><PageHeading eyebrow={t("FROM SAMPLE TO UNDERSTANDING")} title={t("Soil samples")} description={t("Your soil testing records, organized and ready for analysis.")} action={<Link className="button primary" to="/samples/new"><Plus />{t("New sample")}</Link>}/><ErrorNotice message={error}/><div className="panel"><div className="panel-heading"><h3>{t("Sample history")}</h3><label className="search"><Search size={17}/><input placeholder={t("Search sample ID\u2026")} aria-label={t("Search samples")} value={search} onChange={e => setSearch(e.target.value)}/></label></div>{loading ? <Loading /> : filtered?.length ? <div className="table-scroll"><table><thead><tr><th>{t("Sample ID")}</th><th>{t("Farm")}</th><th>{t("Collection date")}</th><th>{t("Parameters")}</th><th>{t("Status")}</th><th></th></tr></thead><tbody>{filtered.map(s => <tr key={s.id}><td><Link to={`/samples/${s.id}`} className="sample-link"><FlaskConical size={17}/>{s.sample_code}</Link></td><td>{farms.data?.find(f => f.id === s.farm_id)?.name || '—'}</td><td>{s.collected_on}</td><td>{s.measurements.length}{t("recorded")}</td><td><span className={`pill ${s.status === 'draft' ? 'amber' : ''}`}>{t(s.status)}</span></td><td><Link to={`/samples/${s.id}`}>{t("View record")}</Link></td></tr>)}</tbody></table></div> : <Empty title={search ? t('No matching samples') : t('Every insight starts with a sample')}><p>{t("Record a soil test or import laboratory results to begin.")}</p><Link to="/samples/new" className="button">{t("Record your first sample")}</Link></Empty>}</div><div className="info-strip"><FlaskConical /><p>{t("Every measurement keeps its original unit and laboratory method. Results from different test methods are never silently combined.")}</p></div></>;
}
