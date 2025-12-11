"""Unit tests for FiindoClient API client.

Tests cover:
- HTTP request handling and error cases
- Response parsing and validation
- API endpoint methods (get_symbols, get_general, get_financials, get_eod)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError

from src.clients.fiindo_client import FiindoClient, FiindoClientError


@pytest.fixture
def mock_session():
    """Mock requests.Session for HTTP operations."""
    return MagicMock()


@pytest.fixture
def client(mock_session):
    """Create FiindoClient with mocked session."""
    with patch('src.clients.fiindo_client.requests.Session', return_value=mock_session):
        client = FiindoClient(
            base_url="https://api.test.fiindo.com",
            auth_identifier="test.user",
            timeout=10,
            retries=3,
        )
        client.session = mock_session
        return client


class TestFiindoClientInitialization:
    """Tests for client initialization and configuration."""
    
    def test_client_initialization(self):
        """Test that client initializes with correct configuration."""
        client = FiindoClient(
            base_url="https://api.test.fiindo.com",
            auth_identifier="test.user",
            timeout=15,
            retries=2,
        )
        
        assert client.base_url == "https://api.test.fiindo.com"
        assert client.timeout == 15
        assert "Bearer test.user" in client.session.headers.get("Authorization", "")
    
    
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slashes are stripped from base_url."""
        client = FiindoClient(base_url="https://api.test.fiindo.com/")
        assert client.base_url == "https://api.test.fiindo.com"


class TestGetMethod:
    """Tests for the internal _get() method."""
    
    def test_get_success(self, client):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": "value"}
        mock_response.status_code = 200
        
        client.session.get.return_value = mock_response
        
        result = client._get("/api/v1/test")
        
        assert result == {"data": "value"}
        client.session.get.assert_called_once()
    
    def test_get_with_params(self, client):
        """Test GET request with query parameters."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"result": "ok"}
        
        client.session.get.return_value = mock_response
        
        result = client._get("/api/v1/test", params={"key": "value"})
        
        assert result == {"result": "ok"}
        # Verify params were passed
        call_args = client.session.get.call_args
        assert call_args[1]["params"] == {"key": "value"}
    
    def test_get_error_non_ok_response(self, client):
        """Test GET request that returns error status."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        client.session.get.return_value = mock_response
        
        with pytest.raises(FiindoClientError) as exc_info:
            client._get("/api/v1/notfound")
        
        assert "404" in str(exc_info.value)
    
    def test_get_invalid_json_response(self, client):
        """Test GET request with invalid JSON response."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        client.session.get.return_value = mock_response
        
        with pytest.raises(FiindoClientError) as exc_info:
            client._get("/api/v1/test")
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_get_timeout(self, client):
        """Test GET request that times out."""
        client.session.get.side_effect = Timeout("Request timed out")
        
        with pytest.raises(Timeout):
            client._get("/api/v1/test")


class TestGetSymbols:
    """Tests for get_symbols() endpoint."""
    
    def test_get_symbols_success(self, client):
        """Test successful symbols fetch."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "symbols": ["AAPL", "MSFT", "GOOGL"]
        }
        
        client.session.get.return_value = mock_response
        
        result = client.get_symbols()
        
        assert result == ["AAPL", "MSFT", "GOOGL"]
        # Verify correct endpoint was called
        call_args = client.session.get.call_args
        assert "/api/v1/symbols" in call_args[0][0]
    
    def test_get_symbols_empty_list(self, client):
        """Test symbols endpoint returning empty list."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"symbols": []}
        
        client.session.get.return_value = mock_response
        
        result = client.get_symbols()
        
        assert result == []
    
    def test_get_symbols_invalid_format(self, client):
        """Test symbols endpoint returning invalid format."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = "not a dict"  # Invalid format
        
        client.session.get.return_value = mock_response
        
        with pytest.raises(FiindoClientError) as exc_info:
            client.get_symbols()
        
        assert "Unexpected API response format" in str(exc_info.value)
    
    def test_get_symbols_missing_symbols_field(self, client):
        """Test symbols endpoint missing 'symbols' field."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": []}  # No 'symbols' field
        
        client.session.get.return_value = mock_response
        
        with pytest.raises(FiindoClientError) as exc_info:
            client.get_symbols()
        
        assert "Missing or invalid 'symbols' field" in str(exc_info.value)


class TestGetGeneral:
    """Tests for get_general() endpoint."""
    
    def test_get_general_success(self, client):
        """Test successful general info fetch."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "fundamentals": {
                "profile": {
                    "data": [{"industry": "Software - Application"}]
                }
            }
        }
        
        client.session.get.return_value = mock_response
        
        result = client.get_general("AAPL")
        
        assert isinstance(result, dict)
        assert "fundamentals" in result
        # Verify correct endpoint with symbol
        call_args = client.session.get.call_args
        assert "/api/v1/general/AAPL" in call_args[0][0]
    
    def test_get_general_invalid_response(self, client):
        """Test general endpoint returning invalid format."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = ["not", "a", "dict"]  # Invalid format
        
        client.session.get.return_value = mock_response
        
        with pytest.raises(FiindoClientError) as exc_info:
            client.get_general("AAPL")
        
        assert "Invalid general response format" in str(exc_info.value)


class TestGetEOD:
    """Tests for get_eod() endpoint."""
    
    def test_get_eod_success(self, client):
        """Test successful EOD data fetch."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "stockprice": {
                "data": [
                    {"date": "2025-01-10", "close": 150.0, "volume": 1000000}
                ]
            }
        }
        
        client.session.get.return_value = mock_response
        
        result = client.get_eod("AAPL")
        
        assert isinstance(result, dict)
        assert "stockprice" in result
        # Verify correct endpoint
        call_args = client.session.get.call_args
        assert "/api/v1/eod/AAPL" in call_args[0][0]
    
    def test_get_eod_invalid_response(self, client):
        """Test EOD endpoint returning invalid format."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = []  # Invalid format (not dict)
        
        client.session.get.return_value = mock_response
        
        with pytest.raises(FiindoClientError) as exc_info:
            client.get_eod("AAPL")
        
        assert "Invalid EOD response format" in str(exc_info.value)


class TestGetFinancials:
    """Tests for get_financials() endpoint."""
    
    @pytest.mark.parametrize("statement_type", [
        "income_statement",
        "balance_sheet_statement",
        "cash_flow_statement",
    ])
    def test_get_financials_valid_statements(self, client, statement_type):
        """Test fetching each valid statement type."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "fundamentals": {
                "financials": {
                    statement_type: {"data": []}
                }
            }
        }
        
        client.session.get.return_value = mock_response
        
        result = client.get_financials("AAPL", statement_type)
        
        assert isinstance(result, dict)
        # Verify correct endpoint with statement type
        call_args = client.session.get.call_args
        assert f"/api/v1/financials/AAPL/{statement_type}" in call_args[0][0]
    
    def test_get_financials_invalid_statement(self, client):
        """Test get_financials with invalid statement type."""
        with pytest.raises(ValueError) as exc_info:
            client.get_financials("AAPL", "invalid_statement")
        
        assert "Invalid statement" in str(exc_info.value)
    
    def test_get_financials_invalid_response(self, client):
        """Test financials endpoint returning invalid format."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = "not a dict"  # Invalid format
        
        client.session.get.return_value = mock_response
        
        with pytest.raises(FiindoClientError) as exc_info:
            client.get_financials("AAPL", "income_statement")
        
        assert "Invalid financials response format" in str(exc_info.value)


class TestValidStatements:
    """Tests for VALID_STATEMENTS constant."""
    
    def test_valid_statements_contains_required_types(self):
        """Test that VALID_STATEMENTS has required statement types."""
        assert "income_statement" in FiindoClient.VALID_STATEMENTS
        assert "balance_sheet_statement" in FiindoClient.VALID_STATEMENTS
        assert "cash_flow_statement" in FiindoClient.VALID_STATEMENTS
    
    def test_valid_statements_is_set(self):
        """Test that VALID_STATEMENTS is a set (for fast lookup)."""
        assert isinstance(FiindoClient.VALID_STATEMENTS, set)


class TestFiindoClientError:
    """Tests for FiindoClientError exception."""
    
    def test_fiindo_client_error_is_exception(self):
        """Test that FiindoClientError is an Exception."""
        error = FiindoClientError("Test error")
        assert isinstance(error, Exception)
    
    def test_fiindo_client_error_message(self):
        """Test error message preservation."""
        msg = "API returned 500 error"
        error = FiindoClientError(msg)
        assert str(error) == msg
