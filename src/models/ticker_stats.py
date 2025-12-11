"""ORM model representing per-ticker statistics for a single period.

`TickerStats` records computed metrics for a given symbol and reporting
period (period_end). The ETL pipeline populates these records and the
data is later used to produce industry aggregates and reports.
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func

from src.models.base import Base


class TickerStats(Base):
    """SQLAlchemy model for storing computed ticker statistics.

    Attributes:
        id: Primary key.
        symbol: Ticker symbol (e.g., 'AAPL.US').
        industry: Industry name the ticker belongs to.
        period_end: The reporting period end date for these stats.
        pe_ratio: Price-to-earnings ratio for the period (nullable).
        revenue_growth_qoq: Quarter-over-quarter revenue growth (nullable).
        net_income_ttm: Trailing twelve months net income (nullable).
        debt_ratio: Debt-to-equity ratio (nullable).
        created_at: Record creation timestamp.
    """

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
