from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from pydantic import Field
from app.database.session import get_db
from app.models.entities import Farm, SoilSample, Measurement, Prediction, User, UserRole, AuditLog, ModelVersion, MLModel, Dataset, Session
from app.core.security import current_user, require, roles, user_json, audit
from app.repositories.access import visible_farms, farm_access
from app.schemas.auth import StrictModel
from app.services.records import record_json

router=APIRouter()


@router.get('/dashboard')
def dashboard(user=Depends(current_user),db=Depends(get_db)):
    farm_ids=visible_farms(db,user).with_only_columns(Farm.id)
    samples=list(db.scalars(select(SoilSample).where(SoilSample.farm_id.in_(farm_ids)).order_by(SoilSample.collected_on.desc())))
    sample_ids=[s.id for s in samples]
    predictions=list(db.scalars(select(Prediction).where(Prediction.sample_id.in_(sample_ids),Prediction.task=='fertility').order_by(Prediction.created_at.desc()))) if sample_ids else []
    latest={}
    for p in predictions:
        if p.sample_id not in latest:
            latest[p.sample_id]=p
    distribution={label:sum(p.result.get('label')==label for p in latest.values()) for label in ['low','medium','high']}
    measurements=list(db.scalars(select(Measurement).where(Measurement.sample_id.in_([s.id for s in samples[:30]])))) if samples else []
    trends=[{'sample_id':s.id,'sample_code':s.sample_code,'date':s.collected_on,'measurements':[{'parameter':m.parameter,'value':m.value,'unit':m.unit,'method':m.method} for m in measurements if m.sample_id==s.id]} for s in reversed(samples[:30])]
    return {'farms':db.scalar(select(func.count()).select_from(visible_farms(db,user).subquery())), 'samples':len(samples),'submitted':sum(s.status=='submitted' for s in samples),'completed_analyses':len(latest),'fertility_distribution':distribution,'recent_samples':[record_json(s) for s in samples[:5]],'trends':trends,'model_status':'available' if db.scalar(select(ModelVersion).where(ModelVersion.active==True,ModelVersion.approved==True)) else 'unavailable','activity':[record_json(a) for a in db.scalars(select(AuditLog).where(AuditLog.user_id==user.id).order_by(AuditLog.created_at.desc()).limit(8))]}


@router.get('/admin/analytics')
def analytics(user=Depends(require('ADMIN')),db=Depends(get_db)):
    return {'users':db.scalar(select(func.count(User.id))),'farms':db.scalar(select(func.count(Farm.id)).where(Farm.deleted==False)),'samples':db.scalar(select(func.count(SoilSample.id))),'predictions':db.scalar(select(func.count(Prediction.id))),'datasets':db.scalar(select(func.count(Dataset.id))),'approved_models':db.scalar(select(func.count(ModelVersion.id)).where(ModelVersion.active==True,ModelVersion.approved==True))}


@router.get('/admin/users')
def users(user=Depends(require('ADMIN')),db=Depends(get_db),offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=200)):
    return [user_json(db,u) for u in db.scalars(select(User).order_by(User.created_at.desc()).offset(offset).limit(limit))]


class UserAdminInput(StrictModel):
    roles:list[Literal['FARMER','ADMIN','AGRICULTURAL_OFFICER']]=Field(min_length=1,max_length=3)
    active:bool=True


@router.put('/admin/users/{user_id}')
def manage_user(user_id:str,data:UserAdminInput,user=Depends(require('ADMIN')),db=Depends(get_db)):
    target=db.get(User,user_id)
    if not target:
        raise HTTPException(404,'User not found')
    if user_id==user.id and ('ADMIN' not in data.roles or not data.active):
        raise HTTPException(422,'You cannot remove your own administrative access')
    target.active=data.active
    db.execute(delete(UserRole).where(UserRole.user_id==user_id))
    db.add_all([UserRole(user_id=user_id,role=role) for role in set(data.roles)])
    # Role changes invalidate all target sessions, including existing access JWTs.
    for session in db.scalars(select(Session).where(Session.user_id==user_id)):
        session.revoked=True
    audit(db,user.id,'user.permissions.update',user_id)
    db.commit()
    return user_json(db,target)


class AssignOfficer(StrictModel):
    officer_id:str|None=None


@router.put('/admin/farms/{farm_id}/officer')
def assign_officer(farm_id:str,data:AssignOfficer,user=Depends(require('ADMIN')),db=Depends(get_db)):
    farm=farm_access(db,user,farm_id,True)
    if data.officer_id:
        target=db.get(User,data.officer_id)
        if not target or not target.active or 'AGRICULTURAL_OFFICER' not in roles(db,target):
            raise HTTPException(422,'Select an active agricultural officer')
    farm.officer_id=data.officer_id
    audit(db,user.id,'farm.officer.assign',farm_id)
    db.commit()
    return record_json(farm)


@router.get('/admin/audit-logs')
def audit_logs(user=Depends(require('ADMIN')),db=Depends(get_db),limit:int=Query(100,ge=1,le=200)):
    return [record_json(a) for a in db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))]


@router.get('/admin/models')
def models(user=Depends(require('ADMIN')),db=Depends(get_db)):
    return [{'model':record_json(m),'versions':[record_json(v) for v in db.scalars(select(ModelVersion).where(ModelVersion.model_id==m.id))]} for m in db.scalars(select(MLModel))]


@router.get('/admin/datasets')
def datasets(user=Depends(require('ADMIN')),db=Depends(get_db)):
    return [record_json(d) for d in db.scalars(select(Dataset).order_by(Dataset.created_at.desc()))]
