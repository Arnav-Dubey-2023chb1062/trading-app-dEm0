import logging
from decimal import Decimal
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOCK_PRICES = {
    "AAPL": Decimal("170.25"),
    "MSFT": Decimal("300.50"),
    "GOOGL": Decimal("2750.75"),
    "TSLA": Decimal("1000.00"),
    "NVDA": Decimal("250.60"), # Added more common tickers
    "AMZN": Decimal("3200.00"),
    "BTC-USD": Decimal("40000.00"), # Example crypto
    "EURUSD=X": Decimal("1.08"),   # Example forex
}

def get_mock_current_price(ticker_symbol: str) -> Decimal:
    """
    Returns a mock current price for a given ticker symbol.
    Uses a predefined dictionary or generates a pseudo-random price.
    """
    ticker_upper = ticker_symbol.upper() # Normalize ticker
    if ticker_upper in MOCK_PRICES:
        price = MOCK_PRICES[ticker_upper]
        logger.info(f"Returning mock price for {ticker_upper}: {price}")
    else:
        # Generate a pseudo-random price for unknown tickers
        price = Decimal(str(round(random.uniform(10.00, 5000.00), 2)))
        logger.info(f"No predefined mock price for {ticker_upper}. Returning generated pseudo-random price: {price}")
    return price
