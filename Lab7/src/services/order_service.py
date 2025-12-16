from typing import Dict, List, Optional

from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        user_repository: UserRepository,
    ):
        self.order_repository = order_repository
        self.user_repository = user_repository
        self.product_repository = product_repository

    async def create_order(self, order_data: Dict):
        user_id = order_data["user_id"]
        print(f"Looking for user with ID: {user_id} (type: {type(user_id)})")

        user = await self.user_repository.get_by_id(user_id)
        print(f"Found user: {user}")

        if not user:
            raise ValueError(f"User not found {user_id}")

        items: List[Dict] = order_data.get("items", [])
        if not items:
            raise ValueError("Order must have at least one item")

        # Validate quantities before processing
        for it in items:
            if it["quantity"] <= 0:
                raise ValueError("Quantity must be greater than 0")

        total = 0.0
        updated_products = []

        for it in items:
            product = await self.product_repository.get_by_id(it["product_id"])
            if not product:
                raise ValueError(f"Product {it['product_id']} not found")
            if product.stock_quantity < it["quantity"]:
                raise ValueError("Insufficient stock")
            total += product.price * it["quantity"]
            updated_products.append((product, it["quantity"]))

        for product, quantity in updated_products:
            product.stock_quantity -= quantity
            await self.product_repository.update(
                product.id, stock_quantity=product.stock_quantity
            )

        order = await self.order_repository.create(user_id=user.id, items=items)
        return order

    async def get_by_id(self, order_id: int):
        """
        Get a single order by ID.
        """
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        return order

    async def delete(self, order_id: int):
        """
        Delete an order by ID.
        """
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        await self.order_repository.delete(order_id)

    async def update(self, order_id: int, update_data: Dict):
        """
        Update an order (typically status changes).
        """
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        order_fields = {}

        if "status" in update_data and update_data["status"] is not None:
            status = update_data["status"]
            status_str = status.value if hasattr(status, "value") else str(status)

            valid_statuses = [
                "pending",
                "processing",
                "shipped",
                "delivered",
                "cancelled",
            ]
            if status_str not in valid_statuses:
                raise ValueError(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )

            if status_str == "cancelled" and order.status != "cancelled":
                for item in order.items:
                    product = await self.product_repository.get_by_id(item.product_id)
                    if product:
                        new_stock = product.stock_quantity + item.quantity
                        await self.product_repository.update(
                            product.id, stock_quantity=new_stock
                        )

            order_fields["status"] = status_str

        if "items" in update_data and update_data["items"] is not None:
            items_list = []
            for item in update_data["items"]:
                items_list.append(
                    {"product_id": item["product_id"], "quantity": item["quantity"]}
                )
            order_fields["items"] = items_list

        if order_fields:
            updated_order = await self.order_repository.update(order_id, **order_fields)
        else:
            updated_order = order

        return updated_order

    async def get_by_filter(
        self,
        count: int = 10,
        page: int = 1,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict:
        """
        Returns paginated list of orders with optional filters.
        """
        offset = (page - 1) * count

        try:
            total, items = await self.order_repository.list(
                limit=count, offset=offset, user_id=user_id, status=status
            )
        except TypeError:
            total, all_orders = await self.order_repository.list(limit=1000, offset=0)

            filtered_orders = all_orders
            if user_id is not None:
                filtered_orders = [o for o in filtered_orders if o.user_id == user_id]
            if status is not None:
                filtered_orders = [o for o in filtered_orders if o.status == status]

            total = len(filtered_orders)

            items = filtered_orders[offset : offset + count]

        return {"total": total, "items": items}
