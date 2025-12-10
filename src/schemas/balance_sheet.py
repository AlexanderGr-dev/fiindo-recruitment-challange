from datetime import date
from typing import Optional
from pydantic import BaseModel


class BalanceSheetSchema(BaseModel):
    symbol: str
    period: str          # FY
    period_end: date
    calendar_year: int

    total_debt: Optional[float]
    total_equity: Optional[float]

    class Config:
        from_attributes = True

class BalanceSheetCollection:
    def __init__(self, items: list[BalanceSheetSchema]):
        self.items = sorted(
            items,
            key=lambda x: x.period_end,
            reverse=True
        )

    def latest_year(self) -> BalanceSheetSchema | None:
        return next(
            (i for i in self.items if i.period == "FY"),
            None
        )

    def latest_quarter(self) -> BalanceSheetSchema | None:
        return next(
            (i for i in self.items if i.period.startswith("Q")),
            None
        )

def parse_balance_sheets(api_response: dict) -> BalanceSheetCollection:
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
