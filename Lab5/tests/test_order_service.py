import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.order_service import OrderService


@pytest.fixture
def mock_order_repository():
    """Mock order repository"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.list = AsyncMock()
    return repo


@pytest.fixture
def mock_product_repository():
    """Mock product repository"""
    repo = Mock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_user_repository():
    """Mock user repository"""
    repo = Mock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def order_service_with_mocks(mock_order_repository, mock_product_repository, mock_user_repository):
    """Create order service with mocked repositories"""
    return OrderService(
        order_repository=mock_order_repository,
        product_repository=mock_product_repository,
        user_repository=mock_user_repository
    )


@pytest.mark.asyncio
async def test_create_order_success(order_service_with_mocks, mock_user_repository, 
                                    mock_product_repository, mock_order_repository):
    """Test successful order creation with mocks"""
    mock_user = Mock(id=1, username="testuser")
    mock_user_repository.get_by_id.return_value = mock_user
    
    mock_product = Mock(id=1, price=50.0, stock_quantity=100)
    mock_product_repository.get_by_id.return_value = mock_product
    
    mock_order = Mock(id=1, user_id=1, status="pending", total_amount=100.0)
    mock_order_repository.create.return_value = mock_order
    
    order_data = {
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": 2}]
    }
    result = await order_service_with_mocks.create_order(order_data)
    
    assert result.id == 1
    assert result.user_id == 1
    mock_user_repository.get_by_id.assert_called_once_with(1)
    mock_product_repository.get_by_id.assert_called_once_with(1)
    mock_product_repository.update.assert_called_once_with(1, stock_quantity=98)
    mock_order_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_user_not_found(order_service_with_mocks, mock_user_repository):
    """Test order creation fails when user not found"""
    mock_user_repository.get_by_id.return_value = None
    
    order_data = {
        "user_id": 999,
        "items": [{"product_id": 1, "quantity": 1}]
    }
    
    with pytest.raises(ValueError, match="User not found"):
        await order_service_with_mocks.create_order(order_data)
    
    mock_user_repository.get_by_id.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_create_order_product_not_found(order_service_with_mocks, mock_user_repository, 
                                              mock_product_repository):
    """Test order creation fails when product not found"""
    mock_user = Mock(id=1, username="testuser")
    mock_user_repository.get_by_id.return_value = mock_user
    mock_product_repository.get_by_id.return_value = None
    
    order_data = {
        "user_id": 1,
        "items": [{"product_id": 999, "quantity": 1}]
    }
    
    with pytest.raises(ValueError, match="Product 999 not found"):
        await order_service_with_mocks.create_order(order_data)


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(order_service_with_mocks, mock_user_repository,
                                               mock_product_repository):
    """Test order creation fails with insufficient stock"""
    mock_user = Mock(id=1, username="testuser")
    mock_user_repository.get_by_id.return_value = mock_user
    
    mock_product = Mock(id=1, price=50.0, stock_quantity=5)
    mock_product_repository.get_by_id.return_value = mock_product
    
    order_data = {
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": 10}]
    }
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        await order_service_with_mocks.create_order(order_data)
    
    mock_product_repository.update.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_no_items(order_service_with_mocks, mock_user_repository):
    """Test order creation fails with no items"""
    mock_user = Mock(id=1, username="testuser")
    mock_user_repository.get_by_id.return_value = mock_user
    
    order_data = {
        "user_id": 1,
        "items": []
    }
    
    with pytest.raises(ValueError, match="Order must have at least one item"):
        await order_service_with_mocks.create_order(order_data)


@pytest.mark.asyncio
async def test_create_order_zero_quantity(order_service_with_mocks, mock_user_repository):
    """Test order creation fails with zero quantity"""
    mock_user = Mock(id=1, username="testuser")
    mock_user_repository.get_by_id.return_value = mock_user
    
    order_data = {
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": 0}]
    }
    
    with pytest.raises(ValueError, match="Quantity must be greater than 0"):
        await order_service_with_mocks.create_order(order_data)


@pytest.mark.asyncio
async def test_create_order_negative_quantity(order_service_with_mocks, mock_user_repository):
    """Test order creation fails with negative quantity"""
    mock_user = Mock(id=1, username="testuser")
    mock_user_repository.get_by_id.return_value = mock_user
    
    order_data = {
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": -5}]
    }
    
    with pytest.raises(ValueError, match="Quantity must be greater than 0"):
        await order_service_with_mocks.create_order(order_data)


@pytest.mark.asyncio
async def test_create_order_multiple_items_stock_validation(order_service_with_mocks, 
                                                           mock_user_repository,
                                                           mock_product_repository):
    """Test that stock validation happens before any updates"""
    mock_user = Mock(id=1, username="testuser")
    mock_user_repository.get_by_id.return_value = mock_user
    
    def get_product(product_id):
        if product_id == 1:
            return Mock(id=1, price=10.0, stock_quantity=50)
        elif product_id == 2:
            return Mock(id=2, price=20.0, stock_quantity=3)
        return None
    
    mock_product_repository.get_by_id.side_effect = get_product
    
    order_data = {
        "user_id": 1,
        "items": [
            {"product_id": 1, "quantity": 5},
            {"product_id": 2, "quantity": 10}
        ]
    }
    
    with pytest.raises(ValueError, match="Insufficient stock"):
        await order_service_with_mocks.create_order(order_data)
    
    mock_product_repository.update.assert_not_called()


@pytest.mark.asyncio
async def test_get_order_by_id(order_service_with_mocks, mock_order_repository):
    """Test retrieving order by ID"""
    mock_order = Mock(id=1, user_id=1, status="pending")
    mock_order_repository.get_by_id.return_value = mock_order
    
    result = await order_service_with_mocks.get_by_id(1)
    
    assert result.id == 1
    mock_order_repository.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_order_not_found(order_service_with_mocks, mock_order_repository):
    """Test retrieving non-existent order raises error"""
    mock_order_repository.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match="Order 999 not found"):
        await order_service_with_mocks.get_by_id(999)


@pytest.mark.asyncio
async def test_update_order_status(order_service_with_mocks, mock_order_repository):
    """Test updating order status"""
    mock_order = Mock(id=1, user_id=1, status="pending", items=[])
    mock_updated_order = Mock(id=1, user_id=1, status="shipped", items=[])
    
    mock_order_repository.get_by_id.return_value = mock_order
    mock_order_repository.update.return_value = mock_updated_order
    
    result = await order_service_with_mocks.update(1, {"status": "shipped"})
    
    assert result.status == "shipped"
    mock_order_repository.update.assert_called_once_with(1, status="shipped")


@pytest.mark.asyncio
async def test_update_order_invalid_status(order_service_with_mocks, mock_order_repository):
    """Test updating order with invalid status fails"""
    mock_order = Mock(id=1, user_id=1, status="pending", items=[])
    mock_order_repository.get_by_id.return_value = mock_order
    
    with pytest.raises(ValueError, match="Invalid status"):
        await order_service_with_mocks.update(1, {"status": "invalid_status"})


@pytest.mark.asyncio
async def test_update_order_not_found(order_service_with_mocks, mock_order_repository):
    """Test updating non-existent order raises error"""
    mock_order_repository.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match="Order 999 not found"):
        await order_service_with_mocks.update(999, {"status": "shipped"})


@pytest.mark.asyncio
async def test_cancel_order_restores_stock(order_service_with_mocks, mock_order_repository,
                                          mock_product_repository):
    """Test canceling an order restores product stock"""
    mock_item = Mock(product_id=1, quantity=5)
    mock_order = Mock(id=1, user_id=1, status="pending", items=[mock_item])
    mock_updated_order = Mock(id=1, user_id=1, status="cancelled", items=[mock_item])
    
    mock_order_repository.get_by_id.return_value = mock_order
    mock_order_repository.update.return_value = mock_updated_order
    
    mock_product = Mock(id=1, stock_quantity=95)
    mock_product_repository.get_by_id.return_value = mock_product
    
    result = await order_service_with_mocks.update(1, {"status": "cancelled"})
    
    mock_product_repository.get_by_id.assert_called_once_with(1)
    mock_product_repository.update.assert_called_once_with(1, stock_quantity=100)
    assert result.status == "cancelled"

@pytest.mark.asyncio
async def test_delete_order(order_service_with_mocks, mock_order_repository):
    """Test deleting an order"""
    mock_order = Mock(id=1, user_id=1, status="pending")
    mock_order_repository.get_by_id.return_value = mock_order
    
    await order_service_with_mocks.delete(1)
    
    mock_order_repository.get_by_id.assert_called_once_with(1)
    mock_order_repository.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_order_not_found(order_service_with_mocks, mock_order_repository):
    """Test deleting non-existent order raises error"""
    mock_order_repository.get_by_id.return_value = None
    
    with pytest.raises(ValueError, match="Order 999 not found"):
        await order_service_with_mocks.delete(999)


@pytest.mark.asyncio
async def test_get_by_filter_pagination(order_service_with_mocks, mock_order_repository):
    """Test getting orders with pagination"""
    mock_orders = [Mock(id=i) for i in range(1, 6)]
    mock_order_repository.list.return_value = (5, mock_orders[:3])
    
    result = await order_service_with_mocks.get_by_filter(count=3, page=1)
    
    assert result["total"] == 5
    assert len(result["items"]) == 3
    mock_order_repository.list.assert_called_once_with(
        limit=3, offset=0, user_id=None, status=None
    )


@pytest.mark.asyncio
async def test_get_by_filter_pagination_pages_differ(order_service_with_mocks, 
                                                     mock_order_repository):
    """Test pagination returns different results for different pages"""
    page1_orders = [Mock(id=i) for i in range(1, 4)]
    page2_orders = [Mock(id=i) for i in range(4, 7)]
    
    mock_order_repository.list.side_effect = [
        (10, page1_orders),
        (10, page2_orders)
    ]
    
    page1 = await order_service_with_mocks.get_by_filter(count=3, page=1)
    page2 = await order_service_with_mocks.get_by_filter(count=3, page=2)
    
    assert len(page1["items"]) == 3
    assert len(page2["items"]) == 3
    assert page1["items"][0].id != page2["items"][0].id


@pytest.mark.asyncio
async def test_filter_by_user_id(order_service_with_mocks, mock_order_repository):
    """Test filtering orders by user_id"""
    user1_orders = [Mock(id=i, user_id=1) for i in range(1, 4)]
    mock_order_repository.list.return_value = (3, user1_orders)
    
    result = await order_service_with_mocks.get_by_filter(user_id=1)
    
    assert result["total"] == 3
    assert all(order.user_id == 1 for order in result["items"])
    mock_order_repository.list.assert_called_once_with(
        limit=10, offset=0, user_id=1, status=None
    )


@pytest.mark.asyncio
async def test_filter_by_status(order_service_with_mocks, mock_order_repository):
    """Test filtering orders by status"""
    pending_orders = [Mock(id=i, status="pending") for i in range(1, 4)]
    mock_order_repository.list.return_value = (3, pending_orders)
    
    result = await order_service_with_mocks.get_by_filter(status="pending")
    
    assert result["total"] == 3
    assert all(order.status == "pending" for order in result["items"])
    mock_order_repository.list.assert_called_once_with(
        limit=10, offset=0, user_id=None, status="pending"
    )


@pytest.mark.asyncio
async def test_filter_fallback_when_repository_lacks_filters(order_service_with_mocks,
                                                            mock_order_repository):
    """Test fallback behavior when repository doesn't support filtering"""
    all_orders = [
        Mock(id=1, user_id=1, status="pending"),
        Mock(id=2, user_id=2, status="pending"),
        Mock(id=3, user_id=1, status="shipped"),
    ]
    
    mock_order_repository.list.side_effect = [
        TypeError("unexpected keyword argument"),
        (3, all_orders)
    ]
    
    result = await order_service_with_mocks.get_by_filter(user_id=1)
    
    assert result["total"] == 2
    assert all(order.user_id == 1 for order in result["items"])
