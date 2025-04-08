"""
Main entry point for the stock screener (penny or normal).
"""

import logging
import argparse # Import argparse
from .config import settings
from .data.stock_screener import screen_penny_stocks, screen_normal_stocks # Import both screeners
from .analysis.ai_analyzer import analyze_stocks
from .utils.helpers import save_investment_summary

# Set up logging
logger = logging.getLogger(__name__)


def main():
    """Main function to run the stock screener."""
    parser = argparse.ArgumentParser(description="Run the stock screener.")
    parser.add_argument(
        "--type", 
        type=str,
        choices=["penny", "normal"], 
        default="penny", 
        help="Type of stock screener to run (penny or normal). Default: penny"
    )
    parser.add_argument(
        "--max-stocks", 
        type=int,
        default=settings.TOP_N, 
        help=f"Maximum number of stocks to analyze. Default: {settings.TOP_N}"
    )
    parser.add_argument(
        "--min-score", 
        type=float,
        default=7.0, 
        help="Minimum score for penny stocks (ignored for normal). Default: 7.0"
    )
    args = parser.parse_args()

    screener_type = args.type
    max_stocks_to_analyze = args.max_stocks
    min_score_penny = args.min_score

    logger.info(f"Starting {screener_type} stock screener...")

    screened_stocks = []
    screener_name = ""
    analysis_file_prefix = ""

    if screener_type == "penny":
        screener_name = "Penny Stock"
        analysis_file_prefix = "penny_stocks"
        screened_stocks = screen_penny_stocks(
            min_score=min_score_penny,
            max_stocks=max_stocks_to_analyze
        )
    elif screener_type == "normal":
        screener_name = "Normal Stock"
        analysis_file_prefix = "normal_stocks"
        screened_stocks = screen_normal_stocks(
            max_stocks=max_stocks_to_analyze
        )

    if not screened_stocks:
        logger.info(f"No stocks met the {screener_type} screening criteria.")
        return

    # Analyze top N stocks
    logger.info(
        f"Generating detailed analysis for top {len(screened_stocks)} {screener_type} stocks..."
    )
    analyze_stocks(screened_stocks, screener_name, analysis_file_prefix)

    # Save summary (pass prefix to potentially use in filename later)
    logger.info(f"Saving {screener_type} investment summary...")
    save_investment_summary(screened_stocks, analysis_file_prefix)

    logger.info(f"{screener_name} screening process completed.")


if __name__ == "__main__":
    main()
