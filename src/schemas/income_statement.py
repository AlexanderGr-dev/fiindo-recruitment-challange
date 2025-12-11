"""Parse and normalize income statement financial data from Fiindo API.

Income statement data typically includes:
- Revenue, net income, earnings per share (EPS)
- Available in both annual (FY) and quarterly (Q) granularity
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class IncomeStatementSchema(BaseModel):
    """Normalized income statement record for a single fiscal period.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., 'AAPL').
        period: Fiscal period ('FY' for annual, 'Q1'-'Q4' for quarters).
        period_end: End date of the fiscal period.
        calendar_year: Calendar year of the period.
        revenue: Total revenue for the period (in currency units).
        net_income: Net income / profit (in currency units).
        eps: Earnings per share (in currency units per share).
    """
    symbol: str
    period: str              # Q1, Q2, Q3, Q4, FY
    period_end: date
    calendar_year: int

    revenue: Optional[float]
    net_income: Optional[float]
    eps: Optional[float]


class IncomeStatementCollection:
    """Collection of income statement records sorted by date (newest first).
    
    Provides convenience methods to retrieve latest quarterly/annual data
    and rolling periods (e.g., trailing 12 months).
    """
    
    def __init__(self, items: list[IncomeStatementSchema]):
        """Initialize with list of income statement items; sort newest first."""
        # Sort by period_end descending (newest first)
        self.items = sorted(
            items,
            key=lambda x: x.period_end,
            reverse=True
        )

    def latest_quarter(self) -> IncomeStatementSchema | None:
        """Get the most recent quarterly (Q1-Q4) income statement.
        
        Returns:
            Latest quarterly statement, or None if not available.
        """
        return next(
            (i for i in self.items if i.period.startswith("Q")),
            None
        )

    def previous_quarter(self) -> IncomeStatementSchema | None:
        """Get the second-most recent quarterly income statement.
        
        Used for calculating quarter-over-quarter (QoQ) growth.
        
        Returns:
            Previous quarter statement, or None if fewer than 2 quarters available.
        """
        quarters = [i for i in self.items if i.period.startswith("Q")]
        return quarters[1] if len(quarters) > 1 else None

    def last_n_quarters(self, n: int) -> list[IncomeStatementSchema]:
        """Get the most recent n quarterly income statements.
        
        Useful for calculating trailing 12-month (TTM) metrics.
        
        Args:
            n: Number of quarters to return.
        
        Returns:
            List of up to n most recent quarterly statements (newest first).
        """
        return [i for i in self.items if i.period.startswith("Q")][:n]

    def latest_year(self) -> IncomeStatementSchema | None:
        """Get the most recent annual (FY) income statement.
        
        Returns:
            Latest annual statement, or None if not available.
        """
        return next(
            (i for i in self.items if i.period == "FY"),
            None
        )



def parse_income_statements(api_response: dict) -> IncomeStatementCollection:
    """Parse raw Fiindo API response into a normalized IncomeStatementCollection.
    
    Extracts income statement data from nested API response structure and creates
    IncomeStatementSchema objects with validated fields.
    
    Args:
        api_response: Raw dict response from Fiindo API.
    
    Returns:
        IncomeStatementCollection with parsed and sorted items.
    """
    data = (
        api_response
        .get("fundamentals", {})
        .get("financials", {})
        .get("income_statement", {})
        .get("data", [])
    )

    items = [
        IncomeStatementSchema(
            symbol=item["symbol"],
            period=item["period"],
            period_end=item["date"],
            calendar_year=int(item["calendarYear"]),
            revenue=item.get("revenue"),
            net_income=item.get("netIncome"),
            eps=item.get("eps"),
        )
        for item in data
    ]

    return IncomeStatementCollection(items)
