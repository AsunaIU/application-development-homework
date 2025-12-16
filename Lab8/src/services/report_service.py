from datetime import date
from typing import List, Dict, Any

from src.repositories.report_repository import ReportRepository


class ReportService:
    """Сервис для работы с отчетами."""
    
    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository
    
    def _serialize_report(self, report) -> Dict[str, Any]:
        """Преобразует объект OrderReport в словарь."""
        return {
            "report_at": report.report_at.isoformat() if report.report_at else None,
            "order_id": report.order_id,
            "count_product": report.count_product,
            "total_amount": float(report.total_amount) if report.total_amount else 0.0,
        }
    
    async def get_report_by_date(self, report_date: date) -> List[Dict[str, Any]]:
        """
        Получить отчет за конкретную дату.
        
        Args:
            report_date: Дата отчета
            
        Returns:
            Список словарей с данными отчетов
        """
        reports = await self.report_repository.get_report_by_date(report_date)
        return [self._serialize_report(report) for report in reports]
    
    async def get_all_reports(self) -> List[Dict[str, Any]]:
        """
        Получить все отчеты.
        
        Returns:
            Список словарей с данными отчетов
        """
        reports = await self.report_repository.get_all_reports()
        return [self._serialize_report(report) for report in reports]
