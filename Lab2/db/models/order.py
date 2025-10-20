from datetime import datetime
from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4

from db.base import Base


order_product_association = Table(
    'order_products',
    Base.metadata,
    Column('order_id', ForeignKey('orders.id'), primary_key=True),
    Column('product_id', ForeignKey('products.id'), primary_key=True)
)


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    address_id: Mapped[str] = mapped_column(ForeignKey('addresses.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

    user = relationship("User", back_populates="orders")
    address = relationship("Address")
    products = relationship("Product", secondary=order_product_association)
