from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from src.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)

    order_items = relationship("OrderItem", back_populates="product")
