from fastapi import APIRouter
from loguru import logger

from app.schemas.predict import PredictResponse, PredictRequest
from app.config import settings
from app.services.predictions import predict_all


router = APIRouter(tags=["Prediction"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Возвращает словарь в виде: болезнь:вероятность ее наличия",
)
async def predict_risk(request: PredictRequest) -> PredictResponse:
    logger.info("Predict request received")
    pairs = predict_all(request)
    predictions = [f"{model}:{probability}" for model, probability in pairs]
    return PredictResponse(
        predictions=predictions,
        model_version=settings.MODEL_VERSION,
    )
