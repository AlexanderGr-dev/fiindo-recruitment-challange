"""Unit tests for the ETL service.

This module contains unit-level tests for `ETLService`. It provides fixtures
that mock the API client, parsing helpers, calculation service and
repositories. Tests focus on the internal processing logic (single-symbol
processing) and helper functions (payload extraction). End-to-end orchestration
tests are intentionally excluded from the unit test suite.

Structure:
- Fixtures and mock setup
- Helpers for single-symbol processing
- Unit test cases (processing, extraction)
"""

import pytest
from unittest.mock import call
from datetime import date

from src.services.etl import ETLService
from src.models.ticker_stats import TickerStats
from src.models.industry_agg import IndustryAggregation
from src.clients.fiindo_client import FiindoClientError  # for error cases


# 1. FIXTURES & SETUP

class MockSchemaItem:
    """Base class used to represent parsed quarterly or yearly data in tests."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def setup_mocks(mocker):
    """Create all necessary MagicMock objects and simulate their behavior.

    Returns: (mock_client, mock_ticker_repo, mock_industry_repo, mock_calc)
    """
    # 1. Mock API client
    mock_client = mocker.MagicMock()
    mock_client.get_symbols.return_value = ["AAPL", "MSFT", "GOOGL", "NO_INDUSTRY", "ERROR"]

    # 2. Mock repositories (DB)
    mock_ticker_repo = mocker.MagicMock()
    mock_industry_repo = mocker.MagicMock()

    # 3. Mock calculation service
    mock_calc = mocker.MagicMock()

    return mock_client, mock_ticker_repo, mock_industry_repo, mock_calc


@pytest.fixture
def etl_service_setup(mocker):
    """Fixture to set up an ETLService instance with mocked dependencies."""
    mock_db = mocker.MagicMock()
    mock_client, mock_ticker_repo, mock_industry_repo, mock_calc = setup_mocks(mocker)

    # Initialize the ETLService with the mock objects
    service = ETLService(db=mock_db, client=mock_client)

    # Replace calculation and repository attributes on the service with mocks
    service.calc = mock_calc
    service.ticker_repo = mock_ticker_repo
    service.industry_repo = mock_industry_repo

    return service, mock_client, mock_calc, mock_ticker_repo, mock_industry_repo



# 2. HELPERS FOR SINGLE-SYMBOL PROCESSING (_process_single_symbol)

@pytest.fixture
def successful_processing_mocks(mocker):
    """Provide mocks for parsing helpers and API calls representing a successful symbol processing run.

    Returns a tuple of (mock_client, mock_calc, expected_ticker_stats).
    """
    # API responses (raw data)
    MOCK_RAW_DATA = {"data": "raw"}

    # Data used for calculations
    MOCK_LATEST_Q = MockSchemaItem(period_end=date(2025, 3, 31), revenue=120.0, eps=2.0, net_income=10.0)
    MOCK_PREV_Q = MockSchemaItem(revenue=100.0)
    MOCK_LAST_4_Q = [MOCK_LATEST_Q, MockSchemaItem(net_income=9.0), MockSchemaItem(net_income=8.0), MockSchemaItem(net_income=7.0)]
    MOCK_BALANCE = MockSchemaItem(total_debt=50.0, total_equity=100.0)
    MOCK_PRICE = 40.0
    
    # Patch parsing helpers to return the prepared mock objects
    mocker.patch('src.services.etl.parse_income_statements').return_value.latest_quarter.return_value = MOCK_LATEST_Q
    mocker.patch('src.services.etl.parse_income_statements').return_value.previous_quarter.return_value = MOCK_PREV_Q
    mocker.patch('src.services.etl.parse_income_statements').return_value.last_n_quarters.return_value = MOCK_LAST_4_Q
    mocker.patch('src.services.etl.parse_balance_sheets').return_value.latest_year.return_value = MOCK_BALANCE
    mocker.patch('src.services.etl.parse_eod_prices').return_value.latest_close.return_value = MOCK_PRICE
    
    # Mock calculation functions (the results produced by calculations)
    MOCK_PE = 20.0
    MOCK_GROWTH = 0.2
    MOCK_TTM = 34.0
    MOCK_DEBT_RATIO = 0.5
    
    mock_calc = mocker.MagicMock()
    mock_calc.calculate_pe_ratio.return_value = MOCK_PE
    mock_calc.calculate_revenue_growth.return_value = MOCK_GROWTH
    mock_calc.calculate_net_income_ttm.return_value = MOCK_TTM
    mock_calc.calculate_debt_ratio.return_value = MOCK_DEBT_RATIO
    
    # Simulate API return values
    mock_client = mocker.MagicMock()
    mock_client.get_general.return_value = {"fundamentals": {"profile": {"data": [{"industry": "Software - Application"}]}}}
    mock_client.get_financials.return_value = MOCK_RAW_DATA
    mock_client.get_eod.return_value = MOCK_RAW_DATA
    
    # Expected TickerStats (with the mocked calculation results)
    expected_ticker_stats = TickerStats(
        symbol="AAPL",
        industry="Software - Application",
        period_end=MOCK_LATEST_Q.period_end,
        pe_ratio=MOCK_PE,
        revenue_growth_qoq=MOCK_GROWTH,
        net_income_ttm=MOCK_TTM,
        debt_ratio=MOCK_DEBT_RATIO,
    )
    
    return mock_client, mock_calc, expected_ticker_stats


# 3. TEST CASES


class TestETLServiceProcessingMethod:
    """Tests for the internal `_process_single_symbol` method."""

    def test_process_symbol_success(self, etl_service_setup, successful_processing_mocks):
        """Successful processing path returns a TickerStats and triggers API & calc calls."""
        service, _, _, _, _ = etl_service_setup
        mock_client_detail, mock_calc_detail, expected_ticker_stats = successful_processing_mocks

        service.client = mock_client_detail
        service.calc = mock_calc_detail

        result = service._process_single_symbol("AAPL")

        # 1. API calls were made
        mock_client_detail.get_general.assert_called_once_with("AAPL")
        mock_client_detail.get_financials.assert_has_calls([
            call("AAPL", "income_statement"),
            call("AAPL", "balance_sheet_statement"),
        ], any_order=True)
        mock_client_detail.get_eod.assert_called_once_with("AAPL")

        # 2. Calculation calls were performed
        assert mock_calc_detail.calculate_pe_ratio.called
        assert mock_calc_detail.calculate_revenue_growth.called
        assert mock_calc_detail.calculate_net_income_ttm.called
        assert mock_calc_detail.calculate_debt_ratio.called

        # 3. Result verification
        assert isinstance(result, TickerStats)
        assert result.pe_ratio == expected_ticker_stats.pe_ratio
        assert result.net_income_ttm == expected_ticker_stats.net_income_ttm

    def test_process_symbol_is_filtered(self, etl_service_setup, successful_processing_mocks):
        """If a ticker's industry is not allowed, processing returns None and stops further calls."""
        service, mock_client, _, _, _ = etl_service_setup
        service.client = successful_processing_mocks[0]

        # Return a forbidden industry
        service.client.get_general.return_value = {"fundamentals": {"profile": {"data": [{"industry": "Forbidden Industry"}]}}}

        result = service._process_single_symbol("FORBIDDEN")

        assert result is None
        # No financial API calls should have been made
        assert service.client.get_financials.call_count == 0

    def test_process_symbol_api_error(self, etl_service_setup, caplog):
        """When the API raises an error, processing should return None and log the error."""
        service, mock_client, _, _, _ = etl_service_setup

        mock_client.get_general.side_effect = FiindoClientError("Connection Refused")

        result = service._process_single_symbol("API_FAIL")

        assert result is None
        assert "API error for API_FAIL: Connection Refused" in caplog.text


class TestETLServiceExtractIndustry:
    """Unit tests for the `_extract_industry` helper used to parse API payloads."""

    @pytest.mark.parametrize("input_data, expected_industry", [
        ({"fundamentals": {"profile": {"data": [{"industry": "Software - Application"}]}}}, "Software - Application"),
        ({"fundamentals": {"profile": {"data": [{"industry": "Banks - Diversified"}]}}}, "Banks - Diversified"),
        ({}, None),
        ({"fundamentals": {}}, None),
        ({"fundamentals": {"profile": {"data": []}}}, None),
        ({"fundamentals": {"profile": {"data": [1, {"industry": "Software - Application"}]}}}, None),
    ])
    def test_extract_industry(self, input_data, expected_industry):
        result = ETLService._extract_industry(input_data)
        assert result == expected_industry