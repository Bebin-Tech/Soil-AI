import csv
import io
from openpyxl import Workbook
from .test_records import make_farm, sample_payload


def upload_data(client,headers,farm_id,content,name='soil.csv'):
    return client.post('/api/v1/imports/upload',headers=headers,data={'farm_id':farm_id},files={'file':(name,content,'text/csv')})


def csv_fixture(farm_id):
    payload=sample_payload(farm_id)
    row={'sample_code':'BULK-1','collected_on':'2026-01-01'}
    for m in payload['measurements']:
        row[m['parameter']]=m['value']
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=list(row))
    writer.writeheader();writer.writerow(row)
    mapping={'columns':{k:k for k in row},'units':{m['parameter']:m['unit'] for m in payload['measurements']},'methods':{m['parameter']:m['method'] for m in payload['measurements']}}
    return output.getvalue().encode(),mapping


def test_preview_validate_confirm_and_duplicate(client,account):
    _,headers=account
    farm=make_farm(client,headers)
    content,mapping=csv_fixture(farm['id'])
    uploaded=upload_data(client,headers,farm['id'],content)
    assert uploaded.status_code==201,uploaded.text
    item=uploaded.json()
    assert item['row_count']==1
    url='/api/v1/imports/'+item['id']
    assert client.post(url+'/confirm',headers=headers).status_code==409
    validated=client.post(url+'/validate',headers=headers,json=mapping)
    assert validated.json()['status']=='validated',validated.text
    confirmed=client.post(url+'/confirm',headers=headers)
    assert confirmed.status_code==200,confirmed.text
    assert len(confirmed.json()['imported_ids'])==1
    assert client.post(url+'/confirm',headers=headers).status_code==409
    other=upload_data(client,headers,farm['id'],content).json()
    result=client.post('/api/v1/imports/'+other['id']+'/validate',headers=headers,json=mapping).json()
    assert result['status']=='invalid'
    assert 'Duplicate' in result['errors'][0]['message']


def test_invalid_file_missing_units_large_upload(client,account):
    _,headers=account
    farm=make_farm(client,headers)
    assert upload_data(client,headers,farm['id'],b'a,a\n1,2').status_code==422
    assert upload_data(client,headers,farm['id'],b'hello','bad.exe').status_code==415
    assert upload_data(client,headers,farm['id'],b'x'*(5*1024*1024+1)).status_code==413
    content,mapping=csv_fixture(farm['id'])
    item=upload_data(client,headers,farm['id'],content).json()
    mapping['units']={}
    result=client.post('/api/v1/imports/'+item['id']+'/validate',headers=headers,json=mapping).json()
    assert result['status']=='invalid'
    assert client.get('/api/v1/imports/'+item['id']+'/errors',headers=headers).text.startswith('row,error')


def test_xlsx_content_validation(client,account):
    _,headers=account
    farm=make_farm(client,headers)
    workbook=Workbook();workbook.active.append(['sample_code','collected_on']);workbook.active.append(['X-1','2026-01-01'])
    output=io.BytesIO();workbook.save(output)
    assert upload_data(client,headers,farm['id'],output.getvalue(),'lab.xlsx').status_code==201
    assert upload_data(client,headers,farm['id'],b'not-a-workbook','lab.xlsx').status_code==422
