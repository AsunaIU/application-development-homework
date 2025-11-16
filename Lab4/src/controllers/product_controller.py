from typing import Annotated

from litestar import Controller, get, post, put, delete
from litestar.params import Parameter, Dependency
from litestar.exceptions import NotFoundException, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError

from src.services.product_service import ProductService
from src.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from src.utils.db_error_handler import handle_db_errors


class ProductController(Controller):
    path = "/products"
    tags = ["Products"]
    
    @get("/{product_id:int}")
    @handle_db_errors
    async def get_product_by_id(
        self,
        product_service: Annotated[ProductService, Dependency(skip_validation=True)],
        product_id: int = Parameter(gt=0),
    ) -> ProductResponse:
        """Get product by ID"""
        product = await product_service.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail=f"Product with ID {product_id} not found")
        return ProductResponse.model_validate(product)
    
    @get()
    @handle_db_errors
    async def get_all_products(
        self,
        product_service: Annotated[ProductService, Dependency(skip_validation=True)],
        count: int = Parameter(default=10, gt=0, le=100),
        page: int = Parameter(default=1, gt=0),
    ) -> ProductListResponse:
        """Get all products with pagination"""
        result = await product_service.get_by_filter(count, page)
        return ProductListResponse(
            total=result["total"],
            items=[ProductResponse.model_validate(p) for p in result["items"]]
        )
    
    @post()
    @handle_db_errors
    async def create_product(
        self,
        product_service: Annotated[ProductService, Dependency(skip_validation=True)],
        data: ProductCreate,
    ) -> ProductResponse:
        product = await product_service.create(data)
        return ProductResponse.model_validate(product)
    
    @put("/{product_id:int}")
    @handle_db_errors
    async def update_product(
        self,
        product_service: Annotated[ProductService, Dependency(skip_validation=True)],
        product_id: int = Parameter(gt=0),
        data: ProductUpdate = None,
    ) -> ProductResponse:
        product = await product_service.update(product_id, data)
        if not product:
            raise NotFoundException(detail=f"Product with ID {product_id} not found")
        return ProductResponse.model_validate(product)
    
    @delete("/{product_id:int}")
    @handle_db_errors
    async def delete_product(
        self,
        product_service: Annotated[ProductService, Dependency(skip_validation=True)],
        product_id: int = Parameter(gt=0),
    ) -> None:
        product = await product_service.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail=f"Product with ID {product_id} not found")
        await product_service.delete(product_id)
