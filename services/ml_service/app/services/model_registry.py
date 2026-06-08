from dataclasses import dataclass
from pathlib import Path

from catboost import CatBoostClassifier
from loguru import logger


@dataclass(frozen=True)
class LoadedModel:
    name: str
    path: Path
    model: CatBoostClassifier
    feature_names: list[str]
    cat_feature_indices: list[int]


def load_models(models_dir: Path) -> dict[str, LoadedModel]:
    """
    Loads all `*.cbm` CatBoost models from a directory.

    Key is model name (stem without `_model` suffix when present).
    """
    loaded: dict[str, LoadedModel] = {}
    for path in sorted(models_dir.glob("*.cbm")):
        logger.info("Loading model: {}", str(path))
        model = CatBoostClassifier()
        model.load_model(str(path))

        name = path.stem
        for suffix in ("_model",):
            if name.endswith(suffix):
                name = name[: -len(suffix)]

        loaded[name] = LoadedModel(
            name=name,
            path=path,
            model=model,
            feature_names=list(getattr(model, "feature_names_", [])),
            cat_feature_indices=list(model.get_cat_feature_indices()),
        )
        logger.info(
            "Loaded model {} (features={}, cat_idx={})",
            name,
            len(loaded[name].feature_names),
            loaded[name].cat_feature_indices,
        )
    logger.info("Total models loaded: {}", len(loaded))
    return loaded
