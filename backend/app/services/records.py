from sqlalchemy import select, delete
from fastapi import HTTPException
from app.models.entities import SoilSample, Measurement, Field


def record_json(record):
    return {column.name: getattr(record, column.name) for column in record.__table__.columns}


def sample_json(db, sample):
    return {**record_json(sample), 'measurements': [record_json(m) for m in db.scalars(select(Measurement).where(Measurement.sample_id == sample.id))]}


def save_sample(db, data, existing=None):
    if data.field_id:
        field = db.get(Field, data.field_id)
        if not field or field.farm_id != data.farm_id:
            raise HTTPException(422, 'Field must belong to the selected farm')
    values = data.model_dump(exclude={'measurements'})
    values['collected_on'] = data.collected_on.isoformat()
    if existing:
        if existing.farm_id != data.farm_id:
            raise HTTPException(422, 'A sample cannot be moved to another farm')
        for key, value in values.items():
            setattr(existing, key, value)
        sample = existing
        db.execute(delete(Measurement).where(Measurement.sample_id == sample.id))
    else:
        sample = SoilSample(**values)
        db.add(sample)
        db.flush()
    db.add_all([Measurement(sample_id=sample.id, **m.model_dump()) for m in data.measurements])
    db.flush()
    return sample
