import {useState} from 'react';
import {Link} from 'react-router-dom';
import {Download,FileText} from 'lucide-react';
import {t,useLanguage} from '../i18n';
import {useApi} from '../hooks/useApi';
import {api,errorMessage} from '../services/api';
import {PageHeading,Empty,Loading,ErrorNotice} from '../components/Common';
type Report={id:string;sample_id:string;language:string;format:string;created_at:string};
export default function ReportsPage(){
  useLanguage();const {data,error,loading}=useApi<Report[]>('/reports');const [notice,setNotice]=useState(''),[busy,setBusy]=useState('');
  async function download(report:Report){setBusy(report.id);setNotice('');try{const response=await api.get(`/reports/${report.id}/download`,{responseType:'blob'});const url=URL.createObjectURL(response.data);const anchor=document.createElement('a');anchor.href=url;anchor.download=`SoilAI-${report.id}.${report.format}`;anchor.click();URL.revokeObjectURL(url);}catch(e){setNotice(errorMessage(e));}finally{setBusy('');}}
  return <><PageHeading eyebrow={t('YOUR LABORATORY LIBRARY')} title={t('Reports')} description={t('Private snapshots of your soil records in English and Tamil.')}/><ErrorNotice message={error||notice}/><section className="panel"><div className="panel-heading"><h3>{t('Report history')}</h3><FileText size={19}/></div>{loading?<Loading/>:data?.length?<div className="table-scroll"><table><thead><tr><th>{t('Report ID')}</th><th>{t('Created')}</th><th>{t('Language')}</th><th>{t('Format')}</th><th>{t('Sample')}</th><th>{t('Action')}</th></tr></thead><tbody>{data.map(report=><tr key={report.id}><td>{report.id.slice(0,8)}</td><td>{new Date(report.created_at).toLocaleDateString()}</td><td>{report.language==='ta'?'தமிழ்':t('English')}</td><td>{report.format.toUpperCase()}</td><td><Link className="text-button" to={`/samples/${report.sample_id}`}>{t('View record')}</Link></td><td><button className="button" disabled={busy===report.id} onClick={()=>void download(report)}><Download/>{t('Download')}</button></td></tr>)}</tbody></table></div>:<Empty title={t('Your reports will appear here')}><p>{t('Open a soil sample to generate a PDF or Excel laboratory record.')}</p><Link className="button" to="/samples">{t('View soil samples')}</Link></Empty>}</section></>;
}
