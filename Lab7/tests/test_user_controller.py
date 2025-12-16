import pytest
from typing import Protocol
from polyfactory.factories.pydantic_factory import ModelFactory
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.di import Provide
from litestar.testing import create_test_client

from src.controllers.user_controller import UserController
from src.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse


class UserService(Protocol):
    async def get_by_id(self, user_id: int): ...
    async def get_by_filter(self, count: int, page: int): ...
    async def create(self, data: UserCreate): ...
    async def update(self, user_id: int, data: UserUpdate): ...
    async def delete(self, user_id: int): ...


class UserCreateFactory(ModelFactory[UserCreate]):
    __model__ = UserCreate


class UserUpdateFactory(ModelFactory[UserUpdate]):
    __model__ = UserUpdate


class UserResponseFactory(ModelFactory[UserResponse]):
    __model__ = UserResponse


@pytest.fixture()
def user_create():
    return UserCreateFactory.build()


@pytest.fixture()
def user_update():
    return UserUpdateFactory.build()


@pytest.fixture()
def user_response():
    return UserResponseFactory.build()


@pytest.mark.asyncio
async def test_get_user_by_id(user_response: UserResponse):
    """Test retrieving a user by ID"""

    class MockUserService:
        async def get_by_id(self, user_id: int):
            return user_response

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.get(f"/users/{user_response.id}")
        assert response.status_code == HTTP_200_OK
        assert response.json() == user_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_get_user_by_id_not_found():
    """Test retrieving a non-existent user"""

    class MockUserService:
        async def get_by_id(self, user_id: int):
            return None

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.get("/users/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_all_users(user_response: UserResponse):
    """Test listing all users with pagination"""
    users = [user_response]

    class MockUserService:
        async def get_by_filter(self, count: int, page: int):
            return {"total": 1, "items": users}

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.get("/users?count=10&page=1")
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0] == user_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_get_all_users_default_pagination(user_response: UserResponse):
    """Test listing users with default pagination values"""
    users = [user_response]

    class MockUserService:
        async def get_by_filter(self, count: int, page: int):
            assert count == 10
            assert page == 1
            return {"total": 1, "items": users}

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.get("/users")
        assert response.status_code == HTTP_200_OK


@pytest.mark.asyncio
async def test_create_user(user_create: UserCreate, user_response: UserResponse):
    """Test creating a new user"""

    class MockUserService:
        async def create(self, data: UserCreate):
            return user_response

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.post("/users", json=user_create.model_dump())
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == user_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_update_user(user_response: UserResponse, user_update: UserUpdate):
    """Test updating a user"""

    class MockUserService:
        async def update(self, user_id: int, data: UserUpdate):
            return user_response

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.put(
            f"/users/{user_response.id}", json=user_update.model_dump()
        )
        assert response.status_code == HTTP_200_OK
        assert response.json() == user_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_update_user_not_found(user_update: UserUpdate):
    """Test updating a non-existent user"""

    class MockUserService:
        async def update(self, user_id: int, data: UserUpdate):
            return None

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.put("/users/999", json=user_update.model_dump())
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user(user_response: UserResponse):
    """Test deleting a user"""

    class MockUserService:
        async def get_by_id(self, user_id: int):
            return user_response

        async def delete(self, user_id: int):
            pass

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.delete(f"/users/{user_response.id}")
        assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_user_not_found():
    """Test deleting a non-existent user"""

    class MockUserService:
        async def get_by_id(self, user_id: int):
            return None

    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "user_service": Provide(lambda: MockUserService(), sync_to_thread=False)
        },
    ) as client:
        response = client.delete("/users/999")
        assert response.status_code == 404
