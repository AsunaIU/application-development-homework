from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.user import User


def create_user(db: Session, username: str, email: str):
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        return existing_user
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
