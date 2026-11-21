import LanguageSwitcher from '../components/LanguageSwitcher';
import {t,useLanguage} from '../i18n';
import { useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Sprout, ShieldCheck, FlaskConical, ChartNoAxesCombined, UserRound, LockKeyhole, Eye, EyeOff } from 'lucide-react';
import './login.css';
import { api, saveSession, errorMessage } from '../services/api';
import { useAuth } from '../contexts/Auth';
const schema = z.object({ email: z.email(), password: z.string().min(1), name: z.string().optional() });
export default function AuthPage() {
    useLanguage();
    const path = useLocation().pathname;
    const registerMode = path === '/register', forgot = path === '/forgot', reset = path === '/reset';
    const { user } = useAuth();
    const [error, setError] = useState(''), [message, setMessage] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(schema), defaultValues: { email: reset ? 'unused@example.com' : '', password: forgot ? 'unused' : '', name: '' } });
    if (user && !reset)
        return <Navigate to="/" replace/>;
    const submit = handleSubmit(async (values) => {
        setError('');
        setMessage('');
        try {
            if (forgot) {
                await api.post('/auth/forgot-password', { email: values.email });
                setMessage('If your account exists, a reset link will be sent to your email.');
            }
            else if (reset) {
                await api.post('/auth/reset-password', { password: values.password, token: new URLSearchParams(location.search).get('token') || '' });
                setMessage('Password updated. You can now sign in.');
            }
            else {
                const result = await api.post(`/auth/${registerMode ? 'register' : 'login'}`, registerMode ? values : { email: values.email, password: values.password });
                saveSession(result.data);
            }
        }
        catch (e) {
            setError(errorMessage(e));
        }
    });
    if (!forgot && !reset) {
        return <main className="login-page">
            <div className="login-language"><LanguageSwitcher /></div>
            <section className="login-card" aria-labelledby="login-title">
                <Link to="/" className="login-logo" aria-label="SoilAI"><Sprout aria-hidden="true" /></Link>
                <header className="login-heading">
                    <h1 id="login-title">SoilAI</h1>
                    <p>{t(registerMode ? 'Create your farmer account to get started.' : 'Sign in to your SoilAI workspace.')}</p>
                </header>
                <form onSubmit={submit}>
                    {registerMode && <label>
                        <span className="sr-only">{t('Full name')}</span>
                        <span className="login-input">
                            <UserRound aria-hidden="true" />
                            <input {...register('name')} required minLength={2} maxLength={100} autoComplete="name" placeholder={t('Full name')} />
                        </span>
                    </label>}
                    <label>
                        <span className="sr-only">{t('Email address')}</span>
                        <span className="login-input">
                            <UserRound aria-hidden="true" />
                            <input type="email" {...register('email')} autoComplete="email" required placeholder={t('Email address')} aria-invalid={!!errors.email} aria-describedby={errors.email ? 'login-email-error' : undefined} />
                        </span>
                        {errors.email && <small id="login-email-error" className="error">{errors.email.message}</small>}
                    </label>
                    <label>
                        <span className="sr-only">{t('Password')}</span>
                        <span className="login-input">
                            <LockKeyhole aria-hidden="true" />
                            <input type={showPassword ? 'text' : 'password'} {...register('password')} minLength={registerMode ? 12 : 1} maxLength={128} required autoComplete={registerMode ? 'new-password' : 'current-password'} placeholder={t('Password')} aria-label={t('Password')} aria-describedby={registerMode ? 'register-password-hint' : undefined} />
                            <button type="button" className="login-password-toggle" aria-label={t(showPassword ? 'Hide password' : 'Show password')} aria-pressed={showPassword} onClick={() => setShowPassword(value => !value)}>{showPassword ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}</button>
                        </span>
                        {registerMode && <small id="register-password-hint" className="muted">{t('Use at least 12 characters.')}</small>}
                    </label>
                    {error && <div role="alert" className="alert error">{error}</div>}
                    <button className="login-submit" disabled={isSubmitting}>{isSubmitting ? t('Please wait…') : t(registerMode ? 'Create account' : 'Sign in')}</button>
                </form>
                {!registerMode && <Link className="login-forgot" to="/forgot">{t('Forgot password?')}</Link>}
                {registerMode && <p className="login-account-prompt">{t('Already have an account?')}</p>}
                <Link className="login-create" to={registerMode ? '/login' : '/register'}>{t(registerMode ? 'Sign in' : 'Create an account')}</Link>
                <p className="login-caption">{t('Built for farmers. Informed by science.')}</p>
            </section>
        </main>;
    }
    return <div className="auth-layout"><aside className="auth-story"><Link to="/" className="brand"><span className="brand-icon"><Sprout /></span>{t("Soil")}<span className="brand-ai">{t("AI")}</span></Link><div><span className="eyebrow light">{t("CULTIVATE WITH CONFIDENCE")}</span><h1>{t("Better soil.")}<br />{t("Better decisions.")}<br /><em>{t("Better tomorrow.")}</em></h1><p>{t("Your farm\u2019s story begins beneath the surface. Bring soil records, field insights and agricultural expertise together.")}</p><div className="story-features"><span><FlaskConical />{t("Soil records you can trust")}</span><span><ChartNoAxesCombined />{t("Evidence-led decisions")}</span><span><ShieldCheck />{t("Your data, protected")}</span></div></div><small>{t("INTELLIGENT AGRICULTURE, ROOTED IN SCIENCE.")}</small></aside><main className="auth-main"><LanguageSwitcher/><div className="auth-card"><span className="eyebrow">{t("YOUR AGRICULTURAL WORKSPACE")}</span><h2>{registerMode ? t("Start growing smarter.") : forgot ? t("Recover your account.") : reset ? t("Choose a new password.") : t("Welcome back.")}</h2><p className="muted">{registerMode ? t("Create your farmer account to get started.") : t("Sign in to your SoilAI workspace.")}</p><form onSubmit={submit}>
    {registerMode && <label>{t("Full name")}<input {...register('name')} required minLength={2} maxLength={100} autoComplete="name"/></label>}
    {!reset && <label>{t("Email address")}<input type="email" {...register('email')} autoComplete="email" required/>{errors.email && <small className="error">{errors.email.message}</small>}</label>}
    {!forgot && <label>{t("Password")}<input type="password" {...register('password')} minLength={registerMode || reset ? 12 : 1} maxLength={128} required autoComplete={registerMode || reset ? 'new-password' : 'current-password'}/>{registerMode && <small className="muted">{t("Use at least 12 characters.")}</small>}</label>}
    {forgot && <input type="hidden" {...register('password')} value="unused"/>}{reset && <input type="hidden" {...register('email')} value="unused@example.com"/>}
    {error && <div role="alert" className="alert error">{error}</div>}{message && <div role="status" className="alert">{message}</div>}
    <button className="button primary full" disabled={isSubmitting}>{isSubmitting ? t("Please wait…") : registerMode ? t("Create account") : forgot ? t("Send reset link") : reset ? t("Update password") : t("Sign in")}</button>
  </form>{!registerMode && !forgot && !reset && <Link className="subtle-link" to="/forgot">{t("Forgot password?")}</Link>}<p className="auth-footer">{registerMode ? t("Already have an account?") : t("New to SoilAI?")} <Link to={registerMode ? '/login' : '/register'}>{registerMode ? t("Sign in") : t("Create an account")}</Link></p></div><small className="muted">{t("Built for farmers. Informed by science.")}</small></main></div>;
}
