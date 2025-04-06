"""
Module for scraping stock data from Finviz.
"""

from bs4 import BeautifulSoup
from finviz.screener import Screener
from ..utils.helpers import setup_logging

logger = setup_logging()


def calculate_stock_score(stock_data):
    """Calculate a score for a stock based on multiple criteria."""
    score = 0

    # Price (lower is better for penny stocks)
    if stock_data["price"] is not None:
        if stock_data["price"] < 1:
            score += 20
        elif stock_data["price"] < 2:
            score += 15
        elif stock_data["price"] < 3:
            score += 10
        elif stock_data["price"] < 5:
            score += 5

    # Volume (higher is better for liquidity)
    if stock_data["volume"] is not None:
        if stock_data["volume"] > 1000000:
            score += 20
        elif stock_data["volume"] > 500000:
            score += 15
        elif stock_data["volume"] > 100000:
            score += 10

    # P/E Ratio (lower is better for undervalued stocks)
    if stock_data["pe"] is not None and stock_data["pe"] > 0:
        if stock_data["pe"] < 5:
            score += 25
        elif stock_data["pe"] < 10:
            score += 20
        elif stock_data["pe"] < 15:
            score += 15

    # P/B Ratio (lower is better for undervalued stocks)
    if stock_data["pb"] is not None and stock_data["pb"] > 0:
        if stock_data["pb"] < 0.5:
            score += 25
        elif stock_data["pb"] < 0.75:
            score += 20
        elif stock_data["pb"] < 1:
            score += 15

    # EPS Growth (positive is better)
    if stock_data["eps_growth"] is not None and stock_data["eps_growth"] > 0:
        if stock_data["eps_growth"] > 0.3:  # 30% growth
            score += 20
        elif stock_data["eps_growth"] > 0.2:  # 20% growth
            score += 15
        elif stock_data["eps_growth"] > 0.1:  # 10% growth
            score += 10
        else:
            score += 5

    # RSI (lower is better for oversold conditions)
    if stock_data["rsi"] is not None:
        if stock_data["rsi"] < 30:
            score += 20  # Extremely oversold
        elif stock_data["rsi"] < 40:
            score += 15  # Oversold

    return score


def get_penny_stocks():
    """Get list of penny stocks from Finviz."""
    try:
        logger.info("Fetching penny stocks from Finviz...")

        # Set filters
        filters = [
            "exch_nasd",  # NASDAQ stocks
            "sh_price_u5",  # Price under $5
            "cap_micro",  # Market cap: Micro
            "sh_avgvol_o100",  # Average volume over 100K
            "geo_usa",  # Country: USA
        ]

        # Get the screener results
        stocks = Screener(filters=filters, table="Overview", order="ticker")

        if not stocks:
            logger.warning("No stocks found matching the criteria")
            return []

        # Process the results
        tickers = []
        for stock in stocks:
            try:
                # Get ticker
                ticker = str(stock["Ticker"]).strip().upper()

                # Basic validation - should contain only letters, numbers, and dots
                if not ticker or not all(c.isalnum() or c == "." for c in ticker):
                    logger.warning(f"Invalid ticker format: {ticker}")
                    continue

                # Basic validation of price and volume
                try:
                    price = float(str(stock["Price"]).replace("$", ""))
                    volume = float(str(stock["Volume"]).replace(",", ""))

                    if price > 0 and volume > 0:
                        tickers.append(ticker)
                    else:
                        logger.warning(f"Invalid price or volume for {ticker}")
                except (ValueError, KeyError) as e:
                    logger.debug(
                        f"Error processing price/volume for {ticker}: {str(e)}"
                    )
                    continue

            except Exception as e:
                logger.debug(f"Error processing stock: {str(e)}")
                continue

        logger.info(f"Found {len(tickers)} potential penny stocks")
        return tickers

    except Exception as e:
        logger.error(f"Error fetching stocks from Finviz: {str(e)}")
        return []
