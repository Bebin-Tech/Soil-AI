import csv
import io
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from pydantic import Field
from app.schemas.auth import StrictModel
from app.schemas.soil import SampleInput
from app.models.entities import DatasetImport, ImportErrorRow
from app.database.session import get_db
from app.core.config import settings
from app.core.security import current_user, audit
from app.repositories.access import farm_access
from app.services.records import save_sample
from app.services.imports import parse_file, validate_rows, safe_csv

router = APIRouter()


class MappingInput(StrictModel):
    columns: dict[str,str] = Field(max_length=100)
    units: dict[str,str] = Field(default_factory=dict, max_length=17)
    methods: dict[str,str] = Field(default_factory=dict, max_length=17)


def access_import(db, user, import_id, lock=False):
    query = select(DatasetImport).where(DatasetImport.id == import_id, DatasetImport.user_id == user.id)
    item = db.scalar(query.with_for_update() if lock else query)
    if not item:
        raise HTTPException(404, 'Import not found')
    farm_access(db, user, item.farm_id, True)
    return item


def import_json(db, item):
    errors = [{'row':e.row_number,'message':e.message} for e in db.scalars(select(ImportErrorRow).where(ImportErrorRow.import_id == item.id))]
    return {'id':item.id,'filename':item.filename,'farm_id':item.farm_id,'status':item.status,'headers':list(item.rows[0]) if item.rows else [],'row_count':len(item.rows),'preview':item.rows[:20],'mapping':item.mapping,'valid_count':len(item.valid_rows),'errors':errors,'imported_ids':item.imported_ids,'created_at':item.created_at}


@router.post('/imports/upload', status_code=201)
async def upload(farm_id: str = Form(...), file: UploadFile = File(...), user=Depends(current_user), db=Depends(get_db)):
    farm_access(db, user, farm_id, True)
    content = await file.read(settings().max_upload_bytes + 1)
    await file.close()
    if len(content) > settings().max_upload_bytes:
        raise HTTPException(413, 'File exceeds the 5 MiB upload limit')
    filename = Path((file.filename or '').replace('\\','/')).name[:200]
    _, rows = parse_file(filename, content)
    item = DatasetImport(user_id=user.id, farm_id=farm_id, filename=filename, rows=rows)
    db.add(item)
    db.flush()
    audit(db, user.id, 'import.upload', item.id)
    db.commit()
    return import_json(db, item)


@router.get('/imports')
def history(user=Depends(current_user), db=Depends(get_db), limit: int = Query(50,ge=1,le=100)):
    items = db.scalars(select(DatasetImport).where(DatasetImport.user_id == user.id).order_by(DatasetImport.created_at.desc()).limit(limit))
    return [{'id':i.id,'filename':i.filename,'status':i.status,'row_count':len(i.rows),'created_at':i.created_at} for i in items]


@router.get('/imports/{import_id}')
def get_import(import_id: str, user=Depends(current_user), db=Depends(get_db)):
    return import_json(db, access_import(db,user,import_id))


@router.post('/imports/{import_id}/validate')
def validate_import(import_id: str, data: MappingInput, user=Depends(current_user), db=Depends(get_db)):
    item = access_import(db,user,import_id,True)
    if item.status == 'confirmed':
        raise HTTPException(409,'This import is already confirmed')
    valid, errors = validate_rows(db,item,data.model_dump())
    item.mapping, item.valid_rows = data.model_dump(), valid
    item.status = 'invalid' if errors else 'validated'
    db.execute(delete(ImportErrorRow).where(ImportErrorRow.import_id == item.id))
    db.add_all([ImportErrorRow(import_id=item.id,row_number=row,message=message) for row,message in errors])
    db.commit()
    return import_json(db,item)


@router.post('/imports/{import_id}/confirm')
def confirm_import(import_id: str, user=Depends(current_user), db=Depends(get_db)):
    item = access_import(db,user,import_id,True)
    if item.status != 'validated':
        raise HTTPException(409,'Validate all rows successfully before confirmation')
    valid, errors = validate_rows(db,item,item.mapping)
    if errors:
        raise HTTPException(409,'Records changed since validation. Validate again before importing.')
    try:
        ids = [save_sample(db,SampleInput.model_validate(row)).id for row in valid]
        item.status, item.imported_ids = 'confirmed', ids
        audit(db,user.id,'import.confirm',item.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Duplicate records detected; import rolled back in full')
    return import_json(db,item)


@router.get('/imports/{import_id}/errors')
def errors_csv(import_id: str,user=Depends(current_user),db=Depends(get_db)):
    item=access_import(db,user,import_id)
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(['row','error'])
    for error in db.scalars(select(ImportErrorRow).where(ImportErrorRow.import_id==item.id)):
        writer.writerow([error.row_number,safe_csv(error.message)])
    return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="import-errors.csv"'})
