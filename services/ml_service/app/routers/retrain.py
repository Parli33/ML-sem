import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from loguru import logger

from app.config import settings
from app.schemas.retrain import RetrainResponse
from app.services.retrain import retrain_from_dataset_csv


router = APIRouter(tags=["Retrain"])


@router.post(
    "/retrain",
    response_model=RetrainResponse,
    summary="Переобучает все модели по входному датасету",
)
async def retrain_model(
    dataset: UploadFile = File(..., description="CSV как `train_dataset.csv`"),
) -> RetrainResponse:
    logger.info("Retrain request received: filename={}", dataset.filename)
    suffix = Path(dataset.filename or "train_dataset.csv").suffix or ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await dataset.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    logger.info("Saved uploaded dataset to {}", str(tmp_path))
    result = retrain_from_dataset_csv(tmp_path, models_dir=Path(settings.MODELS_DIR))
    return RetrainResponse(
        status="ok",
        models_dir=str(settings.MODELS_DIR),
        saved_models=list(result["saved_models"]),
        metrics_json=result["metrics_json"] or None,
        metrics_csv=result["metrics_csv"] or None,
    )
