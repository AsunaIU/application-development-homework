from sqlalchemy.orm import Session

from db.models.address import Address


def create_address_for_user(
    db: Session,
    user_id: str,
    street: str,
    city: str,
    country: str,
    state: str = None,
    zip_code: str = None,
    is_primary: bool = False,
):
    address = Address(
        user_id=user_id,
        street=street,
        city=city,
        state=state,
        zip_code=zip_code,
        country=country,
        is_primary=is_primary,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address

