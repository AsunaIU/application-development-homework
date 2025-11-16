from typing import Annotated, List

from litestar import Controller, get, post, patch, delete
from litestar.params import Parameter, Dependency
from litestar.exceptions import NotFoundException, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

from src.services.order_service import OrderService
from src.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderUpdate
from src.utils.db_error_handler import handle_db_errors


class OrderController(Controller):
    path = "/orders"
    tags = ["Orders"]

    @post()
    @handle_db_errors
    async def create_order(
        self,
        order_service: Annotated[OrderService, Dependency(skip_validation=True)],
        data: OrderCreate,
    ) -> OrderResponse:
        """Create a new order (supports multiple items)"""
        order = await order_service.create_order(data.model_dump())
        return OrderResponse.model_validate(order)

    @get("/{order_id:int}")
    @handle_db_errors
    async def get_order_by_id(
        self,
        order_service: Annotated[OrderService, Dependency(skip_validation=True)],
        order_id: int = Parameter(gt=0),
    ) -> OrderResponse:
        order = await order_service.get_by_id(order_id)
        if not order:
            raise NotFoundException(detail=f"Order with ID {order_id} not found")
        return OrderResponse.model_validate(order)

    @get()
    @handle_db_errors
    async def list_orders(
        self,
        order_service: Annotated[OrderService, Dependency(skip_validation=True)],
        count: int = Parameter(default=10, gt=0, le=100),
        page: int = Parameter(default=1, gt=0),
    ) -> OrderListResponse:
        result = await order_service.get_by_filter(count, page)
        return OrderListResponse(
            total=result["total"],
            items=[OrderResponse.model_validate(o) for o in result["items"]]
        )
    
    @patch("/{order_id:int}")
    async def update_order(
        self,
        order_id: int,
        data: OrderUpdate,
        order_service: Annotated[OrderService, Dependency(skip_validation=True)],
    ) -> OrderResponse:
        order = await order_service.update(order_id, data.model_dump(exclude_unset=True))
        return OrderResponse.model_validate(order)

    @delete("/{order_id:int}")
    @handle_db_errors
    async def delete_order(
        self,
        order_service: Annotated[OrderService, Dependency(skip_validation=True)],
        order_id: int = Parameter(gt=0),
    ) -> None:
        order = await order_service.get_by_id(order_id)
        if not order:
            raise NotFoundException(detail=f"Order with ID {order_id} not found")
        await order_service.delete(order_id)
