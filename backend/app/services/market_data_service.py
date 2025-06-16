import logging
from decimal import Decimal
import random
import requests # For making HTTP requests
from datetime import datetime, timedelta, timezone # For cache expiry and UTC timestamps

from sqlalchemy.orm import Session

from app.config import settings # For API Key and other settings
from app.models.market_data_models import DBMarketDataCache

# Configure logging (ensure it's configured, or use FastAPI's logger)
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO) # Can be configured in main app or config

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
CACHE_EXPIRY_SECONDS = 60  # Cache prices for 60 seconds

# --- CRUD operations for MarketDataCache (can be embedded or separated) ---

def get_cache_entry(db: Session, ticker_symbol: str) -> DBMarketDataCache | None:
    return db.query(DBMarketDataCache).filter(DBMarketDataCache.ticker_symbol == ticker_symbol).first()

def update_cache_entry(db: Session, ticker_symbol: str, price: Decimal) -> DBMarketDataCache:
    """
    Creates or updates a cache entry. Commits are handled by this function.
    """
    cached_item = get_cache_entry(db, ticker_symbol)
    if cached_item:
        cached_item.last_price = price
        # onupdate in model should handle last_updated, but explicit is fine too for Python-side updates
        cached_item.last_updated = datetime.now(timezone.utc)
    else:
        cached_item = DBMarketDataCache(
            ticker_symbol=ticker_symbol,
            last_price=price
            # last_updated will be set by default= on creation via model's Column definition
        )
        db.add(cached_item)
    db.commit() # Commit here as this is a self-contained cache update operation
    db.refresh(cached_item)
    return cached_item

# --- Price Fetching Logic ---

def get_real_current_price_with_source(db: Session, ticker_symbol: str) -> tuple[Decimal | None, str]:
    """
    Fetches the current price for a ticker symbol, using cache or Finnhub API.
    Returns the price and the source ("cached", "realtime_finnhub", "api_key_missing", "finnhub_error", "processing_error").
    """
    normalized_ticker = ticker_symbol.upper()
    source = "unknown" # Default source

    # 1. Check Cache
    cached_data = get_cache_entry(db, normalized_ticker)
    if cached_data:
        current_time_utc = datetime.now(timezone.utc)
        if cached_data.last_updated + timedelta(seconds=CACHE_EXPIRY_SECONDS) > current_time_utc:
            logger.info(f"Returning cached price for {normalized_ticker}: {cached_data.last_price}")
            return cached_data.last_price, "cached"
        else:
            logger.info(f"Cache expired for {normalized_ticker}.")
            source = "cache_expired_refreshing" # Will attempt refresh

    # 2. Fetch from Finnhub API
    if not settings.FINNHUB_API_KEY:
        logger.error("FINNHUB_API_KEY not set. Cannot fetch real market data.")
        return None, "api_key_missing"

    try:
        logger.info(f"Fetching real price for {normalized_ticker} from Finnhub...")
        response = requests.get(
            f"{FINNHUB_BASE_URL}/quote",
            params={"symbol": normalized_ticker, "token": settings.FINNHUB_API_KEY},
            timeout=10 # Add a timeout
        )
        response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)

        response_json = response.json()

        # Finnhub 'c' is current price, 'pc' is previous close.
        # 't' is timestamp of last price.
        # A current price 'c' of 0 can indicate no recent trade data or an issue.
        current_price_value = response_json.get('c')
        if current_price_value is None or float(current_price_value) == 0:
            logger.warning(f"Finnhub returned no current price (c=0 or null) for {normalized_ticker}. Response: {response_json}")
            # This might be a valid case for some tickers or after hours.
            # Depending on requirements, could return previous close 'pc' or None.
            # For now, if 'c' is 0 or None, treat as no reliable current price found.
            return None, "finnhub_no_data"

        current_price = Decimal(str(current_price_value))

        # 3. Update Cache
        update_cache_entry(db, normalized_ticker, current_price)
        logger.info(f"Fetched real price for {normalized_ticker} from Finnhub and updated cache: {current_price}")
        return current_price, "realtime_finnhub"

    except requests.exceptions.Timeout:
        logger.error(f"Timeout when fetching price for {normalized_ticker} from Finnhub.")
        source = "finnhub_timeout"
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred for {normalized_ticker}: {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        source = "finnhub_http_error"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching price for {normalized_ticker} from Finnhub: {e}")
        source = "finnhub_request_error"
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Error processing Finnhub response for {normalized_ticker}: {e}")
        source = "processing_error"

    return None, source


MOCK_PRICES = {
    "AAPL": Decimal("170.25"), "MSFT": Decimal("300.50"), "GOOGL": Decimal("2750.75"),
    "TSLA": Decimal("1000.00"), "NVDA": Decimal("250.60"), "AMZN": Decimal("3200.00"),
    "BTC-USD": Decimal("40000.00"), "EURUSD=X": Decimal("1.08"),
}

def _get_mock_current_price_with_source(ticker_symbol: str, reason: str = "direct mock call") -> tuple[Decimal, str]:
    """
    Internal mock price function, returns price and source.
    """
    ticker_upper = ticker_symbol.upper()
    source_detail = "mock_random"
    if ticker_upper in MOCK_PRICES:
        price = MOCK_PRICES[ticker_upper]
        source_detail = "mock_fixed"
        logger.info(f"Returning predefined mock price for {ticker_upper} due to {reason}: {price}")
    else:
        price = Decimal(str(round(random.uniform(10.00, 5000.00), 2)))
        logger.info(f"No predefined mock price for {ticker_upper}. Returning generated pseudo-random price due to {reason}: {price}")
    return price, source_detail

# This function can be the main one exported/used by other services like crud_trade and the new route
def get_current_price_with_source_info(db: Session, ticker_symbol: str) -> tuple[Decimal | None, str]:
    """
    Tries to get real price (from cache or Finnhub), returns price and its source.
    Falls back to mock price if real price fetch fails completely or API key is missing.
    """
    price, source = get_real_current_price_with_source(db, ticker_symbol)

    if price is not None:
        return price, source
    else:
        # If real price fetch failed (price is None), source indicates the reason for failure.
        # We then fallback to mock price.
        logger.warning(f"Failed to get real price for {ticker_symbol} (reason: {source}). Falling back to mock price.")
        mock_price, mock_source = _get_mock_current_price_with_source(ticker_symbol, reason=f"real_price_fetch_failed_{source}")
        return mock_price, mock_source # mock_source will be mock_fixed or mock_random

# This function is used by crud_trade.py, ensure it still returns just Decimal or update crud_trade.py
# For now, let's make a new function for the route and keep get_price_for_trade as is for crud_trade if it expects only Decimal
def get_price_for_trade(db: Session, ticker_symbol: str) -> Decimal:
    """
    Tries to get real price, falls back to mock price if real price fails.
    This ensures a price is always returned for paper trading (for crud_trade).
    """
    price, _ = get_current_price_with_source_info(db, ticker_symbol)
    # Since _get_mock_current_price_with_source always returns a price,
    # price here should not be None.
    if price is None: # Should theoretically not happen with current mock fallback
        logger.error(f"CRITICAL: Price for {ticker_symbol} resolved to None even after mock fallback. Defaulting to 1.00")
        return Decimal("1.00")
    return price

# Original get_mock_current_price can be an alias or deprecated if needed
# For clarity, it's better to use _get_mock_current_price_with_source internally
# and let get_price_for_trade handle the fallback logic.
# So, removing the alias:
# get_mock_current_price = _get_mock_current_price
