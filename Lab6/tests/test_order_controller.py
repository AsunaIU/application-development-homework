import pytest
from typing import Protocol
from unittest.mock import AsyncMock
from polyfactory.factories.pydantic_factory import ModelFactory
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.di import Provide
from litestar.testing import AsyncTestClient, create_test_client
from litestar.exceptions import NotFoundException

from src.controllers.order_controller import OrderController
from src.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderUpdate


class OrderService(Protocol):
    async def create_order(self, data: dict): ...
    async def get_by_id(self, order_id: int): ...
    async def get_by_filter(self, count: int, page: int): ...
    async def update(self, order_id: int, data: dict): ...
    async def delete(self, order_id: int): ...


class OrderCreateFactory(ModelFactory[OrderCreate]):
    __model__ = OrderCreate


class OrderResponseFactory(ModelFactory[OrderResponse]):
    __model__ = OrderResponse


class OrderUpdateFactory(ModelFactory[OrderUpdate]):
    __model__ = OrderUpdate


@pytest.fixture()
def order_create():
    return OrderCreateFactory.build()


@pytest.fixture()
def order_response():
    return OrderResponseFactory.build()


@pytest.fixture()
def order_update():
    return OrderUpdateFactory.build()


@pytest.mark.asyncio
async def test_create_order(order_create: OrderCreate, order_response: OrderResponse):
    """Test creating a new order"""

    class MockOrderService:
        async def create_order(self, data: dict):
            return order_response

    with create_test_client(
        route_handlers=[OrderController],
        dependencies={
            "order_service": Provide(lambda: MockOrderService(), sync_to_thread=False)
        },
    ) as client:
        response = client.post("/orders", json=order_create.model_dump())
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == order_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_get_order_by_id(order_response: OrderResponse):
    """Test retrieving an order by ID"""

    class MockOrderService:
        async def get_by_id(self, order_id: int):
            return order_response

    with create_test_client(
        route_handlers=[OrderController],
        dependencies={
            "order_service": Provide(lambda: MockOrderService(), sync_to_thread=False)
        },
    ) as client:
        response = client.get(f"/orders/{order_response.id}")
        assert response.status_code == HTTP_200_OK
        assert response.json() == order_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_get_order_by_id_not_found():
    """Test retrieving a non-existent order"""

    class MockOrderService:
        async def get_by_id(self, order_id: int):
            return None

    with create_test_client(
        route_handlers=[OrderController],
        dependencies={
            "order_service": Provide(lambda: MockOrderService(), sync_to_thread=False)
        },
    ) as client:
        response = client.get("/orders/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_orders(order_response: OrderResponse):
    """Test listing orders with pagination"""
    orders = [order_response]

    class MockOrderService:
        async def get_by_filter(self, count: int, page: int):
            return {"total": 1, "items": orders}

    with create_test_client(
        route_handlers=[OrderController],
        dependencies={
            "order_service": Provide(lambda: MockOrderService(), sync_to_thread=False)
        },
    ) as client:
        response = client.get("/orders?count=10&page=1")
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0] == order_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_update_order(order_response: OrderResponse, order_update: OrderUpdate):
    """Test updating an order"""

    class MockOrderService:
        async def update(self, order_id: int, data: dict):
            return order_response

    with create_test_client(
        route_handlers=[OrderController],
        dependencies={
            "order_service": Provide(lambda: MockOrderService(), sync_to_thread=False)
        },
    ) as client:
        response = client.patch(
            f"/orders/{order_response.id}",
            json=order_update.model_dump(exclude_unset=True),
        )
        assert response.status_code == HTTP_200_OK
        assert response.json() == order_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_delete_order(order_response: OrderResponse):
    """Test deleting an order"""

    class MockOrderService:
        async def get_by_id(self, order_id: int):
            return order_response

        async def delete(self, order_id: int):
            pass

    with create_test_client(
        route_handlers=[OrderController],
        dependencies={
            "order_service": Provide(lambda: MockOrderService(), sync_to_thread=False)
        },
    ) as client:
        response = client.delete(f"/orders/{order_response.id}")
        assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_order_not_found():
    """Test deleting a non-existent order"""

    class MockOrderService:
        async def get_by_id(self, order_id: int):
            return None

    with create_test_client(
        route_handlers=[OrderController],
        dependencies={
            "order_service": Provide(lambda: MockOrderService(), sync_to_thread=False)
        },
    ) as client:
        response = client.delete("/orders/999")
        assert response.status_code == 404
