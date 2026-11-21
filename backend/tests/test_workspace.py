from app.models.entities import UserRole, Farm
from .conftest import register
from .test_records import make_farm,sample_payload


def promote(client,user_id,role):
    with client.db_factory() as db:
        db.add(UserRole(user_id=user_id,role=role))
        db.commit()


def test_real_analytics_and_model_gate(client,account):
    _,headers=account
    empty=client.get('/api/v1/dashboard',headers=headers).json()
    assert empty['farms']==0 and empty['samples']==0 and empty['completed_analyses']==0
    farm=make_farm(client,headers)
    sample=client.post('/api/v1/soil-samples',headers=headers,json=sample_payload(farm['id'])).json()
    dashboard=client.get('/api/v1/dashboard',headers=headers).json()
    assert dashboard['farms']==1 and dashboard['samples']==1 and dashboard['completed_analyses']==0
    fertility=client.post('/api/v1/predictions/fertility',headers=headers,json={'sample_id':sample['id']})
    assert fertility.status_code==503
    assert fertility.json()['detail']['code']=='MODEL_NOT_VALIDATED'
    assert client.post('/api/v1/predictions/crops',headers=headers,json={'sample_id':sample['id']}).status_code==422
    assert client.get('/api/v1/admin/users',headers=headers).status_code==403


def test_officer_assignment_and_read_only_boundary(client,account):
    _,headers=account
    farm=make_farm(client,headers)
    officer=register(client,'officer@example.com')
    promote(client,officer['user']['id'],'AGRICULTURAL_OFFICER')
    officer_headers={'Authorization':'Bearer '+officer['access_token']}
    assert client.get('/api/v1/farms',headers=officer_headers).json()==[]
    with client.db_factory() as db:
        db.get(Farm,farm['id']).officer_id=officer['user']['id']
        db.commit()
    assert len(client.get('/api/v1/farms',headers=officer_headers).json())==1
    assert client.post('/api/v1/soil-samples',headers=officer_headers,json=sample_payload(farm['id'])).status_code==403
    sample=client.post('/api/v1/soil-samples',headers=headers,json=sample_payload(farm['id'])).json()
    assert client.post('/api/v1/soil-samples/'+sample['id']+'/reviews',headers=officer_headers,json={'remarks':'Please verify the test method with the laboratory.'}).status_code==201


def test_administrator_permissions_revoke_sessions(client,account):
    data,headers=account
    promote(client,data['user']['id'],'ADMIN')
    other=register(client,'target@example.com')
    assert client.put('/api/v1/admin/users/'+data['user']['id'],headers=headers,json={'roles':['FARMER'],'active':True}).status_code==422
    result=client.put('/api/v1/admin/users/'+other['user']['id'],headers=headers,json={'roles':['AGRICULTURAL_OFFICER'],'active':True})
    assert result.status_code==200,result.text
    assert client.get('/api/v1/users/me',headers={'Authorization':'Bearer '+other['access_token']}).status_code==401
