"""
Test the file saving functionality independently.
"""

import logging
import sys
import json
from pathlib import Path
from stock_screener.utils.helpers import save_news_data, save_selected_tickers, save_investment_summary
from stock_screener.data.test_data import SAMPLE_STOCKS, SAMPLE_NEWS_DATA, SAMPLE_ANALYSIS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_save_news_data():
    """Test saving news data to a file."""
    logger.info("Testing save_news_data function...")
    
    try:
        file_path = save_news_data(SAMPLE_NEWS_DATA)
        if file_path:
            logger.info(f"News data successfully saved to {file_path}")
            
            # Verify the file was created and contains valid data
            with open(file_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded data has {len(data)} items")
        else:
            logger.error("Failed to save news data")
    except Exception as e:
        logger.error(f"Error in save_news_data: {e}")

def test_save_selected_tickers():
    """Test saving selected tickers to a file."""
    logger.info("Testing save_selected_tickers function...")
    
    # Prepare ticker data in the format expected by the function
    ticker_data = []
    for stock in SAMPLE_STOCKS:
        ticker_data.append({
            'ticker': stock['ticker'],
            'price': stock['price'],
            'volume': stock.get('volume', 'N/A'),
            'market_cap': stock.get('market_cap', 'N/A'),
            'industry': stock.get('industry', 'N/A'),
            'eps': stock.get('eps', 'N/A'),
            'pe_ratio': stock.get('pe_ratio', 'N/A'),
            'score': 8.5  # Test value
        })
    
    try:
        file_path = save_selected_tickers(ticker_data)
        if file_path:
            logger.info(f"Selected tickers successfully saved to {file_path}")
            
            # Verify the file was created and contains valid data
            with open(file_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded data has {len(data)} items")
        else:
            logger.error("Failed to save selected tickers")
    except Exception as e:
        logger.error(f"Error in save_selected_tickers: {e}")

def test_save_investment_summary():
    """Test saving investment summary to a markdown file."""
    logger.info("Testing save_investment_summary function...")
    
    # Prepare stock data with analysis
    top_stocks = []
    for stock in SAMPLE_STOCKS[:3]:  # Just use first 3 stocks
        stock_copy = stock.copy()
        ticker = stock_copy['ticker']
        if ticker in SAMPLE_ANALYSIS:
            stock_copy['analysis'] = SAMPLE_ANALYSIS[ticker]
        top_stocks.append(stock_copy)
    
    try:
        file_path = save_investment_summary(top_stocks, SAMPLE_NEWS_DATA)
        if file_path:
            logger.info(f"Investment summary successfully saved to {file_path}")
            
            # Verify the file was created
            if Path(file_path).exists():
                logger.info(f"File {file_path} exists and has size {Path(file_path).stat().st_size} bytes")
            else:
                logger.error(f"File {file_path} was not created")
        else:
            logger.error("Failed to save investment summary")
    except Exception as e:
        logger.error(f"Error in save_investment_summary: {e}")

def test_all_saving_functions():
    """Test all saving functions."""
    logger.info("Testing all file saving functions...")
    
    logger.info("=" * 50)
    test_save_news_data()
    
    logger.info("=" * 50)
    test_save_selected_tickers()
    
    logger.info("=" * 50)
    test_save_investment_summary()
    
    logger.info("=" * 50)
    logger.info("All file saving tests completed")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--news":
            test_save_news_data()
        elif sys.argv[1] == "--tickers":
            test_save_selected_tickers()
        elif sys.argv[1] == "--summary":
            test_save_investment_summary()
        else:
            logger.error(f"Unknown argument: {sys.argv[1]}")
    else:
        # Test all functions
        test_all_saving_functions()
    
    sys.exit(0) 