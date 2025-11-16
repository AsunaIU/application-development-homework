from decimal import Decimal

import pytest


@pytest.mark.asyncio
async def test_create_product(product_repository):
    """Test creating a new product"""
    product = await product_repository.create(
        name="Test Product",
        price=29.99,
        stock_quantity=100
    )
    
    assert product.id is not None
    assert product.name == "Test Product"
    assert float(product.price) == 29.99
    assert product.stock_quantity == 100


@pytest.mark.asyncio
async def test_get_product_by_id(product_repository):
    """Test retrieving a product by ID"""
    created_product = await product_repository.create(
        name="Get Product",
        price=19.99,
        stock_quantity=50
    )
    
    retrieved_product = await product_repository.get_by_id(created_product.id)
    
    assert retrieved_product is not None
    assert retrieved_product.id == created_product.id
    assert retrieved_product.name == "Get Product"


@pytest.mark.asyncio
async def test_get_nonexistent_product(product_repository):
    """Test retrieving a product that doesn't exist"""
    product = await product_repository.get_by_id(99999)
    assert product is None


@pytest.mark.asyncio
async def test_update_product(product_repository):
    """Test updating a product"""
    product = await product_repository.create(
        name="Update Product",
        price=39.99,
        stock_quantity=75
    )
    
    updated_product = await product_repository.update(
        product.id,
        name="Updated Product",
        price=49.99
    )
    
    assert updated_product.name == "Updated Product"
    assert float(updated_product.price) == 49.99
    assert updated_product.stock_quantity == 75  # unchanged


@pytest.mark.asyncio
async def test_update_product_stock(product_repository):
    """Test updating only product stock"""
    product = await product_repository.create(
        name="Stock Product",
        price=25.00,
        stock_quantity=100
    )
    
    updated_product = await product_repository.update(
        product.id,
        stock_quantity=50
    )
    
    assert updated_product.stock_quantity == 50
    assert updated_product.name == "Stock Product"
    assert float(updated_product.price) == 25.00


@pytest.mark.asyncio
async def test_delete_product(product_repository):
    """Test deleting a product"""
    product = await product_repository.create(
        name="Delete Product",
        price=15.99,
        stock_quantity=10
    )
    product_id = product.id
    
    await product_repository.delete(product_id)
    
    deleted_product = await product_repository.get_by_id(product_id)
    assert deleted_product is None


@pytest.mark.asyncio
async def test_list_products(product_repository):
    """Test listing products with pagination"""
    for i in range(5):
        await product_repository.create(
            name=f"List Product {i}",
            price=10.00 + i,
            stock_quantity=10 * i
        )
    
    result = await product_repository.get_by_filter(count=3, page=1)
    
    assert "total" in result
    assert "items" in result
    assert len(result["items"]) <= 3
    assert result["total"] >= 5

@pytest.mark.asyncio
async def test_list_products_pagination(product_repository):
    """Test product pagination"""
    for i in range(10):
        await product_repository.create(
            name=f"Page Product {i}",
            price=20.00,
            stock_quantity=10
        )
    
    page1_result = await product_repository.get_by_filter(count=3, page=1)
    page2_result = await product_repository.get_by_filter(count=3, page=2)
    
    page1 = page1_result["items"]
    page2 = page2_result["items"]
    
    assert len(page1) <= 3
    assert len(page2) <= 3
    assert page1_result["total"] >= 10
    
    if len(page1) > 0 and len(page2) > 0:
        assert page1[0].id != page2[0].id
