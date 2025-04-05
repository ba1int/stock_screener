"""
Module for screening stocks based on financial metrics.
"""

import logging
import time
from typing import List, Dict, Any, Tuple
from ..utils.helpers import setup_logging
from .simple_yahoo import get_penny_stocks, get_stock_data
from .newsapi_fetcher import get_stock_news

# Set up logging directly instead of using the helper
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def screen_penny_stocks() -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Screen penny stocks using data from Yahoo Finance.
    Returns a tuple of (screened_stocks, news_data).
    """
    try:
        logger.info("Starting penny stock screening process...")
        
        # Get penny stock tickers
        tickers = get_penny_stocks()
        
        if not tickers:
            logger.warning("No penny stocks found to screen")
            return [], {}
        
        logger.info(f"Found {len(tickers)} potential penny stocks to screen")
        
        # Process each stock
        screened_stocks = []
        news_data = {}
        stocks_processed = 0
        stocks_skipped = 0
        
        for i, ticker in enumerate(tickers):
            try:
                # Log progress
                if i > 0 and i % 5 == 0:
                    logger.info(f"Processed {i}/{len(tickers)} stocks...")
                
                # Add delay between requests to avoid rate limiting
                time.sleep(0.75)
                
                # Get stock data 
                stock_data = get_stock_data(ticker)
                
                if 'error' in stock_data:
                    logger.warning(f"Error with {ticker}: {stock_data['error']}")
                    stocks_skipped += 1
                    continue
                
                # Skip if missing critical data
                if not stock_data.get('price') or not stock_data.get('volume'):
                    logger.warning(f"Missing critical data for {ticker}")
                    stocks_skipped += 1
                    continue
                
                # Calculate score based on financial metrics
                score = calculate_stock_score(stock_data)
                if score > 0:
                    stock_data['score'] = score
                    screened_stocks.append(stock_data)
                    stocks_processed += 1
                    
                    # Get news for this ticker
                    news_data[ticker] = get_stock_news(ticker)
                else:
                    stocks_skipped += 1
                
            except Exception as e:
                logger.error(f"Error processing stock {ticker}: {str(e)}")
                stocks_skipped += 1
        
        # Sort stocks by score (descending)
        screened_stocks = sorted(screened_stocks, key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Screening complete. Found {stocks_processed} matching stocks, skipped {stocks_skipped}")
        
        return screened_stocks, news_data
        
    except Exception as e:
        logger.error(f"Error in screen_penny_stocks: {str(e)}")
        return [], {}

def calculate_stock_score(stock_data: Dict[str, Any]) -> float:
    """
    Calculate a score for a stock based on financial metrics.
    Higher score means more attractive investment.
    """
    try:
        score = 0.0
        
        # Skip stocks with invalid data
        price = stock_data.get('price')
        if not price or price <= 0:
            return 0
        
        volume = stock_data.get('volume')
        if not volume or volume < 50000:  # Minimum volume threshold
            return 0
        
        # Base score - all penny stocks start with this
        score += 1
        
        # Price points (favor stocks closer to $1, avoid extremely cheap stocks)
        if 0.5 <= price < 1:
            score += 1
        elif 1 <= price < 3:
            score += 2
        elif 3 <= price < 5:
            score += 1
        elif price < 0.1:
            score -= 2  # Penalty for extremely cheap stocks
        
        # Volume points (higher volume = higher liquidity)
        avg_volume = stock_data.get('avg_volume', 0)
        if avg_volume > 1000000:
            score += 3
        elif avg_volume > 500000:
            score += 2
        elif avg_volume > 100000:
            score += 1
        
        # Value metrics
        pe_ratio = stock_data.get('pe_ratio')
        if pe_ratio and 5 < pe_ratio < 15:  # Reasonably valued
            score += 2
        
        # Growth potential (based on price relative to 52-week range)
        high_52w = stock_data.get('high_52w')
        low_52w = stock_data.get('low_52w')
        if high_52w and low_52w and high_52w > low_52w:
            # Calculate where current price is in the 52-week range (0 to 1)
            range_position = (price - low_52w) / (high_52w - low_52w)
            
            # Favor stocks in lower half of 52-week range (more upside potential)
            if range_position < 0.3:
                score += 3  # Near 52-week low, potential value
            elif range_position < 0.5:
                score += 2  # Below middle of range
        
        # Sector/Industry bonus
        sector = stock_data.get('sector', '').lower()
        industry = stock_data.get('industry', '').lower()
        
        # Favor growth sectors
        growth_sectors = ['technology', 'healthcare', 'consumer cyclical', 'biotech']
        if any(s in sector for s in growth_sectors) or any(s in industry for s in growth_sectors):
            score += 1
        
        return max(0, score)  # Ensure score isn't negative
    
    except Exception as e:
        logger.error(f"Error calculating score: {str(e)}")
        return 0