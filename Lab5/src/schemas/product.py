from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    price: float
    stock_quantity: int


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    stock_quantity: int | None = None

    model_config = ConfigDict(extra="forbid")


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock_quantity: int

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    total: int
    items: list[ProductResponse]
