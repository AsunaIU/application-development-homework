from sqlalchemy.orm import Session
from db.models.product import Product


def create_product(db: Session, name: str, description: str, price: float):
    product = Product(name=name, description=description, price=price)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
