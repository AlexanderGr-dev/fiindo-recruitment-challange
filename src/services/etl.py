
import logging
from src.schemas.balance_sheet import parse_balance_sheets
from src.schemas.eod import parse_eod_prices
from src.schemas.income_statement import parse_income_statements
from src.clients.fiindo_client import FiindoClient, FiindoClientError
from src.services.calculations import CalculationService
from src.models.ticker_stats import TickerStats
from src.models.industry_agg import IndustryAggregation
from src.repositories.ticker_repo import TickerRepository
from src.repositories.industry_repo import IndustryRepository
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class ETLService:
    """
    Orchestrates the ETL pipeline:
    - Fetch symbols from API
    - Filter by industry
    - Fetch financials
    - Calculate metrics
    - Persist ticker and industry aggregates
    """

    ALLOWED_INDUSTRIES = [
        "Banks - Diversified",
        "Software - Application",
        "Consumer Electronics",
    ]

    def __init__(self, db: Session, client: FiindoClient):
        self.db = db
        self.client = client
        self.calc = CalculationService()
        self.ticker_repo = TickerRepository(db)
        self.industry_repo = IndustryRepository(db)

    def run(self) -> dict:
        summary = {"tickers_processed": 0, "industries_processed": 0}
        tickers_for_processing: list[TickerStats] = []

        symbols = self.client.get_symbols()
        logger.info("Fetched %d symbols", len(symbols))

        symbols = symbols[159:240]

        for symbol in symbols:
            try:
                # Get industry
                general = self.client.get_general(symbol)
                industry = self._extract_industry(general)

                if industry not in self.ALLOWED_INDUSTRIES:
                    continue

                # Fetch raw data
                income_raw = self.client.get_financials(symbol, "income_statement")
                balance_raw = self.client.get_financials(symbol, "balance_sheet_statement")
                eod_raw = self.client.get_eod(symbol)

                # Normalize via schemas
                income_q = parse_income_statements(income_raw)
                balance_fy = parse_balance_sheets(balance_raw)
                eod_prices = parse_eod_prices(symbol, eod_raw)

                # Select latest data points
                last_q = income_q.latest_quarter()
                prev_q = income_q.previous_quarter()
                last_4_q = income_q.last_n_quarters(4)
                last_year_balance = balance_fy.latest_year()
                latest_price = eod_prices.latest_close()

                # Calculate key figures
                pe_ratio = self.calc.calculate_pe_ratio(
                    price=latest_price,
                    eps=last_q.eps,
                )

                revenue_growth = self.calc.calculate_revenue_growth(
                    current_revenue=last_q.revenue,
                    previous_revenue=prev_q.revenue,
                )

                net_income_ttm = self.calc.calculate_net_income_ttm(
                    [q.net_income for q in last_4_q]
                )

                debt_ratio = self.calc.calculate_debt_ratio(
                    total_debt=last_year_balance.total_debt,
                    total_equity=last_year_balance.total_equity,
                )

                ticker_stats = TickerStats(
                    symbol=symbol,
                    industry=industry,
                    period_end=last_q.period_end,
                    pe_ratio=pe_ratio,
                    revenue_growth_qoq=revenue_growth,
                    net_income_ttm=net_income_ttm,
                    debt_ratio=debt_ratio,
                )

                tickers_for_processing.append(ticker_stats)
                summary["tickers_processed"] += 1

            except FiindoClientError as e:
                logger.warning("API error for %s: %s", symbol, e)
            except Exception:
                logger.exception("Failed processing symbol %s", symbol)

        # Persist tickers in db
        self.ticker_repo.bulk_save(tickers_for_processing)

        # Aggregate key figures per industry and persist in db
        for industry in self.ALLOWED_INDUSTRIES:
            industry_tickers = [t for t in tickers_for_processing if t.industry == industry]
            if not industry_tickers:
                continue

            metrics = self.calc.aggregate_industry_metrics(industry_tickers)

            self.industry_repo.save(
                IndustryAggregation(
                    industry=industry,
                    avg_pe_ratio=metrics['avg_pe_ratio'],
                    avg_revenue_growth=metrics['avg_revenue_growth'],
                    total_revenue=metrics['total_revenue'],
                )
            )

            summary["industries_processed"] += 1

        logger.info(
            "ETL finished: %d tickers, %d industries",
            summary["tickers_processed"],
            summary["industries_processed"],
        )

        return summary

    @staticmethod
    def _extract_industry(general: dict) -> str | None:
        try:
            return (
                general["fundamentals"]["profile"]["data"][0]["industry"]
            )
        except (KeyError, IndexError, TypeError):
            return None
