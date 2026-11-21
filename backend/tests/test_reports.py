import io
from openpyxl import load_workbook
from pypdf import PdfReader
from .test_records import make_farm,sample_payload
from .conftest import register


def test_reports_english_tamil_excel_and_access(client,account):
    _,headers=account
    farm=make_farm(client,headers)
    sample=client.post('/api/v1/soil-samples',headers=headers,json=sample_payload(farm['id'])).json()
    for language,format in [('en','pdf'),('ta','pdf'),('ta','xlsx')]:
        result=client.post('/api/v1/reports',headers=headers,json={'sample_id':sample['id'],'language':language,'format':format})
        assert result.status_code==201,result.text
        download=client.get(result.json()['download_url'],headers=headers)
        assert download.status_code==200
        if format=='pdf':
            assert download.content.startswith(b'%PDF')
            assert len(PdfReader(io.BytesIO(download.content)).pages)>=1
        else:
            workbook=load_workbook(io.BytesIO(download.content))
            assert workbook.active['B4'].value=='S-001'
        stranger=register(client,f'{language}{format}@example.com')
        assert client.get(result.json()['download_url'],headers={'Authorization':'Bearer '+stranger['access_token']}).status_code==404
