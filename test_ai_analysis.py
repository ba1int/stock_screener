"""
Test the AI analysis functionality independently.
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from stock_screener.analysis.ai_analyzer import analyze_stocks, format_stock_data
from stock_screener.data.test_data import SAMPLE_STOCKS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_format_stock_data():
    """Test the format_stock_data function to see how data is prepared for GPT."""
    logger.info("Testing stock data formatting for GPT...")
    
    for stock in SAMPLE_STOCKS[:2]:  # Just test with a couple of stocks
        try:
            formatted_data = format_stock_data(stock)
            logger.info(f"Formatted data for {stock['ticker']}:")
            logger.info(formatted_data)
            logger.info("-" * 50)
        except Exception as e:
            logger.error(f"Error formatting {stock['ticker']}: {e}")

def test_analyze_single_stock():
    """Test the analyze_stocks function with a single stock."""
    logger.info("Testing single stock analysis...")
    
    if len(SAMPLE_STOCKS) > 0:
        # Select just one stock for testing
        test_stock = SAMPLE_STOCKS[0]
        logger.info(f"Analyzing {test_stock['ticker']}...")
        
        # Create a copy of the stock to avoid modifying the original
        test_stock_copy = test_stock.copy()
        
        try:
            analyze_stocks([test_stock_copy])
            
            # Check if analysis was added
            if 'analysis' in test_stock_copy:
                logger.info(f"Analysis result for {test_stock_copy['ticker']}:")
                logger.info(test_stock_copy['analysis'])
            else:
                logger.warning(f"No analysis was generated for {test_stock_copy['ticker']}")
        
        except Exception as e:
            logger.error(f"Error analyzing {test_stock['ticker']}: {e}")
    else:
        logger.warning("No sample stocks available for testing")

def test_analyze_multiple_stocks():
    """Test the analyze_stocks function with multiple stocks."""
    logger.info("Testing multiple stock analysis (limited to 2 stocks)...")
    
    # Select just 2 stocks for testing to save API costs
    test_stocks = SAMPLE_STOCKS[:2].copy()
    
    try:
        # Create copies to avoid modifying the originals
        test_stocks_copy = [stock.copy() for stock in test_stocks]
        
        analyze_stocks(test_stocks_copy)
        
        # Save results to a file
        results_dir = Path('test_results')
        results_dir.mkdir(exist_ok=True)
        
        date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        result_file = results_dir / f'ai_analysis_test_{date_str}.json'
        
        # Save the results
        with open(result_file, 'w') as f:
            # Keep only what we need to avoid errors with non-serializable objects
            simplified_results = []
            for stock in test_stocks_copy:
                simplified_stock = {
                    'ticker': stock['ticker'],
                    'price': stock['price'],
                    'company_name': stock.get('company_name', 'Unknown'),
                }
                if 'analysis' in stock:
                    simplified_stock['analysis'] = stock['analysis']
                simplified_results.append(simplified_stock)
                
            json.dump(simplified_results, f, indent=2)
            
        logger.info(f"Results saved to {result_file}")
        
    except Exception as e:
        logger.error(f"Error analyzing stocks: {e}")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--format-only":
        # Just test the formatting without making API calls
        test_format_stock_data()
    elif len(sys.argv) > 1 and sys.argv[1] == "--single":
        # Test with just a single stock
        test_analyze_single_stock()
    else:
        # Test with multiple stocks
        test_analyze_multiple_stocks()
    
    sys.exit(0) 