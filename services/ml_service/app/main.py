from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from app.config import settings
from app.logging import setup_logging
from app.schemas.model_info import ModelInfoResponse
from app.schemas.predict import PredictRequest
from app.routers.predictions import router as predictions_router
from app.routers.retrain import router as retrain_router
from app.services.predictions import MODELS, load_all_models, load_region_data


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info("Starting ML service")
    load_all_models(settings.MODELS_DIR)
    load_region_data(settings.REGION_DATA_PATH)
    logger.info(
        "Loaded models_dir={} region_data_path={}",
        str(settings.MODELS_DIR),
        str(settings.REGION_DATA_PATH),
    )
    yield


app = FastAPI(title="ML Service", lifespan=lifespan)

app.include_router(predictions_router)
app.include_router(retrain_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    feature_types = {
        name: str(field.annotation)
        for name, field in PredictRequest.model_fields.items()
    }
    return ModelInfoResponse(
        name="Cardiovascular disease risk models",
        version=settings.MODEL_VERSION,
        models=sorted(MODELS),
        feature_types=feature_types,
    )
