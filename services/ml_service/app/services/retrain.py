import shutil
import threading
import time
from pathlib import Path
from typing import TypedDict

import pandas as pd
from loguru import logger

from app.config import settings
from app.services.predictions import REGION_DATA, load_region_data
from app.services.predictions import load_all_models
from app.services.training import train_models


_LOCK = threading.Lock()


class RetrainResult(TypedDict):
    saved_models: list[str]
    metrics_json: str
    metrics_csv: str


def retrain_from_dataset_csv(
    dataset_csv: Path,
    *,
    models_dir: Path,
    iterations: int = 200,
    learning_rate: float = 0.1,
    test_size: float = 0.33,
    random_state: int = 1000,
) -> RetrainResult:
    """
    Retrains all models from an already prepared dataset (like `train_dataset.csv`).

    The CSV must contain:
    - `id`, `year`
    - base patient features
    - disease target flags: инсульт, сн, нарушение ритма или ибс, стенокардия, им, аг
    """
    df = pd.read_csv(dataset_csv)
    logger.info(
        "Retrain requested from dataset_csv={} rows={} cols={}",
        str(dataset_csv),
        len(df),
        len(df.columns),
    )

    required_cols = {"id", "year"}
    required_targets = {
        "инсульт",
        "сн",
        "нарушение ритма или ибс",
        "стенокардия",
        "им",
        "аг",
    }
    missing = sorted((required_cols | required_targets) - set(df.columns))
    if missing:
        logger.error("Retrain failed: missing required columns: {}", missing)
        raise ValueError(
            "Dataset CSV is missing required columns: " + ", ".join(missing)
        )

    invalid_targets: list[str] = []
    for t in sorted(required_targets):
        y = df[t].fillna(0).astype(int)
        pos = int(y.sum())
        neg = int((y == 0).sum())
        if pos == 0 or neg == 0:
            invalid_targets.append(f"{t} (pos={pos}, neg={neg})")
    if invalid_targets:
        logger.error("Retrain failed: invalid class distribution: {}", invalid_targets)
        raise ValueError(
            "Dataset CSV has invalid class distribution for targets: "
            + "; ".join(invalid_targets)
        )

    tmp_dir = models_dir.parent / f"{models_dir.name}__retrain_tmp_{int(time.time())}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    with _LOCK:
        if not REGION_DATA:
            load_region_data(settings.REGION_DATA_PATH)

        logger.info("Training models into tmp_dir={}", str(tmp_dir))
        train_models(
            df,
            out_dir=tmp_dir,
            region_data=REGION_DATA,
            test_size=test_size,
            random_state=random_state,
            iterations=iterations,
            learning_rate=learning_rate,
        )

        cbm_files = sorted(p.name for p in tmp_dir.glob("*.cbm"))
        if not cbm_files:
            logger.error("Retrain failed: no *.cbm produced in {}", str(tmp_dir))
            raise RuntimeError("No model files were produced during retrain")

        models_dir.mkdir(parents=True, exist_ok=True)
        for f in models_dir.glob("*_model.cbm"):
            f.unlink()

        for src in tmp_dir.glob("*_model.cbm"):
            shutil.move(str(src), str(models_dir / src.name))
        logger.info("Saved model files to {}", str(models_dir))

        metrics_json = tmp_dir / "metrics.json"
        metrics_csv = tmp_dir / "metrics.csv"
        if metrics_json.exists():
            shutil.move(str(metrics_json), str(models_dir / metrics_json.name))
        if metrics_csv.exists():
            shutil.move(str(metrics_csv), str(models_dir / metrics_csv.name))

        shutil.rmtree(tmp_dir, ignore_errors=True)

        load_all_models(models_dir)
        logger.info("Hot-reloaded models after retrain")

    saved = sorted(p.name for p in models_dir.glob("*.cbm"))
    return {
        "saved_models": saved,
        "metrics_json": str(models_dir / "metrics.json")
        if (models_dir / "metrics.json").exists()
        else "",
        "metrics_csv": str(models_dir / "metrics.csv")
        if (models_dir / "metrics.csv").exists()
        else "",
    }
