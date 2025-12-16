from datetime import date
from typing import List, Dict, Any, Optional

from litestar import Controller, get
from litestar.params import Parameter
from litestar.datastructures import ResponseHeader
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK

from src.services.report_service import ReportService


class ReportController(Controller):
    """Контроллер для работы с отчетами по заказам."""
    
    path = "/report"
    tags = ["reports"]
    
    @get(
        "/",
        summary="Получить отчеты по заказам",
        description=(
            "Возвращает отчет за конкретную дату или все отчеты, если дата не указана. "
            "Отчет формируется автоматически из таблиц orders и order_items."
        ),
        status_code=HTTP_200_OK,
    )
    async def get_reports(
        self,
        report_service: ReportService,
        report_date: Optional[date] = Parameter(
            default=None,
            query="date",
            description="Дата отчета в формате YYYY-MM-DD",
            required=False,
        ),
    ) -> List[Dict[str, Any]]:
        """
        Получить отчеты по заказам.
        
        Args:
            report_service: Сервис для работы с отчетами
            report_date: Опциональная дата для фильтрации
            
        Returns:
            List[Dict[str, Any]]: Список отчетов с полями:
                - report_at: дата отчета
                - order_id: ID заказа
                - count_product: количество продуктов в заказе
                - total_amount: общая стоимость заказа
            
        Raises:
            NotFoundException: Если отчеты не найдены
            
        Examples:
            GET /report/  # Все отчеты
            GET /report/?date=2024-12-12  # Отчеты за 12 декабря 2024
        """
        if report_date:
            reports = await report_service.get_report_by_date(report_date)
            if not reports:
                raise NotFoundException(
                    detail=f"Отчеты за дату {report_date.isoformat()} не найдены"
                )
        else:
            reports = await report_service.get_all_reports()
            if not reports:
                raise NotFoundException(detail="Отчеты не найдены")
        
        return reports
    
    @get(
        "/summary",
        summary="Получить сводку по отчету",
        description="Возвращает агрегированную статистику за указанную дату",
        status_code=HTTP_200_OK,
    )
    async def get_report_summary(
        self,
        report_service: ReportService,
        report_date: date = Parameter(
            query="date",
            description="Дата отчета в формате YYYY-MM-DD",
            required=True,
        ),
    ) -> Dict[str, Any]:
        """
        Получить сводку по отчету за дату.
        
        Args:
            report_service: Сервис для работы с отчетами
            report_date: Дата отчета
            
        Returns:
            Dict[str, Any]: Сводная статистика:
                - date: дата отчета
                - total_orders: всего заказов
                - total_products: всего продуктов
                - average_products_per_order: среднее кол-во продуктов на заказ
                - total_value: общая стоимость всех заказов за дату
                - average_order_value: средняя стоимость заказа
            
        Raises:
            NotFoundException: Если отчеты за дату не найдены
            
        Example:
            GET /report/summary?date=2024-12-12
        """
        reports = await report_service.get_report_by_date(report_date)
        
        if not reports:
            raise NotFoundException(
                detail=f"Отчеты за дату {report_date.isoformat()} не найдены"
            )
        
        total_orders = len(reports)
        total_products = sum(r["count_product"] for r in reports)
        total_value = sum(r["total_amount"] for r in reports)
        
        return {
            "date": report_date.isoformat(),
            "total_orders": total_orders,
            "total_products": total_products,
            "total_value": round(total_value, 2),
        }
