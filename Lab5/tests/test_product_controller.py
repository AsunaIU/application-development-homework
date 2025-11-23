import pytest
from typing import Protocol, Annotated
from polyfactory.factories.pydantic_factory import ModelFactory
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.di import Provide
from litestar.params import Dependency
from litestar.testing import create_test_client

from src.controllers.product_controller import ProductController
from src.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse


class ProductService(Protocol):
    async def get_by_id(self, product_id: int): ...
    async def get_by_filter(self, count: int, page: int): ...
    async def create(self, data: ProductCreate): ...
    async def update(self, product_id: int, data: ProductUpdate): ...
    async def delete(self, product_id: int): ...


class ProductCreateFactory(ModelFactory[ProductCreate]):
    __model__ = ProductCreate


class ProductUpdateFactory(ModelFactory[ProductUpdate]):
    __model__ = ProductUpdate


class ProductResponseFactory(ModelFactory[ProductResponse]):
    __model__ = ProductResponse


@pytest.fixture()
def product_create():
    return ProductCreateFactory.build()


@pytest.fixture()
def product_update():
    return ProductUpdateFactory.build()


@pytest.fixture()
def product_response():
    return ProductResponseFactory.build()


@pytest.mark.asyncio
async def test_get_product_by_id(product_response: ProductResponse):
    """Test retrieving a product by ID"""
    
    class MockProductService:
        async def get_by_id(self, product_id: int):
            return product_response
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.get(f"/products/{product_response.id}")
        assert response.status_code == HTTP_200_OK
        assert response.json() == product_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_get_product_by_id_not_found():
    """Test retrieving a non-existent product"""
    
    class MockProductService:
        async def get_by_id(self, product_id: int):
            return None
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.get("/products/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_all_products(product_response: ProductResponse):
    """Test listing all products with pagination"""
    products = [product_response]
    
    class MockProductService:
        async def get_by_filter(self, count: int, page: int):
            return {"total": 1, "items": products}
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.get("/products?count=10&page=1")
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0] == product_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_get_all_products_default_pagination(product_response: ProductResponse):
    """Test listing products with default pagination values"""
    products = [product_response]
    
    class MockProductService:
        async def get_by_filter(self, count: int, page: int):
            assert count == 10
            assert page == 1
            return {"total": 1, "items": products}
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.get("/products")
        assert response.status_code == HTTP_200_OK


@pytest.mark.asyncio
async def test_create_product(product_create: ProductCreate, product_response: ProductResponse):
    """Test creating a new product"""
    
    class MockProductService:
        async def create(self, data: ProductCreate):
            return product_response
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.post("/products", json=product_create.model_dump())
        assert response.status_code == HTTP_201_CREATED
        assert response.json() == product_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_update_product(product_response: ProductResponse, product_update: ProductUpdate):
    """Test updating a product"""
    
    class MockProductService:
        async def update(self, product_id: int, data: ProductUpdate):
            return product_response
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.put(
            f"/products/{product_response.id}",
            json=product_update.model_dump()
        )
        assert response.status_code == HTTP_200_OK
        assert response.json() == product_response.model_dump(mode="json")


@pytest.mark.asyncio
async def test_update_product_not_found(product_update: ProductUpdate):
    """Test updating a non-existent product"""
    
    class MockProductService:
        async def update(self, product_id: int, data: ProductUpdate):
            return None
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.put("/products/999", json=product_update.model_dump())
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product(product_response: ProductResponse):
    """Test deleting a product"""
    
    class MockProductService:
        async def get_by_id(self, product_id: int):
            return product_response
        
        async def delete(self, product_id: int):
            pass
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.delete(f"/products/{product_response.id}")
        assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_product_not_found():
    """Test deleting a non-existent product"""
    
    class MockProductService:
        async def get_by_id(self, product_id: int):
            return None
    
    with create_test_client(
        route_handlers=[ProductController],
        dependencies={"product_service": Provide(lambda: MockProductService(), sync_to_thread=False)}
    ) as client:
        response = client.delete("/products/999")
        assert response.status_code == 404
