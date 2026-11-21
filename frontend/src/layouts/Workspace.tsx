import LanguageSwitcher from '../components/LanguageSwitcher';
import {t, useLanguage} from '../i18n';
import {NavLink, Navigate, Outlet, Link} from 'react-router-dom';
import {Sprout, LayoutDashboard, MapPinned, FlaskConical, Upload, Settings, LogOut, ShieldCheck, Menu, BookOpen, FileText, X} from 'lucide-react';
import {useState} from 'react';
import {useAuth} from '../contexts/Auth';

const navigation = [
  {to: '/', label: 'Overview', icon: LayoutDashboard},
  {to: '/farms', label: 'My farms', icon: MapPinned},
  {to: '/samples', label: 'Soil samples', icon: FlaskConical},
  {to: '/imports', label: 'Import data', icon: Upload},
  {to: '/reports', label: 'Reports', icon: FileText},
];

export default function Workspace() {
  useLanguage();
  const {user, logout} = useAuth();
  const [open, setOpen] = useState(false);
  if (!user) return <Navigate to="/login" replace/>;

  return <div className={`workspace ${open ? 'nav-open' : ''}`}>
    {open && <button className="sidebar-backdrop" aria-label={t('Close')} onClick={() => setOpen(false)}/>}
    <aside className="sidebar" id="workspace-navigation">
      <div className="sidebar-brand-row">
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-icon"><Sprout/></span>{t('Soil')}<span className="brand-ai">{t('AI')}</span>
        </Link>
        <button className="sidebar-close" aria-label={t('Close')} onClick={() => setOpen(false)}><X size={20}/></button>
      </div>
      <div className="workspace-label">{t('AGRICULTURAL WORKSPACE')}</div>
      <nav aria-label={t('AGRICULTURAL WORKSPACE')} onClick={() => setOpen(false)}>
        {navigation.map(({to, label, icon: Icon}) => <NavLink key={to} to={to} end={to === '/'}>
          <span className="nav-icon"><Icon size={19}/></span><span>{t(label)}</span>
        </NavLink>)}
        {user.roles.includes('ADMIN') && <NavLink to="/admin"><span className="nav-icon"><ShieldCheck size={19}/></span><span>{t('Administration')}</span></NavLink>}
        <div className="sidebar-divider"/>
        <NavLink to="/profile"><span className="nav-icon"><Settings size={19}/></span><span>{t('Settings')}</span></NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="science-note"><BookOpen/><div><strong>{t('Rooted in evidence')}</strong><p>{t('Good decisions start with reliable soil records.')}</p></div></div>
        <button className="sidebar-user" onClick={() => void logout()} title={t('Sign out')} aria-label={`${t('Sign out')} · ${user.name}`}>
          <span className="avatar">{user.name.slice(0, 2).toUpperCase()}</span>
          <span><strong>{user.name}</strong><small>{t(user.roles[0])}</small></span><LogOut size={18}/>
        </button>
      </div>
    </aside>
    <div className="workspace-main">
      <header className="topbar">
        <button className="mobile-menu" aria-label={t('Toggle navigation')} aria-expanded={open} aria-controls="workspace-navigation" onClick={() => setOpen(!open)}><Menu/></button>
        <div className="breadcrumb">{t('Workspace')}<span>/</span><strong>{t('Agricultural intelligence')}</strong></div>
        <div className="topbar-right"><LanguageSwitcher/><span className="workspace-badge"><Sprout size={14}/>{t('SoilAI workspace')}</span><span className="avatar small">{user.name.slice(0, 1).toUpperCase()}</span></div>
      </header>
      <main className="content"><Outlet/></main>
      <footer className="workspace-footer"><span>{t('SoilAI · Intelligent Agricultural Decision Support')}</span><span>{t('Science in the soil. Confidence in every decision.')}</span></footer>
    </div>
  </div>;
}
