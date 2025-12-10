from datetime import date
from typing import Optional
from pydantic import BaseModel


class EODPriceSchema(BaseModel):
    symbol: str
    date: date

    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]

    class Config:
        from_attributes = True

class EODPriceCollection:
    def __init__(self, items: list[EODPriceSchema]):
        self.items = sorted(
            items,
            key=lambda x: x.date,
            reverse=True
        )

    def latest(self) -> EODPriceSchema | None:
        return self.items[0] if self.items else None

    def latest_close(self) -> float | None:
        latest = self.latest()
        return latest.close if latest else None

def parse_eod_prices(symbol: str, api_response: list[dict]) -> EODPriceCollection:

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
