from datetime import datetime
from sqlalchemy import Float
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4


from db.base import Base

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=False)
