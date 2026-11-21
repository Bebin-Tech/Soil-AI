import uuid
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from app.database.session import get_db
from app.core.config import settings,ROOT
from app.core.security import current_user,audit
from app.models.entities import Report,Measurement,OfficerReview,User
from app.repositories.access import sample_access,farm_access
from app.schemas.auth import StrictModel
from app.services.reports import generate_pdf,generate_xlsx
from app.services.records import record_json

router=APIRouter()


class ReportInput(StrictModel):
    sample_id:str
    language:Literal['en','ta']='en'
    format:Literal['pdf','xlsx']='pdf'


@router.post('/reports',status_code=201)
def create_report(data:ReportInput,user=Depends(current_user),db=Depends(get_db)):
    sample=sample_access(db,user,data.sample_id)
    farm=farm_access(db,user,sample.farm_id)
    owner=db.get(User,farm.owner_id)
    measurements=list(db.scalars(select(Measurement).where(Measurement.sample_id==sample.id)))
    reviews=list(db.scalars(select(OfficerReview).where(OfficerReview.sample_id==sample.id)))
    directory=(ROOT/settings().storage_dir/'reports').resolve()
    directory.mkdir(parents=True,exist_ok=True)
    report_id=str(uuid.uuid4());path=directory/(report_id+'.'+data.format)
    try:
        if data.format=='pdf':generate_pdf(path,report_id,data.language,sample,farm,owner,measurements,reviews)
        else:generate_xlsx(path,data.language,sample,farm,owner,measurements,reviews)
    except ValueError as error:
        raise HTTPException(503,str(error))
    report=Report(id=report_id,user_id=user.id,sample_id=sample.id,language=data.language,format=data.format,path=path.name)
    db.add(report);audit(db,user.id,'report.generate',report_id);db.commit()
    return {'id':report_id,'download_url':f'/api/v1/reports/{report_id}/download'}


@router.get('/reports')
def reports(user=Depends(current_user),db=Depends(get_db)):
    return [{k:v for k,v in record_json(r).items() if k!='path'} for r in db.scalars(select(Report).where(Report.user_id==user.id).order_by(Report.created_at.desc()).limit(100))]


@router.get('/reports/{report_id}/download')
def download(report_id:str,user=Depends(current_user),db=Depends(get_db)):
    report=db.get(Report,report_id)
    if not report or report.user_id!=user.id:
        raise HTTPException(404,'Report not found')
    sample_access(db,user,report.sample_id)
    directory=(ROOT/settings().storage_dir/'reports').resolve()
    path=(directory/report.path).resolve()
    if path.parent!=directory or not path.is_file():
        raise HTTPException(404,'Report file not found')
    return FileResponse(path,filename=f'SoilAI-{report.id}.{report.format}',media_type='application/pdf' if report.format=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
