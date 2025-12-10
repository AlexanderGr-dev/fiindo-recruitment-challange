from typing import List
from sqlalchemy.orm import Session
from src.models.ticker_stats import TickerStats
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class TickerRepository(BaseRepository):
    def save(self, ticker: TickerStats):
        self.db.add(ticker)
        self.db.commit()
        logger.debug("Saved ticker: %s", ticker.symbol)

    def bulk_save(self, tickers: List[TickerStats]):
        if not tickers:
            return
        self.db.bulk_save_objects(tickers)
        self.db.commit()
        logger.info("Bulk saved %d tickers", len(tickers))

    def get_all(self) -> List[TickerStats]:
        return self.db.query(TickerStats).all()

    def get_by_symbol(self, symbol: str) -> TickerStats:
        return self.db.query(TickerStats).filter(TickerStats.symbol == symbol).first()
