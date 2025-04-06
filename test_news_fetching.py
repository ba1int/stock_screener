"""
Test the news fetching functionality independently.
"""

import logging
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from stock_screener.data.newsapi_fetcher import get_stock_news
from stock_screener.data.test_data import SAMPLE_STOCKS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_news_fetching_single_stock():
    """Test news fetching for a single stock."""
    logger.info("Testing news fetching for a single stock...")

    if len(SAMPLE_STOCKS) > 0:
        # Select just one stock for testing
        test_stock = SAMPLE_STOCKS[0]
        ticker = test_stock["ticker"]
        logger.info(f"Fetching news for {ticker}...")

        try:
            news = get_stock_news(ticker)
            logger.info(f"News for {ticker}:")
            logger.info(news if news else "No news found")
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
    else:
        logger.warning("No sample stocks available for testing")


def test_news_fetching_multiple_stocks():
    """Test news fetching for multiple stocks."""
    logger.info("Testing news fetching for multiple stocks (limited sample)...")

    # Use a subset of stocks for testing
    test_stocks = SAMPLE_STOCKS[:3]  # Just test with 3 stocks
    news_data = {}

    for stock in test_stocks:
        ticker = stock["ticker"]
        logger.info(f"Fetching news for {ticker}...")

        try:
            news = get_stock_news(ticker)
            news_data[ticker] = news
            logger.info(f"Retrieved news for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")

    # Save results to a file
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_file = results_dir / f"news_test_{date_str}.json"

    # Save the results
    with open(result_file, "w") as f:
        json.dump(news_data, f, indent=2)

    logger.info(f"News data saved to {result_file}")

    # Show a summary
    logger.info("News fetching summary:")
    for ticker, news in news_data.items():
        status = (
            "Success" if news and news != "No recent news found." else "No news found"
        )
        logger.info(f"  {ticker}: {status}")


def test_news_with_sample_data():
    """Test with the pre-defined sample news data."""
    from stock_screener.data.test_data import SAMPLE_NEWS_DATA

    logger.info("Testing with sample news data...")

    for ticker, news in SAMPLE_NEWS_DATA.items():
        logger.info(f"Sample news for {ticker}:")
        logger.info(news)
        logger.info("-" * 50)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test news fetching functionality")
    parser.add_argument(
        "--single", action="store_true", help="Test with a single stock"
    )
    parser.add_argument(
        "--sample", action="store_true", help="Test with sample data (no API calls)"
    )

    args = parser.parse_args()

    if args.single:
        # Test with just a single stock
        test_news_fetching_single_stock()
    elif args.sample:
        # Test with sample data (no API calls)
        test_news_with_sample_data()
    else:
        # Test with multiple stocks
        test_news_fetching_multiple_stocks()

    sys.exit(0)
