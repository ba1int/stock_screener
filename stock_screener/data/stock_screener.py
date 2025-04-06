"""
Module for screening stocks based on financial metrics.
"""

import logging
import time
from typing import List, Dict, Any, Tuple
from .simple_yahoo import get_penny_stocks, get_stock_data, get_stock_news
# from .newsapi_fetcher import get_stock_news # Keep this if you want NewsAPI as primary/fallback
import yfinance as yf
from ..utils.helpers import save_json # Import save_json
from ..config import settings # Import settings module

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
                        f"Skipping {ticker}: No data or error ({stock_data.get('error')})"
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

        # --- Fetch News ONLY for Top Stocks --- #
        logger.info(f"Fetching news summaries for top {len(top_stocks)} stocks...")
        for stock in top_stocks:
            ticker = stock.get("ticker")
            if ticker:
                try:
                    stock["news_summary"] = get_stock_news(ticker)
                    time.sleep(0.3) # Small delay between news requests
                except Exception as e:
                     logger.error(f"Failed to get news for top stock {ticker}: {e}")
                     stock["news_summary"] = "Error fetching news."
            else:
                 stock["news_summary"] = "Ticker not found for news fetching."
        # --------------------------------------- #

        elapsed_time = time.time() - start_time
        logger.info(
            f"Screening complete. Found {stocks_processed} matching stocks, skipped {stocks_skipped}. Time: {elapsed_time:.2f}s"
        )

        # Save results
        # save_json("news_data", news_data, logger) # Remove this - news is now in top_stocks
        save_json(
            "selected_tickers", top_stocks, logger
        )  # Save top_stocks which now include news

        return top_stocks

    except Exception as e:
        logger.error(f"Error in screen_penny_stocks: {str(e)}")
        return []


def calculate_stock_score(stock_data: Dict[str, Any]) -> float:
    """Calculate a comprehensive score for a stock based on multiple criteria."""
    try:
        score = 0
        max_score = 100 # Define a theoretical max score for normalization

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
        if volume is not None and avg_volume is not None and avg_volume > 10000: # Ensure avg_volume is meaningful
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
             logger.debug(f"Insufficient volume data for {stock_data.get('ticker')} scoring")

        # P/E Ratio (Value) - Max 10 points (Adjusted scoring)
        pe = stock_data.get("pe_ratio") # Assuming 'pe_ratio' from get_stock_data
        if pe is not None and pe > 0:
            if pe < 10:
                score += 10
            elif pe < 15:
                score += 5
        else:
             logger.debug(f"No P/E for {stock_data.get('ticker')} scoring")

        # Consider adding more criteria (e.g., EPS growth, Beta, Sector trends) if data is available

        # --- Normalization --- #
        # Normalize the score to a 0-10 scale (adjust max_score based on criteria added)
        # Example max_score if only Price(15), Volume(15), PE(10) are used = 40
        max_score_used = 15 + 15 + 10 # Update this if criteria change

        if max_score_used == 0:
             return 0 # Avoid division by zero

        normalized_score = (score / max_score_used) * 10

        logger.debug(f"Score for {stock_data.get('ticker')}: Raw={score}, Norm={normalized_score:.2f}")

        return round(normalized_score, 2) # Return score out of 10

    except Exception as e:
        logger.error(f"Error calculating score for {stock_data.get('ticker', 'unknown')}: {e}", exc_info=True)
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
