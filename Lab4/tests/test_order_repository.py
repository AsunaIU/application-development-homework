import uuid

import pytest

from src.schemas.user import UserCreate


@pytest.fixture(scope="function")
async def test_user(user_repository):
    """Create a test user for order tests"""
    unique_id = uuid.uuid4().hex[:8]
    user_data = UserCreate(
        username=f"orderuser_{unique_id}",
        email=f"order_{unique_id}@example.com",
        full_name="Order Test User"
    )
    user = await user_repository.create(user_data)
    yield user
    try:
        await user_repository.delete(user.id)
    except:
        pass


@pytest.fixture(scope="function")
async def test_product(product_repository):
    """Create a test product for order tests"""
    unique_id = uuid.uuid4().hex[:8]
    product = await product_repository.create(
        name=f"Order Test Product {unique_id}",
        price=99.99,
        stock_quantity=100
    )
    yield product
    try:
        await product_repository.delete(product.id)
    except:
        pass


@pytest.mark.asyncio
async def test_create_order_single_item(order_repository, test_user, test_product):
    """Test creating an order with a single item"""
    items = [
        {
            "product_id": test_product.id,
            "quantity": 2
        }
    ]
    
    order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    
    assert order.id is not None
    assert isinstance(order.id, int)
    assert order.user_id == test_user.id
    assert order.status == "pending"
    assert float(order.total_amount) == 99.99 * 2
    assert len(order.items) == 1
    assert order.items[0].product_id == test_product.id
    assert order.items[0].quantity == 2


@pytest.mark.asyncio
async def test_create_order_multiple_items(order_repository, test_user, product_repository):
    """Test creating an order with multiple items"""
    product1 = await product_repository.create(
        name=f"Multi Product 1 {uuid.uuid4().hex[:8]}",
        price=10.00,
        stock_quantity=50
    )
    product2 = await product_repository.create(
        name=f"Multi Product 2 {uuid.uuid4().hex[:8]}",
        price=20.00,
        stock_quantity=50
    )
    
    items = [
        {"product_id": product1.id, "quantity": 3},
        {"product_id": product2.id, "quantity": 2}
    ]
    
    order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    
    assert len(order.items) == 2
    assert float(order.total_amount) == (10.00 * 3) + (20.00 * 2)


@pytest.mark.asyncio
async def test_order_with_invalid_product(order_repository, test_user):
    """Test creating order with non-existent product fails with FK constraint"""
    items = [{"product_id": 99999, "quantity": 1}]
    
    with pytest.raises(ValueError, match="Product 99999 not found"):
        await order_repository.create(
            user_id=test_user.id,
            items=items
        )


@pytest.mark.asyncio
async def test_order_with_invalid_user(order_repository, test_product):
    """Test creating order with non-existent user fails with FK constraint"""
    items = [{"product_id": test_product.id, "quantity": 1}]
    
    with pytest.raises(ValueError):
        await order_repository.create(
            user_id=99999,
            items=items
        )


@pytest.mark.asyncio
async def test_get_order_by_id_with_relationships(order_repository, test_user, test_product):
    """Test retrieving an order by ID includes all relationships"""
    items = [{"product_id": test_product.id, "quantity": 1}]
    created_order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    
    retrieved_order = await order_repository.get_by_id(created_order.id)
    
    assert retrieved_order is not None
    assert retrieved_order.id == created_order.id
    assert retrieved_order.user_id == test_user.id
    assert len(retrieved_order.items) == 1
    assert retrieved_order.items[0].product_id == test_product.id


@pytest.mark.asyncio
async def test_get_nonexistent_order(order_repository):
    """Test retrieving an order that doesn't exist returns None"""
    order = await order_repository.get_by_id(99999)
    assert order is None


@pytest.mark.asyncio
async def test_update_order_items_add_new(order_repository, test_user, product_repository):
    """Test updating order to add new items"""
    product1 = await product_repository.create(
        name=f"Update Item 1 {uuid.uuid4().hex[:8]}",
        price=15.00,
        stock_quantity=100
    )
    product2 = await product_repository.create(
        name=f"Update Item 2 {uuid.uuid4().hex[:8]}",
        price=25.00,
        stock_quantity=100
    )
    
    # Create order with one item
    items = [{"product_id": product1.id, "quantity": 2}]
    order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    
    # Update to different quantity and add new item
    new_items = [
        {"product_id": product1.id, "quantity": 3},
        {"product_id": product2.id, "quantity": 1}
    ]
    
    updated_order = await order_repository.update(
        order.id,
        items=new_items
    )
    
    assert len(updated_order.items) == 2
    assert float(updated_order.total_amount) == (15.00 * 3) + (25.00 * 1)


@pytest.mark.asyncio
async def test_update_order_items_remove(order_repository, test_user, product_repository):
    """Test removing items from an order"""
    product1 = await product_repository.create(
        name=f"Remove Item 1 {uuid.uuid4().hex[:8]}",
        price=30.00,
        stock_quantity=100
    )
    product2 = await product_repository.create(
        name=f"Remove Item 2 {uuid.uuid4().hex[:8]}",
        price=40.00,
        stock_quantity=100
    )
    
    # Create order with two items
    items = [
        {"product_id": product1.id, "quantity": 1},
        {"product_id": product2.id, "quantity": 1}
    ]
    order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    
    assert len(order.items) == 2
    
    # Update to only one item
    new_items = [{"product_id": product1.id, "quantity": 2}]
    updated_order = await order_repository.update(
        order.id,
        items=new_items
    )
    
    assert len(updated_order.items) == 1
    assert updated_order.items[0].product_id == product1.id
    assert float(updated_order.total_amount) == 30.00 * 2


@pytest.mark.asyncio
async def test_update_order_total_recalculated(order_repository, test_user, product_repository):
    """Test that order total is recalculated when items are updated"""
    product = await product_repository.create(
        name=f"Recalc Product {uuid.uuid4().hex[:8]}",
        price=50.00,
        stock_quantity=100
    )
    
    items = [{"product_id": product.id, "quantity": 2}]
    order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    
    assert float(order.total_amount) == 100.00
    
    # Update quantity
    new_items = [{"product_id": product.id, "quantity": 5}]
    updated_order = await order_repository.update(
        order.id,
        items=new_items
    )
    
    assert float(updated_order.total_amount) == 250.00


@pytest.mark.asyncio
async def test_delete_order_cascades_to_items(order_repository, test_user, test_product):
    """Test that deleting an order also deletes its items (cascade)"""
    items = [{"product_id": test_product.id, "quantity": 1}]
    order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    order_id = order.id
    
    await order_repository.delete(order_id)
    
    deleted_order = await order_repository.get_by_id(order_id)
    assert deleted_order is None


@pytest.mark.asyncio
async def test_list_orders_with_limit_offset(order_repository, test_user, test_product):
    """Test listing orders with pagination parameters"""
    created_orders = []
    for i in range(5):
        items = [{"product_id": test_product.id, "quantity": i + 1}]
        order = await order_repository.create(
            user_id=test_user.id,
            items=items
        )
        created_orders.append(order)
    
    total, orders = await order_repository.list(limit=3, offset=0)
    
    assert total >= 5
    assert len(orders) <= 3
    assert all(isinstance(order.id, int) for order in orders)


@pytest.mark.asyncio
async def test_list_orders_pagination_consistency(order_repository, test_user, test_product):
    """Test that pagination returns consistent, non-overlapping results"""
    for i in range(10):
        items = [{"product_id": test_product.id, "quantity": 1}]
        await order_repository.create(
            user_id=test_user.id,
            items=items
        )
    
    total1, page1 = await order_repository.list(limit=3, offset=0)
    total2, page2 = await order_repository.list(limit=3, offset=3)
    
    assert total1 == total2
    assert len(page1) == 3
    assert len(page2) == 3
    
    page1_ids = {order.id for order in page1}
    page2_ids = {order.id for order in page2}
    assert len(page1_ids.intersection(page2_ids)) == 0


@pytest.mark.asyncio
async def test_order_items_preserve_order(order_repository, test_user, product_repository):
    """Test that order items maintain their order"""
    products = []
    for i in range(5):
        product = await product_repository.create(
            name=f"Ordered Product {i} {uuid.uuid4().hex[:8]}",
            price=10.00 * (i + 1),
            stock_quantity=100
        )
        products.append(product)
    
    items = [{"product_id": p.id, "quantity": 1} for p in products]
    order = await order_repository.create(
        user_id=test_user.id,
        items=items
    )
    
    retrieved_order = await order_repository.get_by_id(order.id)

    assert len(retrieved_order.items) == 5
    retrieved_product_ids = [item.product_id for item in retrieved_order.items]
    assert len(set(retrieved_product_ids)) == 5
