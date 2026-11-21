import {t,useLanguage} from '../i18n';
import type { ReactNode } from 'react';
import { Sprout, LoaderCircle } from 'lucide-react';
export function ErrorNotice({ message }: {
    message: string;
}) { useLanguage(); return message ? <div className="alert error" role="alert">{message}</div> : null; }
export function Loading() { useLanguage(); return <div className="loading" role="status"><LoaderCircle className="spin"/>{t("Loading your records\u2026")}</div>; }
export function Empty({ title, children }: {
    title: string;
    children: ReactNode;
}) { useLanguage(); return <div className="empty"><span className="empty-icon"><Sprout /></span><h3>{title}</h3><div className="muted">{children}</div></div>; }
export function PageHeading({ eyebrow, title, description, action }: {
    eyebrow: string;
    title: string;
    description: string;
    action?: ReactNode;
}) { useLanguage(); return <div className="page-heading"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p className="muted">{description}</p></div>{action}</div>; }
