from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.order import Order, OrderItem
from src.models.product import Product
from src.models.user import User


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, items: List[Dict]) -> Order:
        user = await self.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        order = Order(user_id=user_id, status="pending", total_amount=0)
        self.session.add(order)
        await self.session.flush()

        total = 0
        for it in items:
            product_id = it["product_id"]
            quantity = int(it["quantity"])
            product = await self.session.get(Product, product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")
            unit_price = float(product.price)
            oi = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
            )
            self.session.add(oi)
            total += quantity * unit_price

        order.total_amount = total
        await self.session.commit()
        await self.session.refresh(order, ["items"])
        return order

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        stmt = (
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        limit: int = 10,
        offset: int = 0,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Tuple[int, List[Order]]:
        count_stmt = select(Order)
        stmt = select(Order).options(selectinload(Order.items))

        if user_id is not None:
            count_stmt = count_stmt.where(Order.user_id == user_id)
            stmt = stmt.where(Order.user_id == user_id)

        if status is not None:
            count_stmt = count_stmt.where(Order.status == status)
            stmt = stmt.where(Order.status == status)

        total_res = await self.session.execute(count_stmt)
        all_rows = total_res.scalars().all()
        total = len(all_rows)

        stmt = stmt.limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        items = res.scalars().all()

        return total, items

    async def update(self, order_id: int, **patch) -> Optional[Order]:
        order = await self.get_by_id(order_id)
        if not order:
            return None

        if "status" in patch and patch["status"] is not None:
            order.status = str(patch["status"])

        if "items" in patch and patch["items"] is not None:
            new_items = patch["items"]
            existing_by_product = {int(i.product_id): i for i in order.items}
            seen_product_ids = set()
            total = 0.0

            for ni in new_items:
                pid = int(ni["product_id"])
                qty = int(ni["quantity"])
                seen_product_ids.add(pid)

                product = await self.session.get(Product, pid)
                if not product:
                    raise ValueError(f"Product {pid} not found")

                unit_price = float(product.price)

                if pid in existing_by_product:
                    existing = existing_by_product[pid]
                    existing.quantity = qty
                    existing.unit_price = unit_price
                    self.session.add(existing)
                else:
                    new_oi = OrderItem(
                        order_id=order.id,
                        product_id=pid,
                        quantity=qty,
                        unit_price=unit_price,
                    )
                    self.session.add(new_oi)

                total += qty * unit_price

            for pid, existing in existing_by_product.items():
                if pid not in seen_product_ids:
                    await self.session.delete(existing)

            order.total_amount = total

        await self.session.commit()
        await self.session.refresh(order, ["items"])
        return order

    async def delete(self, order_id: int) -> None:
        order = await self.get_by_id(order_id)
        if order:
            await self.session.delete(order)
            await self.session.commit()
