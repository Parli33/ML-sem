import logging
from time import monotonic
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MlApiError(RuntimeError):
    pass


def request_prediction(
    base_url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/predict"
    started_at = monotonic()
    logger.info("Sending prediction request to ML API url=%s", url)
    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        logger.error(
            "ML API rejected prediction request url=%s status=%s duration_ms=%.1f",
            url,
            error.response.status_code,
            (monotonic() - started_at) * 1000,
        )
        raise MlApiError(
            f"ML API отклонил запрос: HTTP {error.response.status_code}"
        ) from error
    except httpx.RequestError as error:
        logger.error(
            "ML API request failed url=%s duration_ms=%.1f error=%s",
            url,
            (monotonic() - started_at) * 1000,
            error,
        )
        raise MlApiError("ML API сейчас недоступен") from error

    try:
        data = response.json()
    except ValueError as error:
        logger.error("ML API returned invalid JSON url=%s", url)
        raise MlApiError("ML API вернул некорректный ответ") from error
    if not isinstance(data, dict):
        logger.error("ML API returned unexpected response type url=%s", url)
        raise MlApiError("ML API вернул некорректный ответ")
    logger.info(
        "ML API prediction request completed status=%s duration_ms=%.1f",
        response.status_code,
        (monotonic() - started_at) * 1000,
    )
    return data
