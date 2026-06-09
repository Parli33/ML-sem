from pathlib import Path
from pydantic import DirectoryPath, FilePath
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # Avoid accidental cross-project env var collisions like MODELS_DIR=models_v2.
    # Use ML_MODELS_DIR / ML_REGION_DATA_PATH if overriding is needed.
    model_config = SettingsConfigDict(env_prefix="ML_")

    MODEL_VERSION: str = "1.0.0"
    MODELS_DIR: DirectoryPath = BASE_DIR / "models"
    REGION_DATA_PATH: FilePath = BASE_DIR / "data" / "region_data.json"


settings = Settings()
