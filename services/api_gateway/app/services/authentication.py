from app.extensions import db
from app.infrastructure.models import User


def register_user(username: str, password: str) -> User | None:
    normalized_username = username.strip()
    existing_user = db.session.scalar(
        db.select(User).where(User.username == normalized_username)
    )
    if existing_user is not None:
        return None

    user = User(username=normalized_username, hashed_password="")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(username: str, password: str) -> User | None:
    user = db.session.scalar(db.select(User).where(User.username == username.strip()))
    if user is None or not user.check_password(password):
        return None
    return user
