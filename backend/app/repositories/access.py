from fastapi import HTTPException
from sqlalchemy import select
from app.models.entities import Farm, SoilSample
from app.core.security import roles


def visible_farms(db, user):
    allowed = roles(db, user)
    query = select(Farm).where(Farm.deleted == False)
    if 'ADMIN' in allowed:
        return query
    if 'AGRICULTURAL_OFFICER' in allowed:
        return query.where((Farm.owner_id == user.id) | (Farm.officer_id == user.id))
    return query.where(Farm.owner_id == user.id)


def farm_access(db, user, farm_id, write=False):
    farm = db.scalar(visible_farms(db, user).where(Farm.id == farm_id))
    if not farm:
        raise HTTPException(404, 'Farm not found')
    if write and farm.owner_id != user.id and 'ADMIN' not in roles(db, user):
        raise HTTPException(403, 'Only the owner or administrator can change farm records')
    return farm


def sample_access(db, user, sample_id, write=False):
    sample = db.get(SoilSample, sample_id)
    if not sample:
        raise HTTPException(404, 'Sample not found')
    farm_access(db, user, sample.farm_id, write)
    return sample
