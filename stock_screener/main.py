"""
Main entry point for the penny stock screener.
"""

import json
import logging
import argparse
from .config import settings
from .data.stock_screener import screen_penny_stocks
from .analysis.ai_analyzer import analyze_stocks
from .utils.helpers import (
    setup_logging,
    save_selected_tickers,
    save_investment_summary,
)

# Set up logging
logger = logging.getLogger(__name__)


def main():
    """Main function to run the stock screener."""
    logger.info("Starting penny stock screener...")

    # Screen stocks
    screened_stocks = screen_penny_stocks(min_score=7.0, max_stocks=settings.TOP_N)

    if not screened_stocks:
        logger.info("No stocks met the screening criteria.")
        return

    # Analyze top N stocks
    logger.info(f"Generating detailed analysis for top {len(screened_stocks)} stocks...")
    analyze_stocks(screened_stocks)

    # Save summary
    logger.info("Saving investment summary...")
    save_investment_summary(screened_stocks)

    logger.info("Penny stock screening process completed.")


if __name__ == "__main__":
    main()
