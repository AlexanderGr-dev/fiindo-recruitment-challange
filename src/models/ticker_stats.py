from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func

from src.models.base import Base


class TickerStats(Base):
    __tablename__ = "ticker_stats"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String, nullable=False, index=True)
    industry = Column(String, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    pe_ratio = Column(Float, nullable=True)
    revenue_growth_qoq = Column(Float, nullable=True)
    net_income_ttm = Column(Float, nullable=True)
    debt_ratio = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
