import secrets
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.database.session import get_db
from app.models.entities import User, UserRole, Session, PasswordReset, now
from app.core.security import hasher, verify_password, issue, current_user, user_json, digest, audit, utc
from app.core.config import settings
from app.schemas.auth import Register, Login, Refresh, Profile, Forgot, Reset

router = APIRouter()


@router.post('/auth/register', status_code=201)
def register(data: Register, db=Depends(get_db)):
    user = User(email=data.email.lower(), name=data.name, password_hash=hasher.hash(data.password), language=data.language)
    db.add(user)
    try:
        db.flush()
        db.add(UserRole(user_id=user.id, role='FARMER'))
        audit(db, user.id, 'register')
        result = issue(db, user)
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Account could not be created with this email')


@router.post('/auth/login')
def login(data: Login, db=Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    # Execute Argon2 even for unknown users to reduce account enumeration timing.
    valid = verify_password(user.password_hash if user else hasher.hash(secrets.token_urlsafe(24)), data.password)
    if not user or not valid or not user.active:
        raise HTTPException(401, 'Invalid email or password')
    result = issue(db, user)
    audit(db, user.id, 'login')
    db.commit()
    return result


@router.post('/auth/refresh')
def refresh(data: Refresh, db=Depends(get_db)):
    session = db.scalar(select(Session).where(Session.token_hash == digest(data.refresh_token)).with_for_update())
    if not session:
        raise HTTPException(401, 'Invalid refresh token')
    if session.revoked:
        db.execute(update(Session).where(Session.user_id == session.user_id).values(revoked=True))
        db.commit()
        raise HTTPException(401, 'Refresh token reuse detected; sessions revoked')
    user = db.get(User, session.user_id)
    if utc(session.expires_at) <= now() or not user or not user.active:
        raise HTTPException(401, 'Session expired')
    session.revoked = True
    result = issue(db, user)
    db.commit()
    return result


@router.post('/auth/logout', status_code=204)
def logout(data: Refresh, user=Depends(current_user), db=Depends(get_db)):
    session = db.scalar(select(Session).where(Session.token_hash == digest(data.refresh_token), Session.user_id == user.id))
    if session:
        session.revoked = True
    audit(db, user.id, 'logout')
    db.commit()


@router.get('/users/me')
def me(user=Depends(current_user), db=Depends(get_db)):
    return user_json(db, user)


@router.put('/users/me')
def profile(data: Profile, user=Depends(current_user), db=Depends(get_db)):
    user.name, user.language = data.name, data.language
    audit(db, user.id, 'profile.update')
    db.commit()
    return user_json(db, user)


@router.get('/auth/sessions')
def sessions(user=Depends(current_user), db=Depends(get_db)):
    return [{'id': s.id, 'created_at': s.created_at, 'expires_at': s.expires_at} for s in db.scalars(select(Session).where(Session.user_id == user.id, Session.revoked == False))]


@router.delete('/auth/sessions/{session_id}', status_code=204)
def revoke(session_id: str, user=Depends(current_user), db=Depends(get_db)):
    session = db.get(Session, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(404, 'Session not found')
    session.revoked = True
    db.commit()


def send_reset(email, token):
    cfg = settings()
    msg = EmailMessage()
    msg['Subject'], msg['From'], msg['To'] = 'Reset your SoilAI password', cfg.smtp_from, email
    msg.set_content(f'Reset your password within 30 minutes: {cfg.frontend_url}/reset?token={token}')
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15) as smtp:
        smtp.starttls()
        if cfg.smtp_user:
            smtp.login(cfg.smtp_user, cfg.smtp_password)
        smtp.send_message(msg)


@router.post('/auth/forgot-password')
def forgot(data: Forgot, background: BackgroundTasks, db=Depends(get_db)):
    if not settings().smtp_host:
        raise HTTPException(503, 'Password recovery requires configured SMTP delivery')
    user = db.scalar(select(User).where(User.email == data.email.lower(), User.active == True))
    if user:
        token = secrets.token_urlsafe(48)
        db.add(PasswordReset(user_id=user.id, token_hash=digest(token), expires_at=now() + timedelta(minutes=30)))
        db.commit()
        background.add_task(send_reset, user.email, token)
    return {'message': 'If the account exists, a reset email will be sent'}


@router.post('/auth/reset-password')
def reset(data: Reset, db=Depends(get_db)):
    item = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == digest(data.token)).with_for_update())
    if not item or item.used or utc(item.expires_at) <= now():
        raise HTTPException(400, 'Reset token is invalid or expired')
    db.get(User, item.user_id).password_hash = hasher.hash(data.password)
    db.execute(update(PasswordReset).where(PasswordReset.user_id == item.user_id).values(used=True))
    db.execute(update(Session).where(Session.user_id == item.user_id).values(revoked=True))
    audit(db, item.user_id, 'password.reset')
    db.commit()
    return {'message': 'Password updated; sign in again'}
