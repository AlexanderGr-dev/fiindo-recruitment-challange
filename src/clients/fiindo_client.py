"""HTTP client for communicating with the Fiindo API."""

import logging
import requests
from typing import List, Dict, Any, Optional, Set
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.config import settings

logger = logging.getLogger(__name__)


class FiindoClientError(Exception):
    """Raised when Fiindo API communication fails."""
    pass


class FiindoClient:

    VALID_STATEMENTS: Set[str] = {
        "income_statement",
        "balance_sheet_statement",
        "cash_flow_statement",
    }
    
    def __init__(
        self,
        base_url: str = settings.FIINDO_API_BASE,
        auth_identifier: str = settings.FIINDO_AUTH,
        timeout: int = settings.HTTP_TIMEOUT,
        retries: int = settings.HTTP_RETRIES,
    ):
        """Create a `FiindoClient`.

        Args:
            base_url: Base URL for the Fiindo API (no trailing slash required).
            auth_identifier: Identifier used in the `Authorization` header
                (format: `{first_name}.{last_name}`).
            timeout: Per-request timeout in seconds.
            retries: Number of retry attempts for transient HTTP errors.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {auth_identifier}",
            "Accept": "application/json",
        })

        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=0.5,
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=15, 
            pool_maxsize=15      
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)


    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        url = f"{self.base_url}{path}"
        """Perform a GET request and return parsed JSON."""

        logger.debug("GET %s | params=%s", url, params)

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        if not response.ok:
            logger.error(
                "Fiindo API error %s | %s",
                response.status_code,
                response.text,
            )
            raise FiindoClientError(
                f"Fiindo API error {response.status_code}: {response.text}"
            )

        logger.debug("Response received (%s)", response.status_code)

        try:
            return response.json()
        except ValueError as exc:
            raise FiindoClientError("Invalid JSON response") from exc



    def get_symbols(self) -> List[str]:
        """Return the list of symbols available from the Fiindo API.

        Validates the response structure and raises `FiindoClientError` for
        unexpected formats.
        """

        logger.info("Fetching symbols from Fiindo API")

        data = self._get("/api/v1/symbols")

        if not isinstance(data, dict):
            logger.error("Unexpected API response format: %s", type(data))
            raise FiindoClientError("Unexpected API response format")

        symbols = data.get("symbols")

        if not isinstance(symbols, list):
            logger.error("Missing or invalid 'symbols' field in response")
            raise FiindoClientError("Missing or invalid 'symbols' field")

        if not symbols:
            logger.warning("Fiindo API returned empty symbols list")

        logger.info("Fetched %d symbols", len(symbols))
        return symbols
    
    def get_general(self, symbol: str) -> Dict[str, Any]:
        """Fetch and return general information for `symbol`.

        The returned value is expected to be a dictionary matching the API
        shape; callers should validate deeper fields as needed.
        """
        logger.debug("Fetching general info for symbol=%s", symbol)

        path = f"/api/v1/general/{symbol}"
        data = self._get(path)

        if not isinstance(data, dict):
            logger.error("Invalid general response for symbol=%s", symbol)
            raise FiindoClientError("Invalid general response format")

        return data
    
    def get_eod(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch end-of-day (EOD) price data for `symbol`.

        Returns the raw parsed JSON from the API; callers should validate
        the expected keys (e.g., `stockprice`).
        """
        logger.debug("Fetching EOD data for symbol=%s", symbol)

        path = f"/api/v1/eod/{symbol}"
        data = self._get(path)

        if not isinstance(data, dict):
            logger.error("Invalid EOD response for symbol=%s", symbol)
            raise FiindoClientError("Invalid EOD response format")

        return data
    
    def get_financials(self, symbol: str, statement: str) -> Dict[str, Any]:
        """Fetch a financial statement for `symbol`.

        Args:
            symbol: Ticker symbol to fetch financials for.
            statement: One of the values in `FiindoClient.VALID_STATEMENTS`.

        Returns the parsed JSON dictionary for the requested statement.
        Raises `ValueError` for invalid `statement` values and
        `FiindoClientError` for invalid API responses.
        """
        if statement not in self.VALID_STATEMENTS:
            raise ValueError(
                f"Invalid statement '{statement}'. "
                f"Must be one of {self.VALID_STATEMENTS}"
            )

        logger.debug(
            "Fetching financials for symbol=%s, statement=%s",
            symbol,
            statement,
        )

        path = f"/api/v1/financials/{symbol}/{statement}"
        data = self._get(path)

        if not isinstance(data, dict):
            logger.error(
                "Invalid financials response for symbol=%s, statement=%s",
                symbol,
                statement,
            )
            raise FiindoClientError("Invalid financials response format")

        return data



