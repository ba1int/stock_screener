"""
Simple Yahoo Finance integration for stock screening.
"""

import yfinance as yf
import logging
import time
from functools import lru_cache
from typing import List, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from requests.exceptions import RequestException
from ..config import settings
from datetime import datetime
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Expanded list of potential penny stock tickers across various sectors
PENNY_STOCKS_LIST = list(
    set(
        [
            # Technology
            "SIRI",
            "NOK",
            "GPRO",
            "BB",
            "SSYS",
            "IQ",
            "RAD",
            "PLTR",
            "SOFI",
            "CLSK",
            # Healthcare
            "ACRX",
            "SRNE",
            "NVAX",
            "MNKD",
            "PGNX",
            "CTXR",
            "SESN",
            "ATOS",
            "SNDL",
            "VXRT",
            # Energy
            "FCEL",
            "PLUG",
            "UUUU",
            "CPE",
            "SHIP",
            "BORR",
            "TELL",
            "WWR",
            "RIG",
            "NOG",
            # Retail
            "EXPR",
            "GME",
            "AMC",
            "BBBY",
            "WISH",
            "KOSS",
            "NAKD",
            "SFIX",
            "POSH",
            "REAL",
            # Mining
            "BTG",
            "NAK",
            "GPL",
            "EGO",
            "HL",
            "SVM",
            "MUX",
            "AG",
            "PAAS",
            "MAG",
            # Biotech
            "OCGN",
            "INO",
            "BCRX",
            "BNGO",
            "AMRN",
            "TTOO",
            "CODX",
            "ADMA",
            "IBIO",
            "OGEN",
            # Finance
            "FAMI",
            "METX",
            "BK",
            "IVR",
            "TWO",
            "XSPA",
            "CLOV",
            "UWMC",
            "GSAT",
            "MNMD",
            # Other
            "IDEX",
            "MARA",
            "RIOT",
            "SOS",
            "ZOM",
            "GEVO",
            "SENS",
            "TRCH",
            "CIDM",
            "MVIS",
        ]
    )
)  # Use set to remove duplicates


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
@retry(
    stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=settings.YAHOO_TIMEOUT // 2),
    retry=retry_if_exception_type(RequestException),
)
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
@retry(
    stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(RequestException),
)
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
                        date_str = datetime.fromtimestamp(publish_time).strftime(
                            "%Y-%m-%d"
                        )
                    except Exception as date_e:
                        logger.debug(
                            f"Could not parse news timestamp {publish_time}: {date_e}"
                        )
                        date_str = "(Date unknown)"
                else:
                    date_str = "(Date unknown)"

                news_text += f"- [{title}]({link}) - {publisher} {date_str}\n"
            except Exception as item_e:
                logger.debug(f"Error formatting news item for {ticker}: {item_e}")

        return news_text if news_text else "Error processing news."

    except RequestException as e:
        logger.error(f"Network error getting news for {ticker}: {e}")
        raise e  # Reraise for retry
    except Exception as e:
        logger.error(f"Unexpected error getting news for {ticker}: {e}")
        return "Error fetching news."


# --- Options Data --- #


@lru_cache(maxsize=256)
@retry(
    stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=settings.YAHOO_TIMEOUT // 2),
    retry=retry_if_exception_type(RequestException),
)
def get_options_metrics(ticker: str) -> Dict[str, Any]:
    """Fetch options chain data and calculate key metrics.

    Calculates Put/Call ratios (Volume & Open Interest) and a
    weighted average Implied Volatility for a near-term expiration.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A dictionary containing options metrics, or an error dict.
    """
    logger.info(f"Getting options metrics for {ticker}")
    try:
        stock = yf.Ticker(ticker)

        # 1. Get Expiration Dates
        try:
            expiries = stock.options
            if not expiries:
                logger.warning(f"No options expiration dates found for {ticker}")
                return {"error": "No options data available"}
        except Exception as e:
            logger.warning(f"Could not retrieve options expirations for {ticker}: {e}")
            return {"error": "Failed to retrieve options expirations"}

        # 2. Select Target Expiration (approx 30-60 days out)
        today = datetime.today().date()
        target_expiry = None
        min_days = 30
        max_days = 60

        valid_expiries = []
        for expiry_str in expiries:
            try:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                days_to_expiry = (expiry_date - today).days
                if min_days <= days_to_expiry <= max_days:
                    valid_expiries.append((days_to_expiry, expiry_str))
            except ValueError:
                logger.debug(f"Could not parse expiry date: {expiry_str} for {ticker}")
                continue

        if not valid_expiries:
            # Fallback: try nearest expiry if none in 30-60 day range
            logger.debug(
                f"No expiry found in {
                    min_days}-{max_days} days for {ticker}. Trying nearest."
            )
            for expiry_str in expiries:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    days_to_expiry = (expiry_date - today).days
                    if days_to_expiry > 0:  # Ensure it's in the future
                        valid_expiries.append((days_to_expiry, expiry_str))
                except ValueError:
                    continue
            if not valid_expiries:
                logger.warning(f"No valid future expiration dates found for {ticker}")
                return {"error": "No suitable options expiration dates found"}

        # Select the expiry closest to our target range (or just the nearest future)
        valid_expiries.sort()  # Sort by days_to_expiry
        target_expiry = valid_expiries[0][1]  # [1] gets the date string
        logger.info(f"Selected expiry {target_expiry} for {ticker}")

        # 3. Fetch Option Chain for selected expiry
        try:
            opt_chain = stock.option_chain(target_expiry)
            calls = opt_chain.calls
            puts = opt_chain.puts
        except Exception as e:
            logger.warning(
                f"Could not retrieve option chain for {
                    ticker} expiry {target_expiry}: {e}"
            )
            return {"error": f"Failed to retrieve option chain for {target_expiry}"}

        if calls.empty and puts.empty:
            logger.warning(f"Option chain empty for {ticker} expiry {target_expiry}")
            return {"error": "Option chain is empty"}

        # 4. Calculate Put/Call Ratios
        total_call_volume = calls["volume"].sum() if "volume" in calls.columns else 0
        total_put_volume = puts["volume"].sum() if "volume" in puts.columns else 0
        total_call_oi = (
            calls["openInterest"].sum() if "openInterest" in calls.columns else 0
        )
        total_put_oi = (
            puts["openInterest"].sum() if "openInterest" in puts.columns else 0
        )

        pc_volume_ratio = (
            total_put_volume / total_call_volume if total_call_volume > 0 else None
        )
        pc_oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else None

        # 5. Calculate Weighted Average IV
        # Combine calls and puts, filter out zero OI or IV
        all_options = pd.concat([calls, puts])
        valid_iv_options = all_options[
            (all_options["openInterest"] > 0) & (all_options["impliedVolatility"] > 0)
        ].copy()

        weighted_iv = None
        if not valid_iv_options.empty:
            valid_iv_options["iv_x_oi"] = (
                valid_iv_options["impliedVolatility"] * valid_iv_options["openInterest"]
            )
            total_oi_for_iv = valid_iv_options["openInterest"].sum()
            if total_oi_for_iv > 0:
                weighted_iv = valid_iv_options["iv_x_oi"].sum() / total_oi_for_iv

        # 6. Return results
        metrics = {
            "selected_expiry": target_expiry,
            "pc_volume_ratio": (
                round(pc_volume_ratio, 3) if pc_volume_ratio is not None else None
            ),
            "pc_oi_ratio": round(pc_oi_ratio, 3) if pc_oi_ratio is not None else None,
            "average_iv": round(weighted_iv, 4) if weighted_iv is not None else None,
            "total_volume": int(total_call_volume + total_put_volume),  # Cast to int
            "total_open_interest": int(total_call_oi + total_put_oi),  # Cast to int
        }
        logger.debug(f"Options metrics for {ticker}: {metrics}")
        return metrics

    except RequestException as e:
        logger.error(f"Network error fetching options data for {ticker}: {e}")
        raise e  # Reraise to trigger retry
    except Exception as e:
        logger.error(
            f"Unexpected error fetching options data for {ticker}: {e}", exc_info=True
        )
        return {"error": f"Unexpected error fetching options data for {ticker}"}
