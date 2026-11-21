import i18next from 'i18next';
import {initReactI18next,useTranslation} from 'react-i18next';
import en from './en.json';
import ta from './ta.json';
i18next.use(initReactI18next).init({resources:{en:{translation:en},ta:{translation:ta}},lng:localStorage.getItem('soilai-language')||'en',fallbackLng:'en',keySeparator:false,showSupportNotice:false,interpolation:{escapeValue:false}});
export const t=(key:string)=>i18next.t(key);
export function useLanguage(){return useTranslation();}
export function changeLanguage(value:string){localStorage.setItem('soilai-language',value);document.documentElement.lang=value;return i18next.changeLanguage(value);}
export default i18next;
