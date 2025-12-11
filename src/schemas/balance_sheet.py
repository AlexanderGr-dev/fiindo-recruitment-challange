"""Parse and normalize balance sheet financial data from Fiindo API.

Balance sheet data typically includes:
- Assets, liabilities, and equity (snapshot at fiscal period end)
- Available in both annual (FY) and quarterly (Q) granularity
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class BalanceSheetSchema(BaseModel):
    """Normalized balance sheet record for a single fiscal period.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL').
        period: Fiscal period ('FY' for annual, 'Q1'-'Q4' for quarters).
        period_end: End date of the fiscal period.
        calendar_year: Calendar year of the period.
        total_debt: Total debt obligations (in currency units).
        total_equity: Total shareholder equity (in currency units).
    """
    symbol: str
    period: str          # FY
    period_end: date
    calendar_year: int

    total_debt: Optional[float]
    total_equity: Optional[float]


class BalanceSheetCollection:
    """Collection of balance sheet records sorted by date (newest first).
    
    Provides convenience methods to retrieve latest annual or quarterly data.
    """
    
    def __init__(self, items: list[BalanceSheetSchema]):
        """Initialize with list of balance sheet items; sort newest first."""
        # Sort by period_end descending (newest first)
        self.items = sorted(
            items,
            key=lambda x: x.period_end,
            reverse=True
        )

    def latest_year(self) -> BalanceSheetSchema | None:
        """Get the most recent annual (FY) balance sheet.
        
        Returns:
            Latest annual balance sheet, or None if not available.
        """
        return next(
            (i for i in self.items if i.period == "FY"),
            None
        )

    def latest_quarter(self) -> BalanceSheetSchema | None:
        """Get the most recent quarterly (Q1-Q4) balance sheet.
        
        Returns:
            Latest quarterly balance sheet, or None if not available.
        """
        return next(
            (i for i in self.items if i.period.startswith("Q")),
            None
        )

def parse_balance_sheets(api_response: dict) -> BalanceSheetCollection:
    """Parse raw Fiindo API response into a normalized BalanceSheetCollection.
    
    Extracts balance sheet data from nested API response structure and creates
    BalanceSheetSchema objects with validated fields.
    
    Args:
        api_response: Raw dict response from Fiindo API.
    
    Returns:
        BalanceSheetCollection with parsed and sorted items.
    """
    data = (
        api_response
        .get("fundamentals", {})
        .get("financials", {})
        .get("balance_sheet_statement", {})
        .get("data", [])
    )

    items = [
        BalanceSheetSchema(
            symbol=item["symbol"],
            period=item["period"],
            period_end=item["date"],
            calendar_year=int(item["calendarYear"]),
            total_assets=item.get("totalAssets"),
            total_liabilities=item.get("totalLiabilities"),
            total_equity=item.get("totalEquity"),
            total_debt=item.get("totalDebt"),
        )
        for item in data
    ]

    return BalanceSheetCollection(items)
