import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

from src.core.config import settings
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
    Orchestrates the ETL (Extract, Transform, Load) pipeline using concurrent execution.
    
    Handles high API latency by using ThreadPoolExecutor with multiple workers.
    
    Workflow:
    1. Fetch all available stock symbols from the API
    2. Process each symbol in parallel:
       - Fetch general info, income statements, balance sheets, and EOD prices
       - Extract and validate industry classification
       - Calculate key financial metrics (PE ratio, revenue growth, TTM, debt ratio)
       - Create TickerStats record
    3. Persist ticker stats to database
    4. Aggregate metrics by industry and persist aggregations
    """

    # Conservative worker count to match API rate limit (5 RPS).
    MAX_WORKERS = settings.ETL_MAX_WORKERS

    ALLOWED_INDUSTRIES = [
        "Banks - Diversified",
        "Software - Application",
        "Consumer Electronics",
    ]

    def __init__(self, db: Session, client: FiindoClient):
        """Initialize ETL service with database session and API client.
        
        Args:
            db: SQLAlchemy Session for database operations.
            client: FiindoClient instance with rate limiting configured.
        """
        self.db = db
        self.client = client
        self.calc = CalculationService()
        self.ticker_repo = TickerRepository(db)
        self.industry_repo = IndustryRepository(db)

    def _process_single_symbol(self, symbol: str) -> TickerStats | None:
        """Process a single stock symbol through the complete ETL pipeline.
        
        Fetches financial data from the API, validates industry classification,
        normalizes data via Pydantic schemas, calculates metrics, and creates
        a TickerStats record.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL').
        
        Returns:
            TickerStats object if processing succeeds and symbol passes industry filter.
            None if processing fails or symbol is filtered out.
        
        Handles:
        - FiindoClientError: Logs warning and returns None
        - Other exceptions: Logs error with traceback and returns None
        """
        try:
            # 1. Fetch general info and filter by allowed industry
            general = self.client.get_general(symbol)
            industry = self._extract_industry(general)

            if industry not in self.ALLOWED_INDUSTRIES:
                return None

            # 2. Fetch raw financial data (API client enforces rate limiting)
            income_raw = self.client.get_financials(symbol, "income_statement")
            balance_raw = self.client.get_financials(symbol, "balance_sheet_statement")
            eod_raw = self.client.get_eod(symbol)

            # 3. Normalize data via Pydantic schemas
            income_q = parse_income_statements(income_raw)
            balance_fy = parse_balance_sheets(balance_raw)
            eod_prices = parse_eod_prices(symbol, eod_raw)

            # 4. Extract latest data points for calculations
            last_q = income_q.latest_quarter()
            prev_q = income_q.previous_quarter()
            last_4_q = income_q.last_n_quarters(4)
            last_year_balance = balance_fy.latest_year()
            latest_price = eod_prices.latest_close()

            # 5. Calculate financial metrics
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

            # 6. Create and return TickerStats model
            ticker_stats = TickerStats(
                symbol=symbol,
                industry=industry,
                period_end=last_q.period_end,
                pe_ratio=pe_ratio,
                revenue_growth_qoq=revenue_growth,
                net_income_ttm=net_income_ttm,
                debt_ratio=debt_ratio,
            )
            
            return ticker_stats

        except FiindoClientError as e:
            logger.warning("API error for %s: %s", symbol, e)
        except Exception:
            logger.exception("Failed processing symbol %s", symbol)

        return None

    def run(self) -> dict:
        """Execute the complete ETL pipeline.
        
        Steps:
        1. Fetch all available stock symbols from API
        2. Process each symbol concurrently using ThreadPoolExecutor
        3. Persist processed ticker stats to database
        4. Aggregate metrics by industry and persist aggregations
        
        Returns:
            Summary dict with:
            - tickers_processed: Number of tickers successfully processed
            - industries_processed: Number of industries with aggregated metrics
        """
        summary = {"tickers_processed": 0, "industries_processed": 0}
        tickers_for_processing: List[TickerStats] = []
        
        # 1. Fetch all available symbols
        symbols = self.client.get_symbols()
        logger.info("Fetched %d symbols total", len(symbols))

        # 2. Process symbols concurrently with thread pool
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            # Submit all symbols for processing
            future_to_symbol = {
                executor.submit(self._process_single_symbol, sym): sym 
                for sym in symbols
            }
            
            # Collect results as they complete (non-blocking)
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                result = future.result()
                
                if result:
                    # Symbol was processed successfully and passed industry filter
                    tickers_for_processing.append(result)
                    summary["tickers_processed"] += 1

        logger.info("Processed %d symbols successfully", len(symbols))
        logger.info("Found %d ticker stats to persist", summary["tickers_processed"])

        # 3. Persist tickers to database
        self.ticker_repo.bulk_save(tickers_for_processing)

        # 4. Aggregate metrics by industry and persist
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
    def _extract_industry(general: Dict[str, Any]) -> str | None:
        """Extract industry classification from API general info response."""
        try:
            return (
                general["fundamentals"]["profile"]["data"][0]["industry"]
            )
        except (KeyError, IndexError, TypeError):
            return None
