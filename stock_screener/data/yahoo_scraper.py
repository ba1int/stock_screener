"""
Module for retrieving stock data from Yahoo Finance.
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import time
import logging
import random
from ..utils.helpers import setup_logging, convert_to_float

logger = setup_logging()

def get_penny_stocks() -> List[str]:
    """
    Get list of potential penny stocks using Yahoo Finance.
    Returns a list of ticker symbols.
    """
    logger.info("Fetching penny stocks from Yahoo Finance...")
    
    try:
        # Use a list of common penny stock tickers
        penny_stock_sectors = [
            # Technology penny stocks
            "SIRI", "NOK", "ZNGA", "BBRY", "GRPN", "SYMC", "SPWR", "GPRO", "FIT", "SONO",
            # Healthcare penny stocks
            "ACRX", "SRNE", "CTIC", "ONTX", "ATHX", "TTNP", "VBIV", "MNKD", "NVAX", "PGNX",
            # Energy penny stocks
            "UEC", "PEIX", "FCEL", "UUUU", "PLUG", "CPE", "ENSV", "TRCH", "HTGM", "SHIP",
            # Retail penny stocks
            "EXPR", "BGFV", "PRTS", "GME", "AMC", "BBBY", "SPCE", "DKNG", "CLOV", "WISH",
            # Mining penny stocks
            "BTG", "NAK", "GPL", "EGO", "SAND", "ASM", "AUY", "NGD", "HL", "SILV",
            # Biotech penny stocks
            "OCGN", "INO", "BCRX", "IBRX", "ADMP", "BNGO", "ATOS", "YMTX", "AVEO", "AMRN"
        ]
        
        # Add a random selection of tickers from different sectors
        nasdaq_list = ["AACG", "AAME", "AAOI", "AAON", "AAPL", "AATC", "AAWW", "ABCB", "ABEO", "ABIO", 
                      "ABTX", "ACAD", "ACAM", "ACAS", "ACER", "ACET", "ACGL", "ACHC", "ACHV", "ACIU", 
                      "ACIW", "ACLS", "ACMR", "ACNB", "ACOR", "ACRS", "ACRX", "ACST", "ACTG", "ACWI"]
        
        potential_tickers = penny_stock_sectors + random.sample(nasdaq_list, 20)
        
        logger.info(f"Screening {len(potential_tickers)} potential penny stocks...")
        
        # Filter for actual penny stocks (price < $5)
        penny_stocks = []
        
        for i, ticker in enumerate(potential_tickers):
            try:
                # Add delay every 5 requests to avoid rate limiting
                if i > 0 and i % 5 == 0:
                    logger.info(f"Processed {i}/{len(potential_tickers)} tickers...")
                    time.sleep(0.75)
                
                # Get basic stock info
                stock = yf.Ticker(ticker)
                
                # Safety check for info attribute
                if not hasattr(stock, 'info'):
                    logger.debug(f"Ticker {ticker} has no info attribute")
                    continue
                
                # Safety check for None info
                if stock.info is None:
                    logger.debug(f"Ticker {ticker} info is None")
                    continue
                
                # Get current price 
                current_price = None
                
                # Try getting price from info
                if 'regularMarketPrice' in stock.info:
                    current_price = stock.info['regularMarketPrice']
                # If not available, try from history
                else:
                    try:
                        hist = stock.history(period="1d")
                        if not hist.empty:
                            current_price = hist['Close'].iloc[-1]
                    except Exception as e:
                        logger.debug(f"Error getting history for {ticker}: {str(e)}")
                
                if current_price is not None and current_price < 5:
                    penny_stocks.append(ticker)
                    logger.debug(f"Added penny stock: {ticker} (${current_price:.2f})")
            
            except Exception as e:
                logger.debug(f"Error processing {ticker}: {str(e)}")
        
        logger.info(f"Found {len(penny_stocks)} penny stocks")
        return penny_stocks
        
    except Exception as e:
        logger.error(f"Error in get_penny_stocks: {str(e)}")
        return []

def get_stock_news(ticker: str) -> str:
    """
    Get news for a stock ticker from Yahoo Finance.
    Returns a formatted string with news headlines and URLs.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Check if stock has news attribute
        if not hasattr(stock, 'news'):
            logger.debug(f"Ticker {ticker} has no news attribute")
            return "No recent news found."
        
        # Check if news is None
        if stock.news is None:
            logger.debug(f"Ticker {ticker} news is None")
            return "No recent news found."
        
        # Check if news is empty
        if not stock.news:
            return "No recent news found."
        
        # Format the news
        news_text = ""
        for i, item in enumerate(stock.news[:5]):  # Limit to 5 news items
            try:
                title = item.get('title', 'No title')
                link = item.get('link', '#')
                publisher = item.get('publisher', 'Unknown')
                publish_time = item.get('providerPublishTime', 0)
                
                # Convert timestamp to readable date
                from datetime import datetime
                date_str = datetime.fromtimestamp(publish_time).strftime('%Y-%m-%d')
                
                news_text += f"- [{title}]({link}) - {publisher} ({date_str})\n"
            except Exception as e:
                logger.debug(f"Error formatting news item for {ticker}: {str(e)}")
        
        return news_text if news_text else "Error processing news."
    except Exception as e:
        logger.error(f"Error getting news for {ticker}: {str(e)}")
        return "Error fetching news."

def get_stock_details(ticker):
    """Get detailed stock information from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        
        # Check if stock has info attribute
        if not hasattr(stock, 'info'):
            logger.warning(f"Ticker {ticker} has no info attribute")
            return None
        
        # Check if info is None
        if stock.info is None:
            logger.warning(f"Ticker {ticker} info is None")
            return None
        
        return stock.info
    except Exception as e:
        logger.error(f"Error fetching stock details for {ticker}: {str(e)}")
        return None

def calculate_stock_score(stock_data):
    """Calculate a comprehensive score for a stock based on multiple criteria."""
    try:
        score = 0
        
        # Basic validation
        if not stock_data or not isinstance(stock_data, dict):
            return 0
        
        # Price (under $5 for penny stocks)
        price = stock_data.get('price')
        if price is not None:
            if price < 1:
                score += 15
            elif price < 3:
                score += 10
            elif price < 5:
                score += 5
        
        # Volume and liquidity
        volume = stock_data.get('volume')
        avg_volume = stock_data.get('avg_volume')
        if volume is not None and avg_volume is not None and avg_volume > 0:
            vol_ratio = volume / avg_volume
            if vol_ratio > 2:
                score += 15
            elif vol_ratio > 1.5:
                score += 10
            elif vol_ratio > 1:
                score += 5
        
        # Value metrics
        pe = stock_data.get('pe')
        if pe is not None and pe > 0:
            if pe < 10:
                score += 15
            elif pe < 15:
                score += 10
        
        pb = stock_data.get('pb')
        if pb is not None and pb > 0:
            if pb < 1:
                score += 15
            elif pb < 2:
                score += 10
        
        # Growth metrics
        eps_growth = stock_data.get('eps_growth')
        if eps_growth is not None and eps_growth > 0:
            if eps_growth > 0.3:
                score += 15
            elif eps_growth > 0.1:
                score += 10
        
        revenue_growth = stock_data.get('revenue_growth')
        if revenue_growth is not None and revenue_growth > 0:
            if revenue_growth > 0.3:
                score += 15
            elif revenue_growth > 0.1:
                score += 10
        
        # Analyst sentiment
        recommendation = stock_data.get('recommendation')
        if recommendation in ['buy', 'strongBuy']:
            score += 10
        
        return score
    
    except Exception as e:
        logger.error(f"Error calculating score: {str(e)}")
        return 0 