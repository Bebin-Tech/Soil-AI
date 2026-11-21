"""Generate clearly marked QA fixtures, never application database records."""
import sys
from pathlib import Path
from types import SimpleNamespace as Obj
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.services.reports import generate_pdf

root=Path(__file__).resolve().parents[1]/'tmp/pdfs'
root.mkdir(parents=True,exist_ok=True)
sample=Obj(sample_code='QA-ONLY-001',collected_on='2026-11-21',laboratory='Layout verification fixture',status='submitted')
farm=Obj(name='QA layout fixture',village='',district='Thanjavur',state='Tamil Nadu')
owner=Obj(name='Report rendering test')
values=[('nitrogen',100,'kg/ha','Alkaline permanganate'),('phosphorus',20,'kg/ha','Olsen extraction'),('potassium',150,'kg/ha','Ammonium acetate'),('ph',6.5,'pH','1:2.5 soil-water suspension'),('ec',.5,'dS/m','1:2 soil-water extract'),('organic_carbon',.6,'%','Walkley-Black'),('organic_matter',1.1,'%','Laboratory method'),('moisture',25,'%','Gravimetric'),('temperature',28,'°C','Probe')]
measurements=[Obj(parameter=p,value=v,unit=u,method=m) for p,v,u,m in values]
for language in ['en','ta']:
    generate_pdf(root/f'qa-{language}.pdf','QA-LAYOUT-ONLY',language,sample,farm,owner,measurements,[])
print('Created QA PDF fixtures in tmp/pdfs')
