from typing import Any

import httpx


class MlApiError(RuntimeError):
    pass


def request_prediction(
    base_url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> dict[str, Any]:
    try:
        response = httpx.post(
            f"{base_url.rstrip('/')}/predict",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise MlApiError(
            f"ML API отклонил запрос: HTTP {error.response.status_code}"
        ) from error
    except httpx.RequestError as error:
        raise MlApiError("ML API сейчас недоступен") from error

    data = response.json()
    if not isinstance(data, dict):
        raise MlApiError("ML API вернул некорректный ответ")
    return data
