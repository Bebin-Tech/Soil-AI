import {useLanguage,changeLanguage} from '../i18n';
export default function LanguageSwitcher(){const {i18n}=useLanguage();return <select className="language-switcher" value={i18n.language} aria-label="Language / மொழி" onChange={e=>void changeLanguage(e.target.value)}><option value="en">English</option><option value="ta">தமிழ்</option></select>;}
