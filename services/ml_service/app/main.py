from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from app.logging import setup_logging
from app.routers.predictions import router as predictions_router
from app.routers.retrain import router as retrain_router
from app.services.predictions import load_all_models, load_region_data
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
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
def health_check():
    return {"status": "ok"}
