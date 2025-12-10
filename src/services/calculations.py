from typing import Optional, List, Dict

from src.models.ticker_stats import TickerStats


class CalculationService:
    """
    Pure business logic for Fiindo Challenge:
    - PE Ratio
    - Revenue Growth QoQ
    - NetIncome TTM
    - Debt Ratio
    """

    @staticmethod
    def calculate_pe_ratio(price: float, eps: float) -> Optional[float]:
        """
        Price-to-Earnings ratio.
        """
        if eps == 0 or eps is None:
            return None
        return price / eps

    @staticmethod
    def calculate_revenue_growth(current_revenue: float, previous_revenue: float) -> Optional[float]:
        """
        Quarter-over-quarter revenue growth.
        """
        if previous_revenue in (0, None):
            return None
        return (current_revenue - previous_revenue) / previous_revenue

    @staticmethod
    def calculate_net_income_ttm(last_4_quarters: List[float]) -> Optional[float]:
        """
        Trailing twelve months net income.
        """
        if not last_4_quarters or len(last_4_quarters) != 4:
            return None
        return sum(last_4_quarters)

    @staticmethod
    def calculate_debt_ratio(total_debt: float, total_equity: float) -> Optional[float]:
        """
        Debt-to-equity ratio.
        """
        if total_equity in (0, None):
            return None
        return total_debt / total_equity

    @staticmethod
    def aggregate_industry_metrics(tickers: List[TickerStats]) -> Dict:
        """
        Calculate industry-level aggregates.
        Expected tickers: List of dicts with keys:
        - pe_ratio
        - revenue_growth_qoq
        - net_income
        """
        n = len(tickers)
        if n == 0:
            return {
                "avg_pe_ratio": None,
                "avg_revenue_growth": None,
                "total_revenue": None,
            }

        pe_values = [t.pe_ratio for t in tickers if t.pe_ratio is not None]
        rev_values = [t.revenue_growth_qoq for t in tickers if t.revenue_growth_qoq is not None]
        revenue_sum = sum(t.net_income_ttm or 0 for t in tickers)

        avg_pe = sum(pe_values)/len(pe_values) if pe_values else None
        avg_rev = sum(rev_values)/len(rev_values) if rev_values else None

        return {
            "avg_pe_ratio": avg_pe,
            "avg_revenue_growth": avg_rev,
            "total_revenue": revenue_sum,
        }
