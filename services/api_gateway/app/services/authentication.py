import logging

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.infrastructure.models import User

logger = logging.getLogger(__name__)


def register_user(username: str, password: str) -> User | None:
    normalized_username = username.strip()
    try:
        existing_user = db.session.scalar(
            db.select(User).where(User.username == normalized_username)
        )
        if existing_user is not None:
            logger.info("Registration rejected: username already exists")
            return None

        user = User(username=normalized_username, hashed_password="")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Failed to register user")
        raise

    logger.info("User registered id=%s", user.id)
    return user


def authenticate_user(username: str, password: str) -> User | None:
    normalized_username = username.strip()
    try:
        user = db.session.scalar(
            db.select(User).where(User.username == normalized_username)
        )
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Failed to query user during authentication")
        raise

    if user is None or not user.check_password(password):
        logger.info("Authentication rejected")
        return None
    logger.info("Authentication successful user_id=%s", user.id)
    return user
