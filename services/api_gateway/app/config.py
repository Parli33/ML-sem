import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ML_API_URL = os.environ.get("ML_API_URL", "http://localhost:8000")
    ML_API_TIMEOUT = 10.0
    APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Krasnoyarsk")
