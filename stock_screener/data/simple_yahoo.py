"""
Simple Yahoo Finance integration for stock screening.
"""

import yfinance as yf
import logging
import time
from functools import lru_cache
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import RequestException
from ..config import settings
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Expanded list of potential penny stock tickers across various sectors
PENNY_STOCKS_LIST = list(set([
    # Technology
    "SIRI", "NOK", "GPRO", "BB", "SSYS", "IQ", "RAD", "PLTR", "SOFI", "CLSK",
    # Healthcare
    "ACRX", "SRNE", "NVAX", "MNKD", "PGNX", "CTXR", "SESN", "ATOS", "SNDL", "VXRT",
    # Energy
    "FCEL", "PLUG", "UUUU", "CPE", "SHIP", "BORR", "TELL", "WWR", "RIG", "NOG",
    # Retail
    "EXPR", "GME", "AMC", "BBBY", "WISH", "KOSS", "NAKD", "SFIX", "POSH", "REAL",
    # Mining
    "BTG", "NAK", "GPL", "EGO", "HL", "SVM", "MUX", "AG", "PAAS", "MAG",
    # Biotech
    "OCGN", "INO", "BCRX", "BNGO", "AMRN", "TTOO", "CODX", "ADMA", "IBIO", "OGEN",
    # Finance
    "FAMI", "METX", "BK", "IVR", "TWO", "XSPA", "CLOV", "UWMC", "GSAT", "MNMD",
    # Other
    "IDEX", "MARA", "RIOT", "SOS", "ZOM", "GEVO", "SENS", "TRCH", "CIDM", "MVIS"
])) # Use set to remove duplicates


def get_penny_stocks() -> List[str]:
    """Get a list of penny stocks."""
    logger.info("Starting penny stock screening")
    penny_stocks = []

    # Use our expanded predefined list
    for i, ticker in enumerate(PENNY_STOCKS_LIST):
        try:
            # Add delay every 3 requests
            if i > 0 and i % 3 == 0:
                time.sleep(0.5)

            # Get stock info
            logger.info(f"Checking {ticker}...")
            stock = yf.Ticker(ticker)

            try:
                # Try to get the current price
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
                    if price < 5:
                        penny_stocks.append(ticker)
                        logger.info(f"Added penny stock: {ticker} (${price:.2f})")
            except Exception as e:
                logger.warning(f"Error getting history for {ticker}: {e}")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")

    logger.info(f"Found {len(penny_stocks)} penny stocks")
    return penny_stocks


@lru_cache(maxsize=256)
@retry(stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES), wait=wait_exponential(multiplier=1, min=1, max=settings.YAHOO_TIMEOUT // 2), retry=retry_if_exception_type(RequestException))
def get_stock_data(ticker: str) -> Dict[str, Any]:
    """Get detailed data for a stock."""
    logger.info(f"Getting data for {ticker}")
    try:
        stock = yf.Ticker(ticker)

        # Get basic info
        info = {}
        try:
            info = stock.info
        except Exception as e:
            logger.warning(f"Could not get info for {ticker}: {e}")

        # Get recent price data
        price_data = {}
        try:
            hist = stock.history(period="1y")
            if not hist.empty:
                price_data = {
                    "current_price": hist["Close"].iloc[-1],
                    "volume": hist["Volume"].iloc[-1],
                    "high_52w": hist["High"].max(),
                    "low_52w": hist["Low"].min(),
                    "avg_volume": hist["Volume"].mean(),
                }
        except Exception as e:
            logger.warning(f"Could not get price data for {ticker}: {e}")

        # Combine data
        stock_data = {
            "ticker": ticker,
            "price": price_data.get("current_price", None),
            "volume": price_data.get("volume", None),
            "avg_volume": price_data.get("avg_volume", None),
            "high_52w": price_data.get("high_52w", None),
            "low_52w": price_data.get("low_52w", None),
            "company_name": info.get("shortName", "Unknown"),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", None),
            "pe_ratio": info.get("trailingPE", None),
            "eps": info.get("trailingEps", None),
            "dividend_yield": info.get("dividendYield", None),
            "beta": info.get("beta", None),
            "description": info.get("longBusinessSummary", None),
        }

        return stock_data
    except RequestException as e:
        logger.error(f"Network error fetching data for {ticker}: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error fetching data for {ticker}: {e}")
        return {"error": f"Unexpected error fetching data for {ticker}: {e}"}


@lru_cache(maxsize=128)
@retry(stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES), wait=wait_exponential(multiplier=1, min=1, max=5), retry=retry_if_exception_type(RequestException))
def get_stock_news(ticker: str) -> str:
    """Get news for a stock, include date, with retry logic."""
    logger.info(f"Getting news for {ticker}")
    try:
        stock = yf.Ticker(ticker)

        # Get news
        news = []
        try:
            raw_news = stock.news
            if raw_news:
                news = raw_news
        except Exception as e:
            logger.warning(f"Could not get news for {ticker} via yfinance: {e}")
            # Optionally add a fallback news source here if needed

        if not news:
             logger.warning(f"No news found for {ticker}")
             return "No recent news found."

        news_text = ""
        for i, item in enumerate(news[:5]):  # Top 5 news items
            try:
                title = item.get("title", "No title")
                link = item.get("link", "#")
                publisher = item.get("publisher", "Unknown")
                publish_time = item.get("providerPublishTime")

                date_str = ""
                if publish_time:
                    try:
                        # Convert timestamp to readable date
                        date_str = datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d")
                    except Exception as date_e:
                        logger.debug(f"Could not parse news timestamp {publish_time}: {date_e}")
                        date_str = "(Date unknown)"
                else:
                    date_str = "(Date unknown)"

                news_text += f"- [{title}]({link}) - {publisher} {date_str}\n"
            except Exception as item_e:
                 logger.debug(f"Error formatting news item for {ticker}: {item_e}")

        return news_text if news_text else "Error processing news."

    except RequestException as e:
        logger.error(f"Network error getting news for {ticker}: {e}")
        raise e # Reraise for retry
    except Exception as e:
        logger.error(f"Unexpected error getting news for {ticker}: {e}")
        return "Error fetching news."
