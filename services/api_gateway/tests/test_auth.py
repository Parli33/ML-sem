from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db
from app.infrastructure.models import User


def test_registration_stores_hashed_password(app: Flask) -> None:
    client = app.test_client()

    response = client.post(
        "/register",
        data={
            "username": "student",
            "password": "strong-password",
            "password_confirmation": "strong-password",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Регистрация завершена".encode() in response.data
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == "student"))
        assert user is not None
        assert user.hashed_password != "strong-password"
        assert user.check_password("strong-password")


def test_login_grants_access_to_protected_page(app: Flask) -> None:
    client: FlaskClient = app.test_client()
    client.post(
        "/register",
        data={
            "username": "student",
            "password": "strong-password",
            "password_confirmation": "strong-password",
        },
    )

    response = client.post(
        "/login",
        data={"username": "student", "password": "strong-password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Добро пожаловать".encode() in response.data


def test_protected_page_redirects_anonymous_user(app: Flask) -> None:
    response = app.test_client().get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
