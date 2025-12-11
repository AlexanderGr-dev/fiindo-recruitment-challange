"""Parse and normalize end-of-day (EOD) stock price data from Fiindo API.

EOD price data includes:
- Open, high, low, close prices and trading volume
- Daily granularity (one record per trading day)
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class EODPriceSchema(BaseModel):
    """Normalized EOD price record for a single trading day.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL').
        date: Trading date.
        open: Opening price (in currency units).
        high: Highest price of the day (in currency units).
        low: Lowest price of the day (in currency units).
        close: Closing price (in currency units).
        volume: Trading volume (number of shares traded).
    """
    symbol: str
    date: date

    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]


class EODPriceCollection:
    """Collection of EOD price records sorted by date (newest first).
    
    Provides convenience methods to retrieve latest price and closing price.
    """
    
    def __init__(self, items: list[EODPriceSchema]):
        """Initialize with list of EOD price items; sort newest first."""
        # Sort by date descending (newest first)
        self.items = sorted(
            items,
            key=lambda x: x.date,
            reverse=True
        )

    def latest(self) -> EODPriceSchema | None:
        """Get the most recent EOD price record.
        
        Returns:
            Latest EOD price, or None if no prices available.
        """
        return self.items[0] if self.items else None

    def latest_close(self) -> float | None:
        """Get the closing price from the most recent trading day.
        
        Returns:
            Latest closing price, or None if no prices available.
        """
        latest = self.latest()
        return latest.close if latest else None

def parse_eod_prices(symbol: str, api_response: list[dict]) -> EODPriceCollection:
    """Parse raw Fiindo API response into a normalized EODPriceCollection.
    
    Extracts end-of-day price data from nested API response structure and creates
    EODPriceSchema objects with validated fields.
    
    Args:
        symbol: Stock ticker symbol (used to populate schema symbol field).
        api_response: Raw dict response from Fiindo API.
    
    Returns:
        EODPriceCollection with parsed and sorted items.
    """

    data = (
        api_response
        .get("stockprice", {})
        .get("data", {})
    )
       
    items = [
        EODPriceSchema(
            symbol=symbol,
            date=item["date"],
            open=item.get("open"),
            high=item.get("high"),
            low=item.get("low"),
            close=item.get("close"),
            volume=item.get("volume"),
        )
        for item in data
    ]

    return EODPriceCollection(items)
