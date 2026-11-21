from .conftest import register

FARM = {'name':'Cauvery Farm','state':'Tamil Nadu','district':'Thanjavur','area':5,'area_unit':'acre'}


def make_farm(client, headers):
    r = client.post('/api/v1/farms', json=FARM, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def sample_payload(farm_id):
    values = [('nitrogen',100,'kg/ha'),('phosphorus',20,'kg/ha'),('potassium',150,'kg/ha'),('ph',6.5,'pH'),('ec',0.5,'dS/m'),('organic_carbon',0.6,'%'),('organic_matter',1.1,'%'),('moisture',25,'%'),('temperature',28,'°C')]
    return {'farm_id':farm_id,'sample_code':'S-001','collected_on':'2026-01-01','measurements':[{'parameter':p,'value':v,'unit':u,'method':'Laboratory method recorded'} for p,v,u in values]}


def test_farm_crud_and_isolation(client, account):
    _, headers = account
    farm = make_farm(client, headers)
    other = register(client, 'other@example.com')
    stranger = {'Authorization':'Bearer ' + other['access_token']}
    assert client.get('/api/v1/farms',headers=stranger).json() == []
    assert client.get('/api/v1/farms/'+farm['id'],headers=stranger).status_code == 404
    assert client.put('/api/v1/farms/'+farm['id'],headers=headers,json={**FARM,'area':6}).json()['area'] == 6
    assert client.delete('/api/v1/farms/'+farm['id'],headers=headers).status_code == 204
    assert client.get('/api/v1/farms/'+farm['id'],headers=headers).status_code == 404


def test_sample_validation_drafts_and_duplicates(client, account):
    _, headers = account
    farm = make_farm(client, headers)
    payload = sample_payload(farm['id'])
    r = client.post('/api/v1/soil-samples',headers=headers,json=payload)
    assert r.status_code == 201, r.text
    assert len(r.json()['measurements']) == 9
    assert client.post('/api/v1/soil-samples',headers=headers,json=payload).status_code == 409
    payload['sample_code'] = 'S-002'
    payload['measurements'][3]['value'] = 16
    assert client.post('/api/v1/soil-samples',headers=headers,json=payload).status_code == 422
    payload['measurements'] = []
    assert client.post('/api/v1/soil-samples',headers=headers,json=payload).status_code == 422
    payload['status'] = 'draft'
    assert client.post('/api/v1/soil-samples',headers=headers,json=payload).status_code == 201


def test_units_and_cross_farm_fields(client, account):
    _, headers = account
    first = make_farm(client, headers)
    second = make_farm(client, headers)
    field = client.post('/api/v1/farms/'+first['id']+'/fields',headers=headers,json={'name':'East','area':2}).json()
    payload = sample_payload(second['id'])
    payload['field_id'] = field['id']
    assert client.post('/api/v1/soil-samples',headers=headers,json=payload).status_code == 422
    payload['field_id'] = None
    payload['measurements'][0]['unit'] = 'ppm-unknown'
    assert client.post('/api/v1/soil-samples',headers=headers,json=payload).status_code == 422


def test_field_area_units_are_not_silently_reinterpreted(client,account):
    _,headers=account
    farm=make_farm(client,headers)
    field=client.post('/api/v1/farms/'+farm['id']+'/fields',headers=headers,json={'name':'East','area':2}).json()
    assert client.put('/api/v1/farms/'+farm['id'],headers=headers,json={**FARM,'area_unit':'hectare'}).status_code==422
    assert client.put('/api/v1/farms/'+farm['id'],headers=headers,json={**FARM,'area':1}).status_code==422
    edited=client.put('/api/v1/farms/'+farm['id']+'/fields/'+field['id'],headers=headers,json={'name':'East field','area':3,'soil_type':'loam'})
    assert edited.status_code==200 and edited.json()['area']==3
