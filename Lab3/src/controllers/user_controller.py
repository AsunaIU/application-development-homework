from functools import wraps

from litestar import Controller, get, post, put, delete
from litestar.params import Parameter
from litestar.exceptions import NotFoundException, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

from src.services.user_service import UserService
from src.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse


def handle_db_errors(func):
    """Decorator to catch DB and unexpected errors and convert them to proper HTTP responses"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            detail = "User with this data already exists"
            if "email" in str(e.orig).lower():
                detail = "Email already exists"
            elif "username" in str(e.orig).lower():
                detail = "Username already exists"
            raise HTTPException(status_code=409, detail=detail)
        except OperationalError:
            raise HTTPException(status_code=503, detail="Database unavailable, try again later")
        except NotFoundException:
            raise  # re-raise to preserve 404
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper


class UserController(Controller):
    path = "/users"

    @get("/{user_id:int}")
    @handle_db_errors
    async def get_user_by_id(
        self,
        user_service: UserService,
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
        user_service: UserService,
        count: int = Parameter(default=10, gt=0, le=100),
        page: int = Parameter(default=1, gt=0),
    ) -> UserListResponse:
        """Get all users"""
        result = await user_service.get_by_filter(count, page)
        return UserListResponse(
            total=result["total"],
            items=[UserResponse.model_validate(user) for user in result["items"]]
        )

    @post()
    @handle_db_errors
    async def create_user(
        self,
        user_service: UserService,
        data: UserCreate,
    ) -> UserResponse:
        """Create a new user"""
        user = await user_service.create(data)
        return UserResponse.model_validate(user)

    @put("/{user_id:int}")
    @handle_db_errors
    async def update_user(
        self,
        user_service: UserService,
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
        user_service: UserService,
        user_id: int = Parameter(gt=0),
    ) -> None:
        """Delete a user"""
        user = await user_service.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")

        await user_service.delete(user_id)
