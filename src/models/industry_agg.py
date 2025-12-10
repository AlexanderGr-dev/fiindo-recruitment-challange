from sqlalchemy import Column, Integer, String, Float, DateTime, func

from src.models.base import Base


class IndustryAggregation(Base):
    __tablename__ = "industry_aggregations"

    id = Column(Integer, primary_key=True, index=True)

    industry = Column(String, nullable=False, unique=True)

    avg_pe_ratio = Column(Float, nullable=True)
    avg_revenue_growth = Column(Float, nullable=True)
    total_revenue = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
