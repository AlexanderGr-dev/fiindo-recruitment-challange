from sqlalchemy.orm import Session
from src.models.industry_agg import IndustryAggregation
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class IndustryRepository(BaseRepository):
    def save(self, industry: IndustryAggregation):
        # Optional: prüfen ob Industry schon existiert → Update
        existing = self.db.query(IndustryAggregation)\
                          .filter(IndustryAggregation.industry == industry.industry)\
                          .first()
        if existing:
            existing.avg_pe_ratio = industry.avg_pe_ratio
            existing.avg_revenue_growth = industry.avg_revenue_growth
            existing.total_revenue = industry.total_revenue
            self.db.commit()
            logger.info("Updated industry aggregation: %s", industry.industry)
        else:
            self.db.add(industry)
            self.db.commit()
            logger.info("Saved new industry aggregation: %s", industry.industry)

    def get_all(self):
        return self.db.query(IndustryAggregation).all()

    def get_by_industry(self, industry: str):
        return self.db.query(IndustryAggregation)\
                      .filter(IndustryAggregation.industry == industry)\
                      .first()
