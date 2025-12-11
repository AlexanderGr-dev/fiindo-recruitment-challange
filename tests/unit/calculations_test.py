"""Unit tests for calculations service.

Tests cover:
- Calculations of key figures (PE ratio, revenue growth, TTM net income, debt ratio)
- Industry-level aggregation of these metrics
"""
import pytest
from src.services.calculations import CalculationService
from typing import Optional



class MockTickerStats:
    """Simulates a minimal TickerStats object used in aggregation tests."""
    def __init__(self, pe_ratio: Optional[float], revenue_growth_qoq: Optional[float], net_income_ttm: Optional[float]):
        self.pe_ratio = pe_ratio
        self.revenue_growth_qoq = revenue_growth_qoq
        self.net_income_ttm = net_income_ttm


@pytest.fixture
def calc_service():
    """Provide a CalculationService instance for tests."""
    return CalculationService()


class TestCalculatePERatio:
    """Unit tests for CalculationService.calculate_pe_ratio.

    Covers standard cases and edge-case handling when EPS is zero or None.
    """
    @pytest.mark.parametrize("price, eps, expected", [
        (20.0, 2.0, 10.0),      
        (50.0, 5.0, 10.0),
        (100.0, 1.0, 100.0),
    ])
    def test_standard_pe_ratio(self, calc_service, price, eps, expected):
        result = calc_service.calculate_pe_ratio(price, eps)
        assert result == expected

    @pytest.mark.parametrize("price, eps", [
        (100.0, 0.0),
        (100.0, None),
    ])
    def test_pe_ratio_edge_cases_none(self, calc_service, price, eps):
        """Returns None when EPS is zero or None (avoid division by zero)."""
        assert calc_service.calculate_pe_ratio(price, eps) is None


class TestCalculateRevenueGrowth:
    """Tests for CalculationService.calculate_revenue_growth.

    Verifies percent growth calculation and edge-case handling.
    """
    @pytest.mark.parametrize("current, previous, expected", [
        (120.0, 100.0, 0.2),    
        (90.0, 100.0, -0.1),    
        (100.0, 100.0, 0.0),    
    ])
    def test_standard_growth(self, calc_service, current, previous, expected):
        result = calc_service.calculate_revenue_growth(current, previous)
        assert result == pytest.approx(expected)

    @pytest.mark.parametrize("current, previous", [
        (100.0, 0.0),
        (100.0, None),
    ])
    def test_growth_edge_cases_none(self, calc_service, current, previous):
        """Returns None when previous revenue is zero or None."""
        assert calc_service.calculate_revenue_growth(current, previous) is None


class TestCalculateNetIncomeTTM:
    """Tests for CalculationService.calculate_net_income_ttm (TTM calculations)."""

    def test_standard_ttm_calculation(self, calc_service):
        quarters = [10.0, 5.0, 8.0, 7.0]
        expected_sum = 30.0
        assert calc_service.calculate_net_income_ttm(quarters) == expected_sum

    def test_ttm_with_negative_quarters(self, calc_service):
        quarters = [10.0, -5.0, 8.0, 7.0]
        expected_sum = 20.0
        assert calc_service.calculate_net_income_ttm(quarters) == expected_sum

    @pytest.mark.parametrize("quarters", [
        [],
        [10.0, 5.0, 8.0],
        [10.0, 5.0, 8.0, 7.0, 2.0],
        None,
    ])
    def test_ttm_invalid_input(self, calc_service, quarters):
        """Returns None for invalid TTM inputs (None or wrong length)."""
        assert calc_service.calculate_net_income_ttm(quarters) is None


class TestCalculateDebtRatio:
    """Tests for CalculationService.calculate_debt_ratio."""

    @pytest.mark.parametrize("debt, equity, expected", [
        (50.0, 100.0, 0.5),     
        (200.0, 100.0, 2.0),    
    ])
    def test_standard_debt_ratio(self, calc_service, debt, equity, expected):
        result = calc_service.calculate_debt_ratio(debt, equity)
        assert result == pytest.approx(expected)

    @pytest.mark.parametrize("debt, equity", [
        (100.0, 0.0),
        (100.0, None),
    ])
    def test_debt_ratio_edge_cases_none(self, calc_service, debt, equity):
        """Return None if total equity is zero or None."""
        assert calc_service.calculate_debt_ratio(debt, equity) is None


class TestAggregateIndustryMetrics:
    """Unit tests for aggregate_industry_metrics.

    Verifies averages (PE, revenue growth) and total TTM computation
    across lists of ticker-like objects.
    """
    def test_standard_aggregation(self, calc_service):
        tickers = [
            MockTickerStats(pe_ratio=10.0, revenue_growth_qoq=0.1, net_income_ttm=100.0),
            MockTickerStats(pe_ratio=20.0, revenue_growth_qoq=0.3, net_income_ttm=200.0),
            MockTickerStats(pe_ratio=30.0, revenue_growth_qoq=0.2, net_income_ttm=300.0),
        ]
        
        expected = {
            "avg_pe_ratio": pytest.approx((10.0 + 20.0 + 30.0) / 3),  
            "avg_revenue_growth": pytest.approx((0.1 + 0.3 + 0.2) / 3), 
            "total_revenue": 600.0, 
        }
        
        result = calc_service.aggregate_industry_metrics(tickers)
        assert result["avg_pe_ratio"] == expected["avg_pe_ratio"]
        assert result["avg_revenue_growth"] == expected["avg_revenue_growth"]
        assert result["total_revenue"] == expected["total_revenue"]

    def test_aggregation_with_none_values(self, calc_service):
        tickers = [
            MockTickerStats(pe_ratio=10.0, revenue_growth_qoq=0.1, net_income_ttm=100.0),
            MockTickerStats(pe_ratio=None, revenue_growth_qoq=0.3, net_income_ttm=200.0),
            MockTickerStats(pe_ratio=30.0, revenue_growth_qoq=None, net_income_ttm=None), # net_income_ttm should be 0
        ]
        
        # PE-Ratio: (10 + 30) / 2 = 20.0
        # Revenue Growth: (0.1 + 0.3) / 2 = 0.2
        # Total Revenue (TTM): 100 + 200 + 0 = 300.0
        expected = {
            "avg_pe_ratio": 20.0,
            "avg_revenue_growth": 0.2,
            "total_revenue": 300.0, 
        }
        
        result = calc_service.aggregate_industry_metrics(tickers)
        assert result["avg_pe_ratio"] == pytest.approx(expected["avg_pe_ratio"])
        assert result["avg_revenue_growth"] == pytest.approx(expected["avg_revenue_growth"])
        assert result["total_revenue"] == expected["total_revenue"]


    def test_aggregation_empty_list(self, calc_service):
        expected = {
            "avg_pe_ratio": None,
            "avg_revenue_growth": None,
            "total_revenue": None,
        }
        
        result = calc_service.aggregate_industry_metrics([])
        assert result == expected

    def test_aggregation_all_none_values(self, calc_service):
        tickers = [
            MockTickerStats(pe_ratio=None, revenue_growth_qoq=None, net_income_ttm=None),
            MockTickerStats(pe_ratio=None, revenue_growth_qoq=None, net_income_ttm=None),
        ]
        
        expected = {
            "avg_pe_ratio": None,
            "avg_revenue_growth": None,
            "total_revenue": 0.0, 
        }
        
        result = calc_service.aggregate_industry_metrics(tickers)
        assert result == expected