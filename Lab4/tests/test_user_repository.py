import pytest

from src.schemas.user import UserCreate, UserUpdate


@pytest.mark.asyncio
async def test_create_user(user_repository):
    """Test creating a new user"""
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User"
    )
    
    user = await user_repository.create(user_data)
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository):
    """Test retrieving a user by ID"""
    user_data = UserCreate(
        username="getuser",
        email="get@example.com",
        full_name="Get User"
    )
    created_user = await user_repository.create(user_data)
    
    retrieved_user = await user_repository.get_by_id(created_user.id)
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == "getuser"


@pytest.mark.asyncio
async def test_get_nonexistent_user(user_repository):
    """Test retrieving a user that doesn't exist"""
    user = await user_repository.get_by_id(99999)
    assert user is None


@pytest.mark.asyncio
async def test_update_user(user_repository):
    """Test updating a user"""
    user_data = UserCreate(
        username="updateuser",
        email="update@example.com",
        full_name="Update User"
    )
    user = await user_repository.create(user_data)
    
    update_data = UserUpdate(full_name="Updated Name", is_active=False)
    updated_user = await user_repository.update(user.id, update_data)
    
    assert updated_user.full_name == "Updated Name"
    assert updated_user.is_active is False
    assert updated_user.username == "updateuser"  # unchanged


@pytest.mark.asyncio
async def test_delete_user(user_repository):
    """Test deleting a user"""
    user_data = UserCreate(
        username="deleteuser",
        email="delete@example.com"
    )
    user = await user_repository.create(user_data)
    user_id = user.id
    
    await user_repository.delete(user_id)
    
    deleted_user = await user_repository.get_by_id(user_id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_get_users_with_filter(user_repository):
    """Test retrieving users with pagination"""
    for i in range(5):
        user_data = UserCreate(
            username=f"filteruser{i}",
            email=f"filter{i}@example.com"
        )
        await user_repository.create(user_data)
    
    users = await user_repository.get_by_filter(count=3, page=1)
    
    assert len(users) <= 3


@pytest.mark.asyncio
async def test_count_users(user_repository):
    """Test counting users"""
    initial_count = await user_repository.count()
    
    user_data = UserCreate(
        username="countuser",
        email="count@example.com"
    )
    await user_repository.create(user_data)
    
    new_count = await user_repository.count()
    assert new_count == initial_count + 1
