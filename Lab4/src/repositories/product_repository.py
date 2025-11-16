from typing import List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **data) -> Product:
        product = Product(**data)
        self.session.add(product)
        await self.session.commit()
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        return await self.session.get(Product, product_id)

    async def list(self) -> List[Product]:
        res = await self.session.execute(select(Product))
        return res.scalars().all()

    async def get_by_filter(self, count: int = 10, page: int = 1) -> Dict[str, Any]:
        """
        Get paginated products.
        Returns: {"total": int, "items": List[Product]}
        """
        if page < 1:
            page = 1
        if count < 1:
            count = 10

        count_query = select(func.count()).select_from(Product)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * count
        query = select(Product).offset(offset).limit(count)
        result = await self.session.execute(query)
        items = result.scalars().all()

        return {"total": total, "items": items}

    async def update(self, product_id: int, **patch) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        for k, v in patch.items():
            setattr(product, k, v)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: int) -> None:
        product = await self.get_by_id(product_id)
        if product:
            await self.session.delete(product)
            await self.session.commit()
