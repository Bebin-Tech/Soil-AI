from .conftest import register


def test_register_login_logout(client, account):
    data, headers = account
    assert data['user']['roles'] == ['FARMER']
    assert client.get('/api/v1/users/me').status_code == 401
    assert client.get('/api/v1/users/me', headers=headers).status_code == 200
    assert client.post('/api/v1/auth/login', json={'email': data['user']['email'], 'password': 'incorrect'}).status_code == 401
    login = client.post('/api/v1/auth/login', json={'email': data['user']['email'], 'password': 'LongSecurePassword123!'})
    assert login.status_code == 200
    assert client.post('/api/v1/auth/logout', json={'refresh_token': data['refresh_token']}, headers=headers).status_code == 204
    assert client.get('/api/v1/users/me', headers=headers).status_code == 401


def test_rotation_and_reuse_revoke_all_sessions(client, account):
    data, headers = account
    rotated = client.post('/api/v1/auth/refresh', json={'refresh_token': data['refresh_token']})
    assert rotated.status_code == 200
    assert client.get('/api/v1/users/me', headers=headers).status_code == 401
    assert client.post('/api/v1/auth/refresh', json={'refresh_token': data['refresh_token']}).status_code == 401
    assert client.get('/api/v1/users/me', headers={'Authorization': 'Bearer ' + rotated.json()['access_token']}).status_code == 401


def test_no_public_privilege_escalation(client):
    response = client.post('/api/v1/auth/register', json={'name': 'Bad Actor', 'email': 'bad@example.com', 'password': 'LongSecurePassword123!', 'role': 'ADMIN'})
    assert response.status_code == 422


def test_duplicate_email_and_validation(client, account):
    assert client.post('/api/v1/auth/register', json={'name': 'Duplicate', 'email': 'farmer@example.com', 'password': 'LongSecurePassword123!'}).status_code == 409
    assert client.post('/api/v1/auth/register', json={'name': 'x', 'email': 'bad', 'password': 'short'}).status_code == 422
