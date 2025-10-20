from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from uuid import uuid4
from datetime import datetime

from db.base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4())
    )
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(default="", nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=False)

    addresses = relationship("Address", back_populates="user")
    orders = relationship("Order", back_populates="user")
