from collections.abc import Iterator
from pathlib import Path

import pytest
from flask import Flask

from app import create_app
from app.extensions import db


@pytest.fixture
def app(tmp_path: Path) -> Iterator[Flask]:
    database_path = tmp_path / "test.db"
    application = create_app(
        {
            "SECRET_KEY": "test-secret",
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "ML_API_URL": "http://ml-api.test",
        }
    )

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
