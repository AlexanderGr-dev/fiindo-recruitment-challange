from datetime import date
from typing import Optional
from pydantic import BaseModel


class IncomeStatementSchema(BaseModel):
    symbol: str
    period: str              # Q1, Q2, Q3, Q4, FY
    period_end: date
    calendar_year: int

    revenue: Optional[float]
    net_income: Optional[float]
    eps: Optional[float]

    class Config:
        from_attributes = True

class IncomeStatementCollection:
    def __init__(self, items: list[IncomeStatementSchema]):
        # neu → alt sortieren
        self.items = sorted(
            items,
            key=lambda x: x.period_end,
            reverse=True
        )

    def latest_quarter(self) -> IncomeStatementSchema | None:
        return next(
            (i for i in self.items if i.period.startswith("Q")),
            None
        )

    def previous_quarter(self) -> IncomeStatementSchema | None:
        quarters = [i for i in self.items if i.period.startswith("Q")]
        return quarters[1] if len(quarters) > 1 else None

    def last_n_quarters(self, n: int) -> list[IncomeStatementSchema]:
        return [i for i in self.items if i.period.startswith("Q")][:n]

    def latest_year(self) -> IncomeStatementSchema | None:
        return next(
            (i for i in self.items if i.period == "FY"),
            None
        )



def parse_income_statements(api_response: dict) -> IncomeStatementCollection:
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
