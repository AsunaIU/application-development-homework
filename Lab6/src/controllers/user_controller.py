from typing import Annotated

from litestar import Controller, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.params import Dependency, Parameter

from src.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from src.services.user_service import UserService
from src.utils.db_error_handler import handle_db_errors


class UserController(Controller):
    path = "/users"
    tags = ["Users"]

    @get("/{user_id:int}")
    @handle_db_errors
    async def get_user_by_id(
        self,
        user_service: Annotated[UserService, Dependency(skip_validation=True)],
        user_id: int = Parameter(gt=0),
    ) -> UserResponse:
        """Get user by ID"""
        user = await user_service.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)

    @get()
    @handle_db_errors
    async def get_all_users(
        self,
        user_service: Annotated[UserService, Dependency(skip_validation=True)],
        count: int = Parameter(default=10, gt=0, le=100),
        page: int = Parameter(default=1, gt=0),
    ) -> UserListResponse:
        """Get all users"""
        result = await user_service.get_by_filter(count, page)
        return UserListResponse(
            total=result["total"],
            items=[UserResponse.model_validate(user) for user in result["items"]],
        )

    @post()
    @handle_db_errors
    async def create_user(
        self,
        user_service: Annotated[UserService, Dependency(skip_validation=True)],
        data: UserCreate,
    ) -> UserResponse:
        """Create a new user"""
        user = await user_service.create(data)
        return UserResponse.model_validate(user)

    @put("/{user_id:int}")
    @handle_db_errors
    async def update_user(
        self,
        user_service: Annotated[UserService, Dependency(skip_validation=True)],
        user_id: int = Parameter(gt=0),
        data: UserUpdate = None,
    ) -> UserResponse:
        """Update user data"""
        user = await user_service.update(user_id, data)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)

    @delete("/{user_id:int}")
    @handle_db_errors
    async def delete_user(
        self,
        user_service: Annotated[UserService, Dependency(skip_validation=True)],
        user_id: int = Parameter(gt=0),
    ) -> None:
        """Delete a user"""
        user = await user_service.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")

        await user_service.delete(user_id)
