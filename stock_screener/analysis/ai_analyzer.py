"""
Module for AI-powered stock analysis using OpenAI GPT.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from openai import OpenAI, OpenAIError
from ..config.settings import RESULTS_DIR, OPENAI_API_KEY

# Configure logging
logger = logging.getLogger(__name__)

# Define the model to use - using the cheaper gpt-4o-mini model
MODEL_NAME = "gpt-4o-mini"

# Initialize OpenAI client
try:
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set")
    
    # Initialize client
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url="https://api.openai.com/v1"
    )
    
    # Test the client with a simple request
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "Test"}],
        max_tokens=5
    )
    logger.info("Successfully tested OpenAI client")
except OpenAIError as e:
    logger.error(f"OpenAI API Error: {str(e)}")
    client = None
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    client = None

# Cache for GPT responses
gpt_cache = {}

def format_stock_data(stock: Dict[str, Any]) -> str:
    """
    Format stock data for GPT analysis.
    
    Args:
        stock: Stock data dictionary
        
    Returns:
        Formatted string with stock data
    """
    try:
        # Get core stock data
        ticker = stock.get('ticker', 'Unknown')
        company_name = stock.get('company_name', 'Unknown Company')
        price = stock.get('price', 'N/A')
        
        # Format the data
        data = [
            f"TICKER: {ticker}",
            f"COMPANY: {company_name}",
            f"PRICE: ${price}",
        ]
        
        # Add other available data
        for key, label in [
            ('sector', 'SECTOR'),
            ('industry', 'INDUSTRY'),
            ('market_cap', 'MARKET CAP'),
            ('volume', 'VOLUME'),
            ('avg_volume', 'AVG VOLUME'),
            ('pe_ratio', 'P/E RATIO'),
            ('eps', 'EPS'),
            ('high_52w', '52-WEEK HIGH'),
            ('low_52w', '52-WEEK LOW'),
            ('beta', 'BETA'),
            ('dividend_yield', 'DIVIDEND YIELD'),
        ]:
            if key in stock and stock[key] is not None:
                value = stock[key]
                
                # Format numbers
                if key == 'market_cap' and isinstance(value, (int, float)) and value > 0:
                    if value >= 1_000_000_000:
                        value = f"${value/1_000_000_000:.2f}B"
                    elif value >= 1_000_000:
                        value = f"${value/1_000_000:.2f}M"
                    else:
                        value = f"${value:,.0f}"
                elif key in ('volume', 'avg_volume') and isinstance(value, (int, float)):
                    value = f"{value:,.0f}"
                elif key in ('pe_ratio', 'eps', 'beta') and isinstance(value, (int, float)):
                    value = f"{value:.2f}"
                elif key == 'dividend_yield' and isinstance(value, (int, float)):
                    value = f"{value:.2f}%"
                
                data.append(f"{label}: {value}")
        
        # Add description if available
        if 'description' in stock and stock['description']:
            data.append(f"\nDESCRIPTION:\n{stock['description']}")
        
        return "\n".join(data)
    
    except Exception as e:
        logger.error(f"Error formatting stock data: {e}")
        return ""

def generate_analysis(stock: Dict[str, Any]) -> str:
    """
    Generate an analysis for a stock using GPT-4o-mini.
    
    Args:
        stock: Stock data dictionary
        
    Returns:
        Generated analysis text
    """
    logger.info(f"Generating analysis for {stock.get('ticker', 'unknown')}")
    
    if client is None:
        logger.error("OpenAI client is not initialized")
        return "Error: OpenAI client is not initialized. Please check your API key."
    
    # Create a cache key
    ticker = stock.get('ticker', 'unknown')
    price = stock.get('price', 0)
    cache_key = f"{ticker}_{price}"
    
    # Check cache
    if cache_key in gpt_cache:
        cached_analysis, timestamp = gpt_cache[cache_key]
        if datetime.now() - timestamp < timedelta(hours=24):
            logger.info(f"Using cached analysis for {ticker}")
            return cached_analysis
    
    try:
        # Format stock data for analysis
        stock_data_str = format_stock_data(stock)
        
        if not stock_data_str:
            return "Error: Could not format stock data for analysis."
        
        # Create a more concise prompt for GPT
        prompt = f"""Analyze this stock based on the provided data:

{stock_data_str}

Provide a CONCISE investment analysis including:
1. Technical Analysis: Key price levels and volume trends (2-3 bullet points)
2. Fundamental Analysis: Current valuation metrics (P/E, EPS, market cap) and growth outlook (2-3 bullet points)
3. Risk Assessment: Major risks to be aware of (2-3 bullet points)
4. Recommendation: Clear buy/hold/sell stance with brief rationale
5. Price Target: Short-term and long-term targets if applicable

Note: Focus on the data available - don't analyze revenue growth or profit margin as these metrics aren't available.

IMPORTANT: Be extremely concise. Use short sentences. Avoid lengthy explanations. The entire analysis should be no more than 400 words.
"""
        
        # Call GPT-4o-mini with increased max_tokens to ensure complete output
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert financial analyst providing extremely concise stock analyses. Focus on key points only. Be direct and brief."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,  # Increased token limit to ensure complete responses
            temperature=0.7  # Slightly reduced from default for more focused responses
        )
        
        analysis = response.choices[0].message.content.strip()
        
        # Cache the result
        gpt_cache[cache_key] = (analysis, datetime.now())
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error generating analysis for {ticker}: {e}")
        return f"Error: Could not generate analysis for {ticker}. {str(e)}"

def analyze_stocks(stocks: List[Dict[str, Any]]) -> None:
    """
    Analyze a list of stocks using OpenAI's GPT.
    
    Args:
        stocks: List of stock data dictionaries
    """
    if not stocks:
        logger.warning("No stocks provided for analysis")
        return
    
    # Test the OpenAI client
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are an expert financial analyst."},
                     {"role": "user", "content": "Test message"}],
            max_tokens=50
        )
        logger.info("Successfully tested OpenAI client")
    except Exception as e:
        logger.error(f"Error testing OpenAI client: {e}")
        return
    
    # Analyze each stock
    stocks_analyzed = []
    
    for i, stock in enumerate(stocks):
        try:
            ticker = stock.get('ticker', 'unknown')
            company_name = stock.get('company_name', '')
            logger.info(f"[{i+1}/{len(stocks)}] Analyzing {ticker}")
            
            # Generate analysis
            analysis = generate_analysis(stock)
            
            # Add analysis to the stock data
            stock['analysis'] = analysis
            stocks_analyzed.append(stock)
            
            # Print analysis for visibility with better formatting
            print(f"\nAnalysis for {ticker}")
            print("=" * 80)
            
            # Print a summary of key metrics before the analysis
            price = stock.get('price', 'N/A')
            market_cap = stock.get('market_cap', 'N/A')
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                if market_cap >= 1_000_000_000:
                    market_cap = f"${market_cap/1_000_000_000:.2f}B"
                elif market_cap >= 1_000_000:
                    market_cap = f"${market_cap/1_000_000:.2f}M"
                else:
                    market_cap = f"${market_cap:,.0f}"
                    
            pe_ratio = stock.get('pe_ratio', 'N/A')
            eps = stock.get('eps', 'N/A')
            
            if company_name:
                ticker_display = f"{ticker} - {company_name}"
            else:
                ticker_display = ticker
                
            print(f"Stock: {ticker_display}")
            print(f"Price: ${price} | Market Cap: {market_cap} | P/E: {pe_ratio} | EPS: {eps}")
            print("-" * 80)
            
            # Print the analysis with proper line breaks
            print(analysis)
            print("=" * 80)
            
        except Exception as e:
            logger.error(f"Error analyzing stock {stock.get('ticker', 'unknown')}: {e}")
            stock['analysis'] = "Analysis error: Could not generate analysis."
    
    # Save analyses to file
    if stocks_analyzed:
        save_analyses_to_file(stocks_analyzed)

def save_analyses_to_file(stocks: List[Dict[str, Any]]) -> None:
    """
    Save stock analyses to a markdown file.
    
    Args:
        stocks: List of stock dictionaries with analyses
    """
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_path = RESULTS_DIR / f'penny_stocks_analysis_{date_str}.md'
    
    try:
        # Make sure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            # Write header
            f.write(f"# Penny Stock Analysis Report - {date_str}\n\n")
            f.write("## Overview\n")
            f.write(f"This report contains analysis for {len(stocks)} penny stocks that match our screening criteria.\n\n")
            
            # Write a summary table
            f.write("## Summary Table\n\n")
            f.write("| Rank | Ticker | Price | Score | Sector | Recommendation |\n")
            f.write("|------|--------|-------|-------|--------|----------------|\n")
            
            for i, stock in enumerate(stocks, 1):
                ticker = stock.get('ticker', 'unknown')
                price = stock.get('price', 'N/A')
                score = stock.get('score', 'N/A')
                sector = stock.get('sector', 'N/A')
                
                # Extract recommendation from analysis if available
                recommendation = "N/A"
                analysis = stock.get('analysis', '')
                if "Recommendation:" in analysis:
                    # Try to extract the recommendation
                    try:
                        rec_text = analysis.split("Recommendation:")[1].split("\n")[0].strip()
                        if rec_text:
                            recommendation = rec_text
                    except:
                        pass
                
                f.write(f"| {i} | {ticker} | ${price} | {score} | {sector} | {recommendation} |\n")
            
            f.write("\n## Detailed Analyses\n\n")
            
            # Write each stock analysis
            for i, stock in enumerate(stocks, 1):
                ticker = stock.get('ticker', 'unknown')
                company_name = stock.get('company_name', '')
                price = stock.get('price', 'N/A')
                score = stock.get('score', 'N/A')
                
                title = f"{ticker}"
                if company_name:
                    title += f" - {company_name}"
                
                f.write(f"### {i}. {title}\n\n")
                f.write(f"**Price**: ${price} | **Score**: {score}\n\n")
                
                # Write analysis in a more readable format
                analysis = stock.get('analysis', 'Analysis not available')
                
                # Don't use code blocks, use markdown instead
                f.write(analysis)
                f.write("\n\n---\n\n")
        
        logger.info(f"Analysis saved to {output_path}")
        return
    except Exception as e:
        logger.error(f"Error saving analyses to file: {e}")
        return 