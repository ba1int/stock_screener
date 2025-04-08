"""
Module for screening stocks based on financial metrics.
"""

import logging
import time
from typing import List, Dict, Any
from .simple_yahoo import (
    # get_penny_stocks, # This was renamed
    get_potential_penny_stocks, # Use the renamed function
    get_stock_data,
    get_options_metrics,
    # get_potential_penny_stocks, # Already imported above
    get_potential_normal_stocks,
)
from ..utils.helpers import save_json # Restore this import

# from .newsapi_fetcher import get_stock_news # Keep this if you want
# NewsAPI as primary/fallback
# from ..utils.helpers import save_json # Import save_json # Removed unused news saving

# Set up logging directly instead of using the helper
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import settings for risk filters
from ..config import settings

def screen_penny_stocks(
    min_score: float = 7.0, max_stocks: int = 20
) -> List[Dict[str, Any]]:
    """
    Screen penny stocks using data from Yahoo Finance.
    Returns a list of screened stocks.

    Args:
        min_score: Minimum score threshold (0-10)
        max_stocks: Maximum number of stocks to return

    Returns:
        List of stock dictionaries that meet the criteria
    """
    # Validate input parameters
    validate_screening_params(min_score, max_stocks)

    try:
        logger.info(f"Starting penny stock screening process (min_score={min_score}, max_stocks={max_stocks})...")

        screened_stocks = []
        stocks_processed = 0
        stocks_skipped = 0
        start_time = time.time()

        potential_stocks = get_potential_penny_stocks()
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

                # --- Apply Risk Filters --- 
                # Filter by Avg Dollar Volume
                avg_dollar_vol = stock_data.get('avg_dollar_volume')
                if avg_dollar_vol is None or avg_dollar_vol < settings.MIN_AVG_DOLLAR_VOLUME:
                     logger.debug(f"Skipping {ticker}: Avg Dollar Volume {avg_dollar_vol} < {settings.MIN_AVG_DOLLAR_VOLUME}")
                     stocks_skipped += 1
                     continue
                
                # Filter by Historical Volatility
                hist_vol = stock_data.get('hist_volatility_60d_annualized')
                if hist_vol is None or hist_vol > settings.MAX_HIST_VOLATILITY_ANNUALIZED:
                     logger.debug(f"Skipping {ticker}: Historical Volatility {hist_vol}% > {settings.MAX_HIST_VOLATILITY_ANNUALIZED}%")
                     stocks_skipped += 1
                     continue
                # --------------------------

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
        ticker = stock_data.get('ticker', 'unknown')

        # Basic validation
        if not stock_data or not isinstance(stock_data, dict):
            logger.debug("Invalid stock data for scoring")
            return 0

        # --- Scoring Criteria --- #
        from ..config.settings import (
            SCORE_WEIGHTS, PRICE_SCORE_THRESHOLDS,
            VOLUME_RATIO_THRESHOLDS, PE_RATIO_THRESHOLD,
            OPTIONS_RATIO_THRESHOLDS
        )

        # Price scoring
        price = stock_data.get("price")
        if price is not None:
            if price < PRICE_SCORE_THRESHOLDS["HIGH"]["threshold"]:
                score += PRICE_SCORE_THRESHOLDS["HIGH"]["points"]
            elif price < PRICE_SCORE_THRESHOLDS["MEDIUM"]["threshold"]:
                score += PRICE_SCORE_THRESHOLDS["MEDIUM"]["points"]
            elif price < PRICE_SCORE_THRESHOLDS["LOW"]["threshold"]:
                score += PRICE_SCORE_THRESHOLDS["LOW"]["points"]
        else:
            logger.debug(f"No price for {ticker} scoring")

        # Volume vs Average Volume scoring
        volume = stock_data.get("volume")
        avg_volume = stock_data.get("avg_volume")
        if volume is not None and avg_volume is not None and avg_volume > 10000:
            try:
                vol_ratio = volume / avg_volume
                if vol_ratio > VOLUME_RATIO_THRESHOLDS["HIGH"]["threshold"]:
                    score += VOLUME_RATIO_THRESHOLDS["HIGH"]["points"]
                elif vol_ratio > VOLUME_RATIO_THRESHOLDS["MEDIUM"]["threshold"]:
                    score += VOLUME_RATIO_THRESHOLDS["MEDIUM"]["points"]
                elif vol_ratio > VOLUME_RATIO_THRESHOLDS["LOW"]["threshold"]:
                    score += VOLUME_RATIO_THRESHOLDS["LOW"]["points"]
            except ZeroDivisionError:
                logger.debug(f"Zero avg volume for {ticker}")
        else:
            logger.debug(f"Insufficient volume data for {ticker} scoring")

        # P/E Ratio scoring
        pe = stock_data.get("pe_ratio")
        if pe is not None and pe > 0:
            if pe < PE_RATIO_THRESHOLD:
                score += SCORE_WEIGHTS["PE_SCORE"]
        else:
            logger.debug(f"No P/E for {ticker} scoring")

        # Options Sentiment scoring
        options_metrics = stock_data.get("options_metrics")
        if options_metrics and not options_metrics.get("error"):
            pc_oi_ratio = options_metrics.get("pc_oi_ratio")
            pc_vol_ratio = options_metrics.get("pc_volume_ratio")
            ratio_to_use = pc_oi_ratio if pc_oi_ratio is not None else pc_vol_ratio

            if ratio_to_use is not None:
                if ratio_to_use < OPTIONS_RATIO_THRESHOLDS["BULLISH"]["threshold"]:
                    score += OPTIONS_RATIO_THRESHOLDS["BULLISH"]["points"]
                elif ratio_to_use < OPTIONS_RATIO_THRESHOLDS["NEUTRAL"]["threshold"]:
                    score += OPTIONS_RATIO_THRESHOLDS["NEUTRAL"]["points"]
                elif ratio_to_use > OPTIONS_RATIO_THRESHOLDS["BEARISH"]["threshold"]:
                    score += OPTIONS_RATIO_THRESHOLDS["BEARISH"]["points"]
                ratio_str = f"{ratio_to_use:.2f}"
                logger.debug(f"Options ratio score: {ticker} Ratio={ratio_str}")
            else:
                logger.debug(f"No usable P/C ratio for {ticker}")
        else:
            logger.debug(f"No options metrics for {ticker}")

        # --- Normalization --- #
        max_possible_score = sum(SCORE_WEIGHTS.values())
        normalized_score = (score / max_possible_score) * 10 if max_possible_score > 0 else 0

        logger.debug(
            f"Score for {ticker}: Raw={score}, Norm={normalized_score:.2f}"
        )

        return round(normalized_score, 2)

    except Exception as e:
        logger.error(
            f"Error calculating score for {stock_data.get('ticker', 'unknown')}: {e}",
            exc_info=True,
        )
        return 0


def validate_screening_params(min_score: float, max_stocks: int) -> None:
    """Validate stock screening parameters."""
    if not isinstance(min_score, (int, float)):
        raise ValueError("min_score must be a number")
    if not isinstance(max_stocks, int):
        raise ValueError("max_stocks must be an integer")
    if min_score < 0 or min_score > 10:
        raise ValueError("min_score must be between 0 and 10")
    if max_stocks < 1:
        raise ValueError("max_stocks must be greater than 0")

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
    logger.info("Starting potential picks analysis...")
    
    # Validate input parameters
    validate_screening_params(min_score, max_stocks)
    
    try:
        # Use the existing screen_penny_stocks function
        screened_stocks = screen_penny_stocks(min_score, max_stocks)
        
        if not screened_stocks:
            logger.warning("No stocks met the screening criteria")
            return []
            
        logger.info(f"Found {len(screened_stocks)} potential picks")
        return screened_stocks
        
    except Exception as e:
        logger.error(f"Error in get_potential_picks: {str(e)}")
        return []

# Helper function to check against a filter dictionary
def _passes_filters(stock_data: Dict[str, Any], filter_config: Dict[str, Dict[str, float]]) -> bool:
    """Checks if stock data passes the given filter configuration."""
    ticker = stock_data.get('ticker', 'Unknown')
    for key, conditions in filter_config.items():
        value = stock_data.get(key)
        
        # Handle special calculated keys first
        if key == "sma_50_200_ratio":
            sma50 = stock_data.get("sma_50")
            sma200 = stock_data.get("sma_200")
            if sma50 is None or sma200 is None or sma200 == 0:
                 logger.debug(f"Skipping {ticker} on filter '{key}': Missing SMA values")
                 return False # Fail if SMAs needed for ratio are missing
            value = sma50 / sma200 # Calculate the value on the fly
        
        # Check general conditions after potential calculation
        if value is None:
            # If a filter requires a value that's missing (and wasn't calculated), it fails
            logger.debug(f"Skipping {ticker} on filter '{key}': Missing value")
            return False

        if "min" in conditions and value < conditions["min"]:
            logger.debug(f"Skipping {ticker} on filter '{key}': {value:.2f} < {conditions['min']}")
            return False
        if "max" in conditions and value > conditions["max"]:
            logger.debug(f"Skipping {ticker} on filter '{key}': {value:.2f} > {conditions['max']}")
            return False

    return True

def screen_normal_stocks(
    max_stocks: int = 20
) -> List[Dict[str, Any]]:
    """
    Screen normal (non-penny) stocks using data from Yahoo Finance.
    Filters based on criteria in settings.DEFAULT_FILTERS_NORMAL and risk settings.
    Returns a list of screened stocks.

    Args:
        max_stocks: Maximum number of stocks to return

    Returns:
        List of stock dictionaries that meet the criteria
    """
    if not isinstance(max_stocks, int) or max_stocks <= 0:
        raise ValueError("max_stocks must be a positive integer")

    try:
        logger.info(f"Starting normal stock screening process (max_stocks={max_stocks})...")

        screened_stocks = []
        stocks_processed_count = 0
        stocks_skipped_count = 0
        start_time = time.time()

        potential_stocks = get_potential_normal_stocks()
        logger.info(f"Found {len(potential_stocks)} potential normal stocks to screen")

        total_potential = len(potential_stocks)

        for ticker in potential_stocks:
            stocks_processed_count += 1
            try:
                stock_data = get_stock_data(ticker)
                if not stock_data or stock_data.get("error"):
                    logger.warning(
                        f"Skipping {ticker}: No data or error "
                        f"({stock_data.get('error')})"
                    )
                    stocks_skipped_count += 1
                    continue

                # --- Apply Risk Filters --- 
                avg_dollar_vol = stock_data.get('avg_dollar_volume')
                if avg_dollar_vol is None or avg_dollar_vol < settings.MIN_AVG_DOLLAR_VOLUME:
                     logger.debug(f"Skipping {ticker}: Avg Dollar Volume {avg_dollar_vol} < {settings.MIN_AVG_DOLLAR_VOLUME}")
                     stocks_skipped_count += 1
                     continue
                
                hist_vol = stock_data.get('hist_volatility_60d_annualized')
                if hist_vol is None or hist_vol > settings.MAX_HIST_VOLATILITY_ANNUALIZED:
                     logger.debug(f"Skipping {ticker}: Historical Volatility {hist_vol}% > {settings.MAX_HIST_VOLATILITY_ANNUALIZED}%")
                     stocks_skipped_count += 1
                     continue
                # --------------------------

                # --- Apply Default Normal Filters --- 
                # Need SMA data for sma_50_200_ratio filter - ensure it's calculated in get_stock_data
                # The _passes_filters function now handles the ratio calculation if SMAs exist.
                if not _passes_filters(stock_data, settings.DEFAULT_FILTERS_NORMAL):
                    # Debug logging can be added inside _passes_filters if needed
                    stocks_skipped_count += 1
                    continue
                # ------------------------------------
                
                # If passed all filters, add to list
                screened_stocks.append(stock_data)
                
                # Stop if we have enough stocks
                if len(screened_stocks) >= max_stocks:
                    logger.info(f"Reached max_stocks ({max_stocks}), stopping screening early.")
                    # Process remaining stocks to update skipped count correctly
                    stocks_skipped_count += (total_potential - stocks_processed_count)
                    break 

                # Log progress periodically
                if stocks_processed_count % 5 == 0:
                    logger.info(
                        f"Processed {stocks_processed_count}/{total_potential} stocks..."
                    )

            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {e}", exc_info=True)
                stocks_skipped_count += 1
        
        # No sorting by score needed here, selection is based on passing filters
        top_stocks = screened_stocks # Already limited by max_stocks check
        logger.info(f"Selected {len(top_stocks)} stocks meeting normal criteria.")

        # --- Fetch Options Metrics ONLY for Selected Stocks --- #
        if top_stocks:
            logger.info(f"Fetching options metrics for {len(top_stocks)} selected stocks...")
            for stock in top_stocks:
                ticker = stock.get("ticker")
                if ticker:
                    try:
                        stock["options_metrics"] = get_options_metrics(ticker)
                        time.sleep(0.3)  # Small delay between requests
                    except Exception as e:
                        logger.error(
                            f"Failed to get options metrics for selected stock {ticker}: {e}"
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
            f"Normal stock screening complete. Found {len(top_stocks)} matching stocks, "
            f"skipped {stocks_skipped_count}. Time: {elapsed_time:.2f}s"
        )

        # Save results with a different filename prefix
        save_json("selected_tickers_normal", top_stocks, logger)

        return top_stocks

    except Exception as e:
        logger.error(f"Error in screen_normal_stocks: {str(e)}")
        return []

# ... existing calculate_stock_score, validate_screening_params, etc. ...

   