"""ORM model for industry-level aggregate metrics.

The `IndustryAggregation` table stores precomputed aggregates for an
industry (for example, average PE, average revenue growth, and total
revenue) which are produced by the ETL pipeline and persisted for later
analysis and reporting.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, func

from src.models.base import Base


class IndustryAggregation(Base):
    """SQLAlchemy model for storing industry aggregates.

    Attributes:
        id: Primary key.
        industry: Industry name used as a lookup key.
        avg_pe_ratio: Average price-to-earnings ratio for the industry.
        avg_revenue_growth: Average QoQ revenue growth for the industry.
        total_revenue: Sum of revenues (or net income TTM) for the industry.
        created_at: Timestamp when the aggregation was created.
    """

    __tablename__ = "industry_aggregations"

    id = Column(Integer, primary_key=True, index=True)

    industry = Column(String, nullable=False)

    avg_pe_ratio = Column(Float, nullable=True)
    avg_revenue_growth = Column(Float, nullable=True)
    total_revenue = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
