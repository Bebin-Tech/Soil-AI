from datetime import timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.security import SecurityMiddleware
from app.models.entities import PasswordReset,now
from app.core.security import digest


def test_rate_limit_does_not_trust_spoofed_forwarded_headers():
    application=FastAPI();application.add_middleware(SecurityMiddleware)
    @application.post('/api/v1/auth/test')
    def endpoint():return {'ok':True}
    with TestClient(application) as client:
        for index in range(30):
            assert client.post('/api/v1/auth/test',headers={'X-Forwarded-For':f'10.0.0.{index}'}).status_code==200
        result=client.post('/api/v1/auth/test')
        assert result.status_code==429 and result.headers['Retry-After']=='60'


def test_password_reset_one_use_and_session_revocation(client,account):
    data,headers=account
    token='qa-reset-token-only-'+'a'*48
    with client.db_factory() as db:
        db.add(PasswordReset(user_id=data['user']['id'],token_hash=digest(token),expires_at=now()+timedelta(minutes=30)))
        db.commit()
    result=client.post('/api/v1/auth/reset-password',json={'token':token,'password':'AnotherLongPassword456!'})
    assert result.status_code==200,result.text
    assert client.get('/api/v1/users/me',headers=headers).status_code==401
    assert client.post('/api/v1/auth/reset-password',json={'token':token,'password':'AnotherLongPassword456!'}).status_code==400
    assert client.post('/api/v1/auth/login',json={'email':data['user']['email'],'password':'AnotherLongPassword456!'}).status_code==200
