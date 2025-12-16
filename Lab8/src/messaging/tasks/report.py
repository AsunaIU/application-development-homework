import logging
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.messaging.taskiq_broker import taskiq_broker
from src.repositories.report_repository import ReportRepository
from src.services.report_service import ReportService

logger = logging.getLogger(__name__)


async def get_report_data(session: AsyncSession, report_date: date) -> dict:
    """Получение данных отчета за указанную дату."""
    try:
        report_repository = ReportRepository(session)
        report_service = ReportService(report_repository)
        
        reports = await report_service.get_report_by_date(report_date)
        
        total_orders = len(reports)
        total_products = sum(report["count_product"] for report in reports)
        total_value = sum(report["total_amount"] for report in reports)
        
        avg_products = total_products / total_orders if total_orders > 0 else 0
        avg_order_value = total_value / total_orders if total_orders > 0 else 0
        
        return {
            "status": "success",
            "date": report_date.isoformat(),
            "total_orders": total_orders,
            "total_products": total_products,
            "total_value": round(total_value, 2),
            "average_products_per_order": round(avg_products, 2),
            "average_order_value": round(avg_order_value, 2),
            "reports": reports
        }
    except Exception as e:
        logger.error(f"Error getting report data: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "date": report_date.isoformat()
        }


@taskiq_broker.task(
    schedule=[
        {
            "cron": "0 0 * * *",  # Каждый день в полночь
            "schedule_id": "generate_daily_report",
        }
    ]
)
async def generate_daily_report():
    """
    Формирует отчет по заказам за предыдущий день.
    Выполняется автоматически каждый день в полночь.
    """
    from src.main import async_session_maker
    
    # Отчет за вчерашний день
    report_date = (datetime.now() - timedelta(days=1)).date()
    
    logger.info(f"Starting daily report generation for {report_date}")
    
    try:
        async with async_session_maker() as session:
            result = await get_report_data(session, report_date)
            
            if result["status"] == "success":
                logger.info(
                    f"Daily report for {report_date}: "
                    f"Orders: {result['total_orders']}, "
                    f"Products: {result['total_products']}, "
                    f"Total Value: ${result['total_value']}, "
                    f"Avg Order Value: ${result['average_order_value']}"
                )
            else:
                logger.error(f"Failed to generate report: {result.get('error')}")
            
            return result
            
    except Exception as e:
        logger.error(f"Error in generate_daily_report: {e}", exc_info=True)
        return {
            "status": "error",
            "date": report_date.isoformat(),
            "error": str(e)
        }


# @taskiq_broker.task(
#     schedule=[
#         {
#             "cron": "*/1 * * * *",  # Каждую минуту для тестирования
#             "schedule_id": "generate_test_report",
#         }
#     ]
# )
# async def generate_test_report():
#     """Тестовая задача для проверки scheduler (каждую минуту)."""
#     from src.main import async_session_maker
    
#     report_date = date.today()
#     logger.info(f"[TEST] Generating report for {report_date}")
    
#     try:
#         async with async_session_maker() as session:
#             result = await get_report_data(session, report_date)
            
#             if result["status"] == "success":
#                 logger.info(
#                     f"[TEST] Report for {report_date}: "
#                     f"{result['total_orders']} orders, "
#                     f"{result['total_products']} products, "
#                     f"${result['total_value']} total value"
#                 )
#             return result
            
#     except Exception as e:
#         logger.error(f"[TEST] Error: {e}", exc_info=True)
#         return {
#             "status": "error",
#             "date": report_date.isoformat(),
#             "error": str(e)
#         }