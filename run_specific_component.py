"""
Run specific components of the stock screener separately.
"""

import logging
import sys
import argparse
from pathlib import Path
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_stock_fetch():
    """Run just the stock fetching component."""
    from stock_screener.data.simple_yahoo import get_penny_stocks

    logger.info("Running stock fetching component...")

    start_time = time.time()
    tickers = get_penny_stocks()
    elapsed_time = time.time() - start_time

    logger.info(f"Found {len(tickers)} penny stocks in {elapsed_time:.2f} seconds")

    if tickers:
        logger.info(f"First 10 tickers: {tickers[:10]}")

        # Save tickers to a file
        results_dir = Path("component_results")
        results_dir.mkdir(exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_file = results_dir / f"penny_stocks_{date_str}.txt"

        with open(result_file, "w") as f:
            for ticker in tickers:
                f.write(f"{ticker}\n")

        logger.info(f"Saved {len(tickers)} tickers to {result_file}")


def run_stock_screening():
    """Run just the stock screening component."""
    from stock_screener.data.stock_screener import calculate_stock_score
    from stock_screener.data.simple_yahoo import get_stock_data

    # Either use saved tickers or a sample set
    sample_tickers = ["AAPL", "FCEL", "OCGN", "NOK", "AMC"]

    logger.info(
        f"Running stock screening component with {len(sample_tickers)} sample tickers..."
    )

    # Get data and score for each ticker
    results = []
    for ticker in sample_tickers:
        logger.info(f"Processing {ticker}...")

        try:
            stock_data = get_stock_data(ticker)
            if "error" not in stock_data:
                score = calculate_stock_score(stock_data)
                stock_data["score"] = score
                results.append(stock_data)
                logger.info(f"{ticker} - Score: {score}")
            else:
                logger.warning(f"Error with {ticker}: {stock_data['error']}")
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")

    # Sort by score
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Save results to a file
    if results:
        import json
        from stock_screener.utils.helpers import NumpyJSONEncoder

        results_dir = Path("component_results")
        results_dir.mkdir(exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_file = results_dir / f"screened_stocks_{date_str}.json"

        # Save the results
        with open(result_file, "w") as f:
            json.dump(results, f, cls=NumpyJSONEncoder, indent=2)

        logger.info(f"Saved {len(results)} screened stocks to {result_file}")


def run_news_fetching():
    """Run just the news fetching component."""
    from stock_screener.data.newsapi_fetcher import get_stock_news

    # Use a sample set of tickers
    sample_tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]

    logger.info(
        f"Running news fetching component with {len(sample_tickers)} sample tickers..."
    )

    # Get news for each ticker
    news_data = {}
    for ticker in sample_tickers:
        logger.info(f"Fetching news for {ticker}...")

        try:
            news = get_stock_news(ticker)
            news_data[ticker] = news
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")

    # Save news data to a file
    if news_data:
        import json

        results_dir = Path("component_results")
        results_dir.mkdir(exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_file = results_dir / f"news_data_{date_str}.json"

        # Save the news data
        with open(result_file, "w") as f:
            json.dump(news_data, f, indent=2)

        logger.info(f"Saved news data for {len(news_data)} tickers to {result_file}")


def run_ai_analysis():
    """Run just the AI analysis component with sample data."""
    from stock_screener.analysis.ai_analyzer import analyze_stocks
    from stock_screener.data.test_data import SAMPLE_STOCKS

    # Use sample stocks data
    sample_data = SAMPLE_STOCKS[:2]  # Just use 2 stocks to save costs

    logger.info(
        f"Running AI analysis component with {len(sample_data)} sample stocks..."
    )

    # Make copies to avoid modifying the originals
    test_stocks = [stock.copy() for stock in sample_data]

    # Run analysis
    analyze_stocks(test_stocks)

    # Save results to a file
    if test_stocks:
        import json
        from stock_screener.utils.helpers import NumpyJSONEncoder

        results_dir = Path("component_results")
        results_dir.mkdir(exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_file = results_dir / f"ai_analysis_{date_str}.json"

        # Extract just what we need
        simplified_results = []
        for stock in test_stocks:
            simplified_stock = {
                "ticker": stock["ticker"],
                "price": stock["price"],
                "company_name": stock.get("company_name", "Unknown"),
            }
            if "analysis" in stock:
                simplified_stock["analysis"] = stock["analysis"]
            simplified_results.append(simplified_stock)

        # Save the results
        with open(result_file, "w") as f:
            json.dump(simplified_results, f, cls=NumpyJSONEncoder, indent=2)

        logger.info(f"Saved AI analysis results to {result_file}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run specific components of the stock screener"
    )

    # Add arguments for each component
    parser.add_argument(
        "--fetch", action="store_true", help="Run stock fetching component"
    )
    parser.add_argument(
        "--screen", action="store_true", help="Run stock screening component"
    )
    parser.add_argument(
        "--news", action="store_true", help="Run news fetching component"
    )
    parser.add_argument(
        "--analyze", action="store_true", help="Run only the AI analysis component"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Check if any flags were provided
    if not (args.fetch or args.screen or args.news or args.analyze):
        logger.error(
            "No components specified. Use --fetch, --screen, --news, or --analyze"
        )
        sys.exit(1)

    # Create results directory
    Path("component_results").mkdir(exist_ok=True)

    # Run selected components
    if args.fetch:
        run_stock_fetch()

    if args.screen:
        run_stock_screening()

    if args.news:
        run_news_fetching()

    if args.analyze:
        run_ai_analysis()

    logger.info("All selected components completed")
    sys.exit(0)
