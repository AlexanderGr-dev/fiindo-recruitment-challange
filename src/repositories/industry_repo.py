"""Repository for managing `IndustryAggregation` records.

This module provides simple persistence operations used by the ETL
pipeline to save and query industry-level aggregations.
"""

from sqlalchemy.orm import Session
from src.models.industry_agg import IndustryAggregation
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class IndustryRepository(BaseRepository):
    """Repository for industry aggregation persistence.

    Methods:
        save(industry): Persist an `IndustryAggregation` instance.
        get_all(): Return all saved industry aggregations.
        get_by_industry(industry): Get aggregation for a specific industry.
    """

    def save(self, industry: IndustryAggregation):
        """Persist the provided `IndustryAggregation` instance."""
        # Optional: check whether Industry already exists → Update 
        self.db.add(industry)
        self.db.commit()
        logger.info("Saved industry aggregation: %s", industry.industry)

    def get_all(self):
        """Return all `IndustryAggregation` rows."""
        return self.db.query(IndustryAggregation).all()

    def get_by_industry(self, industry: str):
        """Return the aggregation for the given industry, or `None`.

        Args:
            industry: Industry name to look up.
        """
        return (
            self.db.query(IndustryAggregation)
            .filter(IndustryAggregation.industry == industry)
            .first()
        )
