"""
Configuration settings for the penny stock screener.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the root directory
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / '.env'
logger.info(f"Looking for .env file at: {env_path.absolute()}")

if not env_path.exists():
    logger.error(f".env file not found at {env_path.absolute()}")
    raise FileNotFoundError(f".env file not found at {env_path.absolute()}")

# Load environment variables
load_dotenv(dotenv_path=env_path)
logger.info("Loaded .env file successfully")

# API Keys with validation
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  # Use environ.get instead of getenv
logger.info(f"OpenAI API Key found: {'Yes' if OPENAI_API_KEY else 'No'}")

if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OpenAI API key not found in environment variables")

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')  # Use environ.get instead of getenv
if not NEWS_API_KEY:
    logger.error("News API key not found in environment variables")
    raise ValueError("News API key not found in environment variables")

# File paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RESULTS_DIR = DATA_DIR / 'results'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Price and Market Cap Filters
PRICE_MIN = 0.50  # Minimum price to avoid extreme delisting risk
PRICE_MAX = 5.0  # Maximum price for penny stocks
MARKET_CAP_MIN = 25000000  # Minimum $25M market cap
MARKET_CAP_MAX = 2000000000  # Maximum $2B market cap

# Volume and Liquidity Filters
VOLUME_MIN = 200000  # Minimum average daily volume
RELATIVE_VOLUME_MIN = 1.2  # Minimum relative volume

# Valuation Filters
PE_MAX = 40.0  # Maximum P/E ratio
PB_MAX = 3.0  # Maximum P/B ratio
PEG_MAX = 2.5  # Maximum PEG ratio

# Performance Filters
EPS_GROWTH_MIN = -0.10  # Allow some EPS decline
REVENUE_GROWTH_MIN = 0.10  # Minimum 10% revenue growth
PROFIT_MARGIN_MIN = -0.15  # Allow some losses but not extreme

# Technical Filters
RSI_MIN = 20  # Allow more oversold conditions
RSI_MAX = 80  # Allow more overbought conditions

# Risk Filters
DEBT_EQUITY_MAX = 2.0  # Allow higher debt for growth companies
BETA_MIN = 0.3  # Allow lower correlation with market
BETA_MAX = 3.0  # Allow higher volatility

# Quality Filters
INSIDER_OWNERSHIP_MIN = 0.02  # Minimum 2% insider ownership
INSTITUTIONAL_OWNERSHIP_MIN = 0.10  # Minimum 10% institutional ownership

# Analysis Settings
TOP_N = 10  # Number of top stocks to analyze in detail
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)

# Technical analysis parameters
RSI_PERIOD = 14
SMA_FAST = 50
SMA_SLOW = 200
VOLUME_MA_PERIOD = 20

# API Settings
YAHOO_MAX_RETRIES = int(os.getenv('YAHOO_MAX_RETRIES', 3))
YAHOO_TIMEOUT = int(os.getenv('YAHOO_TIMEOUT', 10))

# Logging Configuration
LOG_FORMAT = '[%(levelname)s] %(message)s'

# Default filters for penny stocks
DEFAULT_FILTERS = {
    'price': {'min': 0.1, 'max': 5.0},
    'volume': {'min': 100000},
    'market_cap': {'min': 50000000},  # $50M minimum market cap
    'rsi': {'max': 40},  # Oversold condition
    'sma_50_200_ratio': {'min': 0.8},  # Within 20% of 200-day MA
    'beta': {'min': 1.2},  # Higher volatility
}

# Analysis settings
TECHNICAL_WEIGHT = 0.4
FUNDAMENTAL_WEIGHT = 0.3
SENTIMENT_WEIGHT = 0.3

# Technical parameters
RSI_PERIOD = 14
SMA_PERIODS = [20, 50, 200]
VOLUME_MA_PERIOD = 20

# News API Settings
NEWS_CACHE_DURATION = 1800  # Cache news data for 30 minutes
MAX_NEWS_ARTICLES = 5      # Maximum number of news articles per stock
NEWS_LOOKBACK_DAYS = 7     # Look back this many days for news 