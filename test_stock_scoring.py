"""
Test the stock scoring functionality independently.
"""

import logging
import sys
from stock_screener.data.stock_screener import calculate_stock_score
from stock_screener.data.test_data import SAMPLE_STOCKS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_stock_scoring():
    """Test the stock scoring function with sample data."""
    logger.info("Testing stock scoring functionality...")

    # Score each sample stock
    for stock in SAMPLE_STOCKS:
        try:
            score = calculate_stock_score(stock)
            logger.info(f"Stock: {stock['ticker']} - Score: {score}")

            # Print key factors that went into the score
            logger.info(f"  Price: ${stock['price']:.2f}")
            logger.info(f"  Volume: {stock['volume']:,}")
            if "avg_volume" in stock and stock["avg_volume"]:
                logger.info(f"  Average Volume: {stock['avg_volume']:,}")

            # Show 52-week range if available
            if all(
                k in stock and stock[k] is not None for k in ["high_52w", "low_52w"]
            ):
                range_pct = (
                    (stock["price"] - stock["low_52w"])
                    / (stock["high_52w"] - stock["low_52w"])
                    * 100
                )
                logger.info(f"  Price position in 52w range: {range_pct:.1f}%")

            # Show PE ratio if available
            if "pe_ratio" in stock and stock["pe_ratio"] is not None:
                logger.info(f"  P/E Ratio: {stock['pe_ratio']:.2f}")

            # Show sector/industry
            logger.info(f"  Sector: {stock.get('sector', 'N/A')}")
            logger.info(f"  Industry: {stock.get('industry', 'N/A')}")

            logger.info("-" * 50)

        except Exception as e:
            logger.error(f"Error scoring {stock['ticker']}: {e}")

    logger.info("Stock scoring test completed.")


if __name__ == "__main__":
    test_stock_scoring()
    sys.exit(0)
