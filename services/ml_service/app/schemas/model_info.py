from pydantic import BaseModel, Field


class ModelInfoResponse(BaseModel):
    name: str = Field(description="Название набора моделей")
    version: str = Field(description="Версия моделей")
    models: list[str] = Field(description="Названия загруженных моделей")
    feature_types: dict[str, str] = Field(description="Типы входных признаков")
