FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY services/api_gateway/pyproject.toml services/api_gateway/pyproject.toml
COPY services/ml_service/pyproject.toml services/ml_service/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package web --no-install-project

FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY services/api_gateway/app ./app
COPY services/api_gateway/migrations ./migrations

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

CMD ["sh", "-c", "flask --app app:create_app db upgrade && gunicorn --bind 0.0.0.0:5000 'app:create_app()'"]
