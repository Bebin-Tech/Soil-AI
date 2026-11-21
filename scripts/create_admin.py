"""Run with the backend as working directory; no default credentials."""
import getpass
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.entities import User, UserRole
from app.core.security import hasher, audit
from app.schemas.auth import Register

if __name__ == '__main__':
    data = Register(name=input('Administrator name: '), email=input('Email: '), password=getpass.getpass('Password (12+ characters): '))
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == data.email.lower())):
            raise SystemExit('Email already exists. Use an existing administrator to manage roles.')
        user = User(name=data.name, email=data.email.lower(), password_hash=hasher.hash(data.password))
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role='ADMIN'))
        audit(db, user.id, 'admin.bootstrap')
        db.commit()
        print('Administrator created.')
