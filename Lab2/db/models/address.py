from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from uuid import uuid4
from datetime import datetime

from db.base import Base


class Address(Base):
    __tablename__ = 'addresses'

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    street: Mapped[str] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column()
    zip_code: Mapped[str] = mapped_column()
    country: Mapped[str] = mapped_column(nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=False)

    user = relationship("User", back_populates="addresses")
