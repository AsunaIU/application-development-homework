from db.session import SessionLocal
from crud.user import create_user
from crud.address import create_address_for_user
from crud.product import create_product
from crud.order import create_order


def main():
    db = SessionLocal()
    try:
        user = create_user(db, username="John Doe", email="jdoe@example.com")
        user.description = "VIP клиент"
        db.commit()
        db.refresh(user)

        address = create_address_for_user(
            db, 
            user_id=user.id, 
            street="21 Wall St", 
            city="New York", 
            country="USA", 
            state="NY", 
            zip_code="10005", 
            is_primary=True
        )

        products = []
        for i in range(5):
            products.append(create_product(db, f"Product {i+1}", f"Description {i+1}", price=10.0*(i+1)))

        for i in range(5):
            create_order(db, user_id=user.id, address_id=address.id, product_ids=[p.id for p in products])

    finally:
        db.close()


if __name__ == "__main__":
    main()
