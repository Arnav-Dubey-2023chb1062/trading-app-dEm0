import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables from a .env file if it exists
# This allows for local development without setting system-wide environment variables.
# In production, environment variables should be set directly in the environment.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    logger.info(f"Loading .env file from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    logger.info(".env file not found, relying on system environment variables.")


class Settings:
    # Database URL
    # The default value is a placeholder and should be configured for any real deployment.
    SQLALCHEMY_DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://your_db_user:your_db_password@localhost/trading_app_db"
    )
    if SQLALCHEMY_DATABASE_URL == "postgresql://your_db_user:your_db_password@localhost/trading_app_db":
        logger.warning(
            "Using default placeholder DATABASE_URL. Please set a proper DATABASE_URL environment variable."
        )

    # Finnhub API Key
    FINNHUB_API_KEY: str | None = os.getenv("FINNHUB_API_KEY")
    if not FINNHUB_API_KEY:
        logger.warning(
            "FINNHUB_API_KEY environment variable not set. "
            "Real-time market data features from Finnhub will not be available."
        )
        # FINNHUB_API_KEY = "YOUR_FALLBACK_OR_MOCK_KEY_IF_ANY" # Example if a fallback were used

    # JWT Settings (from auth_service.py, can be centralized here)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-default-should-be-changed") # Default is insecure
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    if SECRET_KEY == "your-secret-key-default-should-be-changed":
        logger.warning(
            "Using default SECRET_KEY. This is insecure. Please set a strong SECRET_KEY environment variable."
        )


# Create an instance of the settings
settings = Settings()
