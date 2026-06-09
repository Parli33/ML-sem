from typing import Any

import httpx
from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db
from app.infrastructure.models import Prediction, User


PREDICTION_FORM_DATA: dict[str, str] = {
    "gender": "1",
    "age": "40",
    "height": "175",
    "weight": "75",
    "hip_measurement": "95",
    "alcohol": "0",
    "profession": "8",
    "region": "2",
}


def register_and_login(client: FlaskClient, username: str = "student") -> None:
    client.post(
        "/register",
        data={
            "username": username,
            "password": "strong-password",
            "password_confirmation": "strong-password",
        },
    )
    client.post(
        "/login",
        data={"username": username, "password": "strong-password"},
    )


def test_index_displays_model_info(app: Flask, monkeypatch: Any) -> None:
    client = app.test_client()
    register_and_login(client)

    def fake_get(*args: Any, **kwargs: Any) -> httpx.Response:
        request = httpx.Request("GET", "http://ml-api.test/model-info")
        return httpx.Response(
            200,
            request=request,
            json={
                "name": "Cardiovascular disease risk models",
                "version": "1.0.0",
                "models": ["general", "ah"],
                "feature_types": {"age": "<class 'int'>"},
            },
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    response = client.get("/")

    assert response.status_code == 200
    assert b"Cardiovascular disease risk models" in response.data
    assert b"1.0.0" in response.data
    assert b"general, ah" in response.data


def test_index_works_when_model_info_is_unavailable(
    app: Flask,
    monkeypatch: Any,
) -> None:
    client = app.test_client()
    register_and_login(client)

    def failing_get(*args: Any, **kwargs: Any) -> httpx.Response:
        raise httpx.ConnectError("unavailable")

    monkeypatch.setattr(httpx, "get", failing_get)
    response = client.get("/")

    assert response.status_code == 200
    assert "Информация о модели сейчас недоступна".encode() in response.data


def test_prediction_is_saved_and_rendered(
    app: Flask,
    monkeypatch: Any,
) -> None:
    client = app.test_client()
    register_and_login(client)

    def fake_post(*args: Any, **kwargs: Any) -> httpx.Response:
        request = httpx.Request("POST", "http://ml-api.test/predict")
        return httpx.Response(
            200,
            request=request,
            json={
                "predictions": ["general:0.25", "ah:0.5"],
                "model_version": "1.0.0",
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    response = client.post("/predict", data=PREDICTION_FORM_DATA)

    assert response.status_code == 200
    assert "Общий риск: вероятность 25.0%".encode() in response.data
    assert "Артериальная гипертензия: вероятность 50.0%".encode() in response.data
    with app.app_context():
        prediction = db.session.scalar(db.select(Prediction))
        assert prediction is not None
        assert prediction.user_id == 1
        assert prediction.input_data["age"] == 40
        assert prediction.prediction["model_version"] == "1.0.0"


def test_ml_api_error_is_displayed_without_saving(
    app: Flask,
    monkeypatch: Any,
) -> None:
    client = app.test_client()
    register_and_login(client)

    def failing_post(*args: Any, **kwargs: Any) -> httpx.Response:
        raise httpx.ConnectError("unavailable")

    monkeypatch.setattr(httpx, "post", failing_post)
    response = client.post("/predict", data=PREDICTION_FORM_DATA)

    assert response.status_code == 200
    assert "ML API сейчас недоступен".encode() in response.data
    with app.app_context():
        assert db.session.scalar(db.select(Prediction)) is None


def test_history_contains_only_current_users_predictions(app: Flask) -> None:
    client = app.test_client()
    register_and_login(client, "first-user")

    with app.app_context():
        first_user = db.session.scalar(
            db.select(User).where(User.username == "first-user")
        )
        second_user = User(username="second-user", hashed_password="")
        second_user.set_password("strong-password")
        db.session.add(second_user)
        db.session.flush()
        assert first_user is not None
        db.session.add_all(
            [
                Prediction(
                    user_id=first_user.id,
                    input_data={"age": 40},
                    prediction={
                        "predictions": ["general:0.25"],
                        "model_version": "1.0.0",
                    },
                ),
                Prediction(
                    user_id=second_user.id,
                    input_data={"age": 50},
                    prediction={
                        "predictions": ["general:0.75"],
                        "model_version": "1.0.0",
                    },
                ),
            ]
        )
        db.session.commit()

    response = client.get("/history")

    assert response.status_code == 200
    assert "Общий риск: вероятность 25.0%".encode() in response.data
    assert "Общий риск: вероятность 75.0%".encode() not in response.data
    assert b"bootstrap.bundle.min.js" in response.data


def test_prediction_pages_require_login(app: Flask) -> None:
    client = app.test_client()

    assert client.get("/predict").status_code == 302
    assert client.get("/history").status_code == 302
