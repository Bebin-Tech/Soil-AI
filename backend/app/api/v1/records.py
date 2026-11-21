from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from pydantic import Field as PydanticField
from app.database.session import get_db
from app.models.entities import Farm, Field, SoilSample, OfficerReview, Prediction, Measurement, User, UserRole
from app.schemas.auth import StrictModel
from app.schemas.soil import FarmInput, FieldInput, SampleInput, PARAMETERS
from app.core.security import current_user, require, audit
from app.repositories.access import visible_farms, farm_access, sample_access
from app.services.records import record_json, sample_json, save_sample

router = APIRouter()


def commit_unique(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'A record with this identifier already exists')


@router.get('/soil-parameters')
def parameters(user=Depends(current_user)):
    return {k: {'min': v[0], 'max': v[1], 'units': v[2]} for k, v in PARAMETERS.items()}


@router.post('/farms', status_code=201)
def create_farm(data: FarmInput, user=Depends(require('FARMER', 'ADMIN')), db=Depends(get_db)):
    farm = Farm(**data.model_dump(), owner_id=user.id)
    db.add(farm)
    db.flush()
    audit(db, user.id, 'farm.create', farm.id)
    db.commit()
    return record_json(farm)


@router.get('/farms')
def farms(user=Depends(current_user), db=Depends(get_db), offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    return [record_json(f) for f in db.scalars(visible_farms(db, user).order_by(Farm.created_at.desc()).offset(offset).limit(limit))]


@router.get('/farms/{farm_id}')
def get_farm(farm_id: str, user=Depends(current_user), db=Depends(get_db)):
    return record_json(farm_access(db, user, farm_id))


@router.put('/farms/{farm_id}')
def update_farm(farm_id: str, data: FarmInput, user=Depends(current_user), db=Depends(get_db)):
    farm = farm_access(db, user, farm_id, True)
    fields=list(db.scalars(select(Field).where(Field.farm_id==farm_id)))
    if fields and data.area_unit != farm.area_unit:
        raise HTTPException(422,'Farm area unit cannot change while fields exist; field areas retain the original farm unit')
    if any(field.area>data.area for field in fields):
        raise HTTPException(422,'Farm area cannot be smaller than an existing field')
    for key, value in data.model_dump().items():
        setattr(farm, key, value)
    audit(db, user.id, 'farm.update', farm.id)
    db.commit()
    return record_json(farm)


@router.delete('/farms/{farm_id}', status_code=204)
def delete_farm(farm_id: str, user=Depends(current_user), db=Depends(get_db)):
    farm_access(db, user, farm_id, True).deleted = True
    audit(db, user.id, 'farm.delete', farm_id)
    db.commit()


@router.get('/farms/{farm_id}/fields')
def fields(farm_id: str, user=Depends(current_user), db=Depends(get_db)):
    farm_access(db, user, farm_id)
    return [record_json(f) for f in db.scalars(select(Field).where(Field.farm_id == farm_id))]


@router.post('/farms/{farm_id}/fields', status_code=201)
def create_field(farm_id: str, data: FieldInput, user=Depends(current_user), db=Depends(get_db)):
    farm = farm_access(db, user, farm_id, True)
    if data.area > farm.area:
        raise HTTPException(422, 'Field area cannot exceed farm area; use the farm area unit')
    field = Field(farm_id=farm_id, **data.model_dump())
    db.add(field)
    commit_unique(db)
    return record_json(field)


@router.put('/farms/{farm_id}/fields/{field_id}')
def edit_field(farm_id: str, field_id: str, data: FieldInput, user=Depends(current_user), db=Depends(get_db)):
    farm = farm_access(db, user, farm_id, True)
    field = db.get(Field, field_id)
    if not field or field.farm_id != farm.id:
        raise HTTPException(404, 'Field not found')
    if data.area > farm.area:
        raise HTTPException(422, 'Field area cannot exceed farm area')
    for key, value in data.model_dump().items():
        setattr(field, key, value)
    commit_unique(db)
    return record_json(field)


@router.post('/soil-samples', status_code=201)
def create_sample(data: SampleInput, user=Depends(current_user), db=Depends(get_db)):
    farm_access(db, user, data.farm_id, True)
    try:
        sample = save_sample(db, data)
        audit(db, user.id, 'sample.create', sample.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Sample ID already exists in this farm')
    return sample_json(db, sample)


@router.get('/soil-samples')
def samples(user=Depends(current_user), db=Depends(get_db), farm_id: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
    ids = visible_farms(db, user).with_only_columns(Farm.id)
    query = select(SoilSample).where(SoilSample.farm_id.in_(ids))
    if farm_id:
        query = query.where(SoilSample.farm_id == farm_id)
    return [sample_json(db, s) for s in db.scalars(query.order_by(SoilSample.created_at.desc()).offset(offset).limit(limit))]


@router.get('/soil-samples/{sample_id}')
def get_sample(sample_id: str, user=Depends(current_user), db=Depends(get_db)):
    sample = sample_access(db, user, sample_id)
    return {**sample_json(db, sample), 'reviews': [record_json(r) for r in db.scalars(select(OfficerReview).where(OfficerReview.sample_id == sample_id))]}


@router.put('/soil-samples/{sample_id}')
def edit_sample(sample_id: str, data: SampleInput, user=Depends(current_user), db=Depends(get_db)):
    sample = sample_access(db, user, sample_id, True)
    try:
        save_sample(db, data, sample)
        audit(db, user.id, 'sample.update', sample_id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Sample ID already exists in this farm')
    return sample_json(db, sample)


class ReviewInput(StrictModel):
    remarks: str = PydanticField(min_length=5, max_length=5000)


@router.post('/soil-samples/{sample_id}/reviews', status_code=201)
def review(sample_id: str, data: ReviewInput, user=Depends(require('AGRICULTURAL_OFFICER','ADMIN')), db=Depends(get_db)):
    sample_access(db, user, sample_id)
    item = OfficerReview(sample_id=sample_id, officer_id=user.id, remarks=data.remarks)
    db.add(item)
    audit(db, user.id, 'sample.review', sample_id)
    db.commit()
    return record_json(item)
