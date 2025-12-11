"""Repository for storing and querying `TickerStats` records.

This repository provides helpers used by the ETL service to persist
per-ticker computed metrics and to fetch them for downstream processing.
"""

from typing import List
from sqlalchemy.orm import Session
from src.models.ticker_stats import TickerStats
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class TickerRepository(BaseRepository):
    """Repository providing CRUD helpers for `TickerStats`.

    Methods:
        save(ticker): Persist a single `TickerStats` row.
        bulk_save(tickers): Efficiently insert many `TickerStats` rows.
        get_all(): Return all `TickerStats` rows.
        get_by_symbol(symbol): Return the latest stats for `symbol`.
    """

    def save(self, ticker: TickerStats):
        """Persist a single `TickerStats` instance and commit."""
        self.db.add(ticker)
        self.db.commit()
        logger.debug("Saved ticker: %s", ticker.symbol)

    def bulk_save(self, tickers: List[TickerStats]):
        """Bulk insert a list of `TickerStats` objects.

        If `tickers` is empty the method returns immediately. Uses
        SQLAlchemy's `bulk_save_objects` to reduce insert overhead for
        large batches.
        """
        if not tickers:
            return
        self.db.bulk_save_objects(tickers)
        self.db.commit()
        logger.info("Bulk saved %d tickers", len(tickers))

    def get_all(self) -> List[TickerStats]:
        """Return all `TickerStats` rows from the database."""
        return self.db.query(TickerStats).all()

    def get_by_symbol(self, symbol: str) -> TickerStats:
        """Return the `TickerStats` row for `symbol`, or `None` if missing."""
        return self.db.query(TickerStats).filter(TickerStats.symbol == symbol).first()
