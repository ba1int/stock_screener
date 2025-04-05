"""
Main entry point for the penny stock screener.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from .config.settings import RESULTS_DIR
from .data.stock_screener import screen_penny_stocks
from .analysis.ai_analyzer import analyze_stocks
from .utils.helpers import setup_logging, save_news_data, save_selected_tickers, save_investment_summary

# Set up logging
logger = logging.getLogger(__name__)

def main():
    """Main function to run the stock screener."""
    logger.info("Starting penny stock screener...")
    
    try:
        # Screen penny stocks using Yahoo Finance
        stocks, news_data = screen_penny_stocks()
        
        # Check if stocks is None or empty
        if not stocks:
            logger.info("No stocks matched your filters.")
            return
        
        # Ensure news_data is not None
        if news_data is None:
            news_data = {}
        
        # Save news data
        save_news_data(news_data)
        
        # Convert stock data to a serializable format
        serializable_stocks = []
        for stock in stocks:
            # Create a new dict with only the serializable data
            serializable_stock = {}
            for key, value in stock.items():
                # Skip complex objects that might not be JSON serializable
                if key not in ('info', 'options', 'dividends', 'splits'):
                    try:
                        # Test if the value is JSON serializable
                        json.dumps({key: value})
                        serializable_stock[key] = value
                    except (TypeError, OverflowError):
                        # Convert non-serializable values to strings
                        serializable_stock[key] = str(value)
            
            serializable_stocks.append(serializable_stock)
        
        # Save selected tickers
        save_selected_tickers([{
            'ticker': stock.get('ticker', 'UNKNOWN'),
            'price': stock.get('price', 'N/A'),
            'volume': stock.get('volume', 'N/A'),
            'market_cap': stock.get('market_cap', 'N/A'),
            'industry': stock.get('industry', 'N/A'),
            'eps': stock.get('eps', 'N/A'),
            'pe_ratio': stock.get('pe_ratio', 'N/A'),
            'score': stock.get('score', 'N/A')
        } for stock in serializable_stocks])
        
        # Sort stocks by score and get top 10
        top_stocks = sorted(serializable_stocks, key=lambda x: x.get('score', 0), reverse=True)[:10]
        
        # Generate detailed analysis for top stocks
        logger.info("Generating detailed analysis for top 10 stocks...")
        analyze_stocks(top_stocks)
        
        # Create investment summary
        save_investment_summary(top_stocks, news_data)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 