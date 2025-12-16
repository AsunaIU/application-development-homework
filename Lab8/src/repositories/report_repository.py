from datetime import date
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.order_report import OrderReport


class ReportRepository:
    """Репозиторий для работы с отчетами."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_report_by_date(self, report_date: date) -> List[OrderReport]:
        """Получить отчет за конкретную дату."""
        query = select(OrderReport).where(OrderReport.report_at == report_date)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_reports(self) -> List[OrderReport]:
        """Получить все отчеты."""
        query = select(OrderReport).order_by(
            OrderReport.report_at.desc(),
            OrderReport.order_id
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
