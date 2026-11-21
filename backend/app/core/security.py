import hashlib
import secrets
from datetime import timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession
from app.core.config import settings
from app.database.session import get_db
from app.models.entities import User, UserRole, Session, AuditLog, now

hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def audit(db, user_id, action, resource=''):
    db.add(AuditLog(user_id=user_id, action=action, resource=str(resource)))


def verify_password(hash_value, password):
    try:
        return hasher.verify(hash_value, password)
    except (VerificationError, InvalidHashError):
        return False


def roles(db, user):
    return list(db.scalars(select(UserRole.role).where(UserRole.user_id == user.id)))


def user_json(db, user):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'language': user.language, 'roles': roles(db, user), 'active': user.active}


def issue(db, user):
    token = secrets.token_urlsafe(48)
    session = Session(user_id=user.id, token_hash=digest(token), expires_at=now() + timedelta(days=settings().refresh_token_days))
    db.add(session)
    db.flush()
    access = jwt.encode({'sub': user.id, 'sid': session.id, 'type': 'access', 'iat': now(), 'exp': now() + timedelta(minutes=settings().access_token_minutes)}, settings().jwt_secret, algorithm='HS256')
    return {'access_token': access, 'refresh_token': token, 'token_type': 'bearer', 'user': user_json(db, user)}


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: DBSession = Depends(get_db)):
    try:
        if not credentials:
            raise ValueError()
        data = jwt.decode(credentials.credentials, settings().jwt_secret, algorithms=['HS256'], options={'require': ['exp', 'sub', 'sid', 'type']})
        if data['type'] != 'access':
            raise ValueError()
        session = db.get(Session, data['sid'])
        user = db.get(User, data['sub'])
        if not session or session.revoked or utc(session.expires_at) <= now() or session.user_id != data['sub'] or not user or not user.active:
            raise ValueError()
        return user
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})


def require(*allowed):
    def check(user=Depends(current_user), db=Depends(get_db)):
        if not set(roles(db, user)).intersection(allowed):
            raise HTTPException(403, 'Role does not permit this action')
        return user
    return check


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
