from sqlalchemy.orm import Session
from db.models.product import Product
from db.models.order import Order


def create_order(db: Session, user_id: str, address_id: str, product_ids: list[str]):
    order = Order(user_id=user_id, address_id=address_id)
    db.add(order)
    db.commit()

    order.products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    db.commit()
    db.refresh(order)
    return order
