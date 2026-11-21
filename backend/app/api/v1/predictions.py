from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.database.session import get_db
from app.core.security import current_user
from app.repositories.access import sample_access
from app.models.entities import Prediction, CropRecommendation, FertilizerRecommendation
from app.schemas.auth import StrictModel
from app.services.records import record_json

router=APIRouter()


class PredictionInput(StrictModel):
    sample_id:str


def unavailable(sample):
    if sample.status!='submitted':
        raise HTTPException(422,'Submit a complete soil sample before requesting analysis')
    raise HTTPException(503,{'code':'MODEL_NOT_VALIDATED','message':'No compatible validated model is deployed. Recorded measurements remain available. Predictions require verified public data, regional evaluation and administrator approval.'})


@router.post('/predictions/fertility')
def fertility(data:PredictionInput,user=Depends(current_user),db=Depends(get_db)):
    return unavailable(sample_access(db,user,data.sample_id))


@router.post('/predictions/crops')
def crops(data:PredictionInput,user=Depends(current_user),db=Depends(get_db)):
    sample=sample_access(db,user,data.sample_id)
    required=['temperature','rainfall','humidity','season','rainfall_period']
    if any(sample.climate.get(k) is None or sample.climate.get(k)=='' for k in required) or sample.climate.get('irrigation','unknown')=='unknown':
        raise HTTPException(422,'Record air temperature, humidity, rainfall and period, season, and irrigation before crop recommendations')
    return unavailable(sample)


@router.get('/predictions/{prediction_id}')
def prediction(prediction_id:str,user=Depends(current_user),db=Depends(get_db)):
    item=db.get(Prediction,prediction_id)
    if not item:
        raise HTTPException(404,'Prediction not found')
    sample_access(db,user,item.sample_id)
    return record_json(item)


@router.get('/recommendations/crops/{prediction_id}')
def crop_recommendations(prediction_id:str,user=Depends(current_user),db=Depends(get_db)):
    prediction(prediction_id,user,db)
    return [record_json(c) for c in db.scalars(select(CropRecommendation).where(CropRecommendation.prediction_id==prediction_id))]


@router.get('/recommendations/fertilizers/{prediction_id}')
def fertilizer_recommendations(prediction_id:str,user=Depends(current_user),db=Depends(get_db)):
    prediction(prediction_id,user,db)
    return [record_json(f) for f in db.scalars(select(FertilizerRecommendation).where(FertilizerRecommendation.prediction_id==prediction_id))]
