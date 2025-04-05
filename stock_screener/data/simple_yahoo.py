"""
Simple Yahoo Finance integration for stock screening.
"""

import yfinance as yf
import logging
import time
import random
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of penny stock tickers to check
PENNY_STOCKS = [
    # Technology
    "SIRI", "NOK", "GPRO", "BB", "SSYS", 
    # Healthcare
    "ACRX", "SRNE", "NVAX", "MNKD", "PGNX",
    # Energy
    "FCEL", "PLUG", "UUUU", "CPE", "SHIP",
    # Retail
    "EXPR", "GME", "AMC", "BBBY", "WISH",
    # Mining
    "BTG", "NAK", "GPL", "EGO", "HL",
    # Biotech
    "OCGN", "INO", "BCRX", "BNGO", "AMRN"
]

def get_penny_stocks() -> List[str]:
    """Get a list of penny stocks."""
    logger.info("Starting penny stock screening")
    penny_stocks = []
    
    # Use our predefined list
    for i, ticker in enumerate(PENNY_STOCKS):
        try:
            # Add delay every 3 requests
            if i > 0 and i % 3 == 0:
                time.sleep(0.5)
                
            # Get stock info
            logger.info(f"Checking {ticker}...")
            stock = yf.Ticker(ticker)
            
            try:
                # Try to get the current price
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    if price < 5:
                        penny_stocks.append(ticker)
                        logger.info(f"Added penny stock: {ticker} (${price:.2f})")
            except Exception as e:
                logger.warning(f"Error getting history for {ticker}: {e}")
                
        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
    
    logger.info(f"Found {len(penny_stocks)} penny stocks")
    return penny_stocks

def get_stock_data(ticker: str) -> Dict[str, Any]:
    """Get detailed data for a stock."""
    logger.info(f"Getting data for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        
        # Get basic info
        info = {}
        try:
            info = stock.info
        except Exception as e:
            logger.warning(f"Could not get info for {ticker}: {e}")
        
        # Get recent price data
        price_data = {}
        try:
            hist = stock.history(period="1y")
            if not hist.empty:
                price_data = {
                    'current_price': hist['Close'].iloc[-1],
                    'volume': hist['Volume'].iloc[-1],
                    'high_52w': hist['High'].max(),
                    'low_52w': hist['Low'].min(),
                    'avg_volume': hist['Volume'].mean()
                }
        except Exception as e:
            logger.warning(f"Could not get price data for {ticker}: {e}")
        
        # Combine data
        stock_data = {
            'ticker': ticker,
            'price': price_data.get('current_price', None),
            'volume': price_data.get('volume', None),
            'avg_volume': price_data.get('avg_volume', None),
            'high_52w': price_data.get('high_52w', None),
            'low_52w': price_data.get('low_52w', None),
            'company_name': info.get('shortName', 'Unknown'),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', None),
            'pe_ratio': info.get('trailingPE', None),
            'eps': info.get('trailingEps', None),
            'dividend_yield': info.get('dividendYield', None),
            'beta': info.get('beta', None),
            'description': info.get('longBusinessSummary', None)
        }
        
        return stock_data
    except Exception as e:
        logger.error(f"Error getting data for {ticker}: {e}")
        return {'ticker': ticker, 'error': str(e)}

def get_stock_news(ticker: str) -> str:
    """Get news for a stock."""
    logger.info(f"Getting news for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        
        # Get news
        try:
            news = stock.news
            if news:
                # Format news
                news_text = ""
                for i, item in enumerate(news[:5]):  # Top 5 news items
                    title = item.get('title', 'No title')
                    link = item.get('link', '#')
                    publisher = item.get('publisher', 'Unknown')
                    
                    news_text += f"- [{title}]({link}) - {publisher}\n"
                
                return news_text
        except Exception as e:
            logger.warning(f"Could not get news for {ticker}: {e}")
        
        return "No recent news found."
    except Exception as e:
        logger.error(f"Error getting news for {ticker}: {e}")
        return "Error fetching news." 