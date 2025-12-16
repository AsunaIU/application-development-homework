from sqlalchemy import Column, Date, Integer, Float
from src.models.base import Base


class OrderReport(Base):
    """Представление для отчетов по заказам"""
    __tablename__ = "order_reports"
    __table_args__ = {'info': {'is_view': True}}
    
    report_at = Column(Date, primary_key=True, nullable=False)
    order_id = Column(Integer, primary_key=True, nullable=False)
    count_product = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    def __repr__(self) -> str:
        return (
            f"OrderReport(report_at={self.report_at}, "
            f"order_id={self.order_id}, count_product={self.count_product}, "
            f"total_amount={self.total_amount})"
        )
