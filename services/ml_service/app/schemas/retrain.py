from pydantic import BaseModel, Field


class RetrainResponse(BaseModel):
    status: str = Field(description="ok / error")
    models_dir: str = Field(description="Куда сохранены модели")
    saved_models: list[str] = Field(description="Список сохранённых файлов моделей")
    metrics_json: str | None = Field(default=None, description="Путь к metrics.json")
    metrics_csv: str | None = Field(default=None, description="Путь к metrics.csv")
