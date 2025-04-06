"""
Module for screening stocks based on financial metrics.
"""

import logging
import time
from typing import List, Dict, Any
from .simple_yahoo import (
    get_penny_stocks,
    get_stock_data,
    get_options_metrics,
)

# from .newsapi_fetcher import get_stock_news # Keep this if you want
# NewsAPI as primary/fallback
from ..utils.helpers import save_json  # Import save_json

# Set up logging directly instead of using the helper
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def screen_penny_stocks(
    min_score: float = 7.0, max_stocks: int = 20
) -> List[Dict[str, Any]]:
    """
    Screen penny stocks using data from Yahoo Finance.
    Returns a list of screened stocks.
    """
    try:
        logger.info("Starting penny stock screening process...")

        screened_stocks = []
        stocks_processed = 0
        stocks_skipped = 0
        start_time = time.time()

        potential_stocks = get_penny_stocks()
        logger.info(f"Found {len(potential_stocks)} potential penny stocks to screen")

        total_potential = len(potential_stocks)
        processed_count = 0

        for ticker in potential_stocks:
            processed_count += 1
            try:
                stock_data = get_stock_data(ticker)
                if not stock_data or stock_data.get("error"):
                    logger.warning(
                        f"Skipping {ticker}: No data or error "
                        f"({stock_data.get('error')})"
                    )
                    stocks_skipped += 1
                    continue

                # Calculate score based on financial metrics
                score = calculate_stock_score(stock_data)
                stock_data["score"] = score  # Add score to the dict

                # Keep stocks with a minimum score
                if score >= min_score:
                    screened_stocks.append(stock_data)
                    stocks_processed += 1
                else:
                    stocks_skipped += 1

                # Log progress periodically
                if processed_count % 5 == 0:
                    logger.info(
                        f"Processed {processed_count}/{total_potential} stocks..."
                    )

            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {e}", exc_info=True)
                stocks_skipped += 1

        # Sort by score descending
        screened_stocks.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Select top N stocks
        top_stocks = screened_stocks[:max_stocks]
        logger.info(f"Selected top {len(top_stocks)} stocks for analysis.")

        # --- Fetch Options Metrics ONLY for Top Stocks --- #
        logger.info(f"Fetching options metrics for top {len(top_stocks)} stocks...")
        for stock in top_stocks:
            ticker = stock.get("ticker")
            if ticker:
                try:
                    stock["options_metrics"] = get_options_metrics(ticker)
                    time.sleep(0.3)  # Small delay between requests
                except Exception as e:
                    logger.error(
                        f"Failed to get options metrics for top stock {ticker}: {e}"
                    )
                    stock["options_metrics"] = {
                        "error": "Error fetching options metrics."
                    }
            else:
                stock["options_metrics"] = {
                    "error": "Ticker not found for options fetching."
                }
        # ------------------------------------------ #

        elapsed_time = time.time() - start_time
        logger.info(
            f"Screening complete. Found {stocks_processed} matching stocks, "
            f"skipped {stocks_skipped}. Time: {elapsed_time:.2f}s"
        )

        # Save results
        # save_json("news_data", news_data, logger) # Remove this - news is now in
        # top_stocks
        save_json("selected_tickers", top_stocks, logger)

        return top_stocks

    except Exception as e:
        logger.error(f"Error in screen_penny_stocks: {str(e)}")
        return []


def calculate_stock_score(stock_data: Dict[str, Any]) -> float:
    """Calculate a comprehensive score for a stock based on multiple criteria."""
    try:
        score = 0

        # Basic validation
        if not stock_data or not isinstance(stock_data, dict):
            logger.debug("Invalid stock data for scoring")
            return 0

        # --- Scoring Criteria --- #

        # Price (under $5 for penny stocks) - Max 15 points
        price = stock_data.get("price")
        if price is not None:
            if price < 1:
                score += 15
            elif price < 3:
                score += 10
            elif price < 5:
                score += 5
        else:
            logger.debug(f"No price for {stock_data.get('ticker')} scoring")

        # Volume vs Average Volume - Max 15 points
        volume = stock_data.get("volume")
        avg_volume = stock_data.get("avg_volume")
        if (
            volume is not None and avg_volume is not None and avg_volume > 10000
        ):  # Ensure avg_volume is meaningful
            try:
                vol_ratio = volume / avg_volume
                if vol_ratio > 2:
                    score += 15
                elif vol_ratio > 1.5:
                    score += 10
                elif vol_ratio > 1:
                    score += 5
            except ZeroDivisionError:
                logger.debug(f"Zero avg volume for {stock_data.get('ticker')}")
        else:
            logger.debug(
                f"Insufficient volume data for {stock_data.get('ticker')} scoring"
            )

        # P/E Ratio (Value) - Max 10 points (Adjusted scoring)
        pe = stock_data.get("pe_ratio")  # Assuming 'pe_ratio' from get_stock_data
        if pe is not None and pe > 0:
            if pe < 10:
                score += 10
            elif pe < 15:
                score += 5
        else:
            logger.debug(f"No P/E for {stock_data.get('ticker')} scoring")

        # Options Sentiment (Put/Call Ratios) - Max 10 points, Min -5
        options_metrics = stock_data.get("options_metrics")
        if options_metrics and not options_metrics.get("error"):
            pc_oi_ratio = options_metrics.get("pc_oi_ratio")
            pc_vol_ratio = options_metrics.get("pc_volume_ratio")

            # Use OI ratio primarily, fallback to Volume ratio if OI is missing
            ratio_to_use = pc_oi_ratio if pc_oi_ratio is not None else pc_vol_ratio

            if ratio_to_use is not None:
                if ratio_to_use < 0.7:
                    score += 10  # Bullish
                elif ratio_to_use < 0.9:
                    score += 5  # Slightly Bullish / Neutral
                elif ratio_to_use > 1.2:
                    score -= 5  # Bearish
                # Ratios between 0.9 and 1.2 are considered neutral
                ticker = stock_data.get("ticker")
                ratio_str = f"{ratio_to_use:.2f}"
                logger.debug(f"Options ratio score: {ticker} Ratio={ratio_str}")
            else:
                logger.debug(f"No usable P/C ratio for {stock_data.get('ticker')}")
        else:
            logger.debug(f"No options metrics for {stock_data.get('ticker')}")

        # Consider adding more criteria (e.g., EPS growth, Beta, Sector trends, IV
        # level)

        # --- Normalization --- #
        # Max possible points: Price(15) + Volume(15) + PE(10) + Options(10) = 50
        max_score_used = 15 + 15 + 10 + 10  # Update this if criteria change

        if max_score_used == 0:
            return 0  # Avoid division by zero

        normalized_score = (score / max_score_used) * 10

        logger.debug(
            f"Score for {stock_data.get('ticker')}: "
            f"Raw={score}, Norm={normalized_score:.2f}"
        )

        return round(normalized_score, 2)  # Return score out of 10

    except Exception as e:
        logger.error(
            f"Error calculating score for {stock_data.get('ticker', 'unknown')}: {e}",
            exc_info=True,
        )
        return 0


def get_potential_picks(
    min_score: float = 7.0, max_stocks: int = 20
) -> List[Dict[str, Any]]:
    """Fetch penny stocks, score them, and return top picks.

    Args:
        min_score: The minimum score a stock must have to be considered.
        max_stocks: The maximum number of stocks to return.

    Returns:
        A list of stocks that meet the criteria.
    """
    # Implementation of get_potential_picks method
    pass
