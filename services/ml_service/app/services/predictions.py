import json
from pathlib import Path

from catboost import Pool
from loguru import logger

from app.services.model_registry import LoadedModel, load_models
from app.services.preprocess import request_to_vector
from app.schemas.predict import PredictRequest


MODELS: dict[str, LoadedModel] = {}
REGION_DATA: dict[str, dict[str, float]] = {}


def load_region_data(path: Path) -> None:
    logger.info("Loading region data: {}", str(path))
    REGION_DATA.clear()
    REGION_DATA.update(json.loads(path.read_text(encoding="utf-8")))
    logger.info("Loaded region data entries: {}", len(REGION_DATA))


def load_all_models(models_dir: Path) -> None:
    logger.info("Loading models from dir: {}", str(models_dir))
    MODELS.clear()
    MODELS.update(load_models(models_dir))


def predict_all(request: PredictRequest) -> list[tuple[str, float]]:
    if not MODELS:
        raise RuntimeError("Models are not loaded")
    if not REGION_DATA:
        raise RuntimeError("Region data is not loaded")

    region_key = request.region.name
    try:
        region_stats = REGION_DATA[region_key]
    except KeyError as e:
        raise KeyError(f"Unknown region key {region_key!r} in region_data.json") from e

    out: list[tuple[str, float]] = []
    for name, loaded in MODELS.items():
        vector = request_to_vector(
            request, feature_order=loaded.feature_names, region_stats=region_stats
        )
        pool = Pool([vector], cat_features=loaded.cat_feature_indices)
        prob = float(loaded.model.predict_proba(pool)[0][1])
        out.append((name, prob))

    out.sort(key=lambda x: x[0])
    logger.info(
        "Predicted {} models for region={}",
        len(out),
        region_key,
    )
    return out
