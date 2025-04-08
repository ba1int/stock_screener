"""
Module for AI-powered stock analysis using Ollama with Llama 3.2 3B.
"""

import logging
import os
import requests
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio  # Add asyncio import
from ..config import settings
from ..config.settings import RESULTS_DIR
from ..communication.telegram_notifier import send_telegram_message, escape_markdown # Import telegram function AND the escaping helper

# Configure logging
logger = logging.getLogger(__name__)

# Ollama API settings
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = os.getenv("LOCAL_LLM", "llama3:latest")


def format_stock_data(stock: Dict[str, Any]) -> str:
    """
    Format stock data for Llama analysis, including enhanced financial and technical metrics.

    Args:
        stock: Stock data dictionary

    Returns:
        Formatted string with stock data
    """
    try:
        # --- Financials & Basic Info ---
        ticker = stock.get("ticker", "N/A")
        company_name = stock.get("company_name", "N/A")
        sector = stock.get("sector", "N/A")
        industry = stock.get("industry", "N/A")
        price = stock.get("price", "N/A")
        market_cap = stock.get("market_cap", "N/A")
        pe_ratio = stock.get("pe_ratio", "N/A")
        eps = stock.get("eps", "N/A")
        dividend_yield = stock.get("dividend_yield", "N/A")
        beta = stock.get("beta", "N/A")
        debt_to_equity = stock.get('debt_to_equity', 'N/A')
        gross_margin_pct = stock.get('gross_margin_pct', 'N/A')
        profit_margin_pct = stock.get('profit_margin_pct', 'N/A')
        cash_runway_years = stock.get('cash_runway_years', 'N/A')
        institutional_ownership_pct = stock.get('institutional_ownership_pct', 'N/A')
        description = stock.get("description", "N/A")

        # --- Volume & Volatility ---
        volume = stock.get("volume", "N/A")
        avg_volume = stock.get("avg_volume", "N/A")
        recent_volume_spike = stock.get('recent_volume_spike', 'N/A')

        # --- Price Action & Levels ---
        high_52w = stock.get("high_52w", "N/A")
        low_52w = stock.get("low_52w", "N/A")
        pct_off_52w_low = stock.get('pct_off_52w_low', 'N/A')
        pct_off_52w_high = stock.get('pct_off_52w_high', 'N/A')
        near_52w_low = stock.get('near_52w_low', 'N/A')
        near_52w_high = stock.get('near_52w_high', 'N/A')
        is_breaking_out_60d = stock.get('is_breaking_out_60d', 'N/A')

        # --- Moving Averages & Momentum ---
        rsi_14 = stock.get('rsi_14', 'N/A')
        macd_line = stock.get('macd_line', 'N/A')
        macd_signal = stock.get('macd_signal', 'N/A')
        macd_hist = stock.get('macd_hist', 'N/A')
        sma_20 = stock.get('sma_20', 'N/A')
        sma_50 = stock.get('sma_50', 'N/A')
        sma_200 = stock.get('sma_200', 'N/A')
        price_above_sma20 = stock.get('price_above_sma20', 'N/A')
        price_above_sma50 = stock.get('price_above_sma50', 'N/A')
        price_above_sma200 = stock.get('price_above_sma200', 'N/A')
        sma50_above_sma200 = stock.get('sma50_above_sma200', 'N/A')
        recent_golden_cross = stock.get('recent_golden_cross', 'N/A')
        recent_death_cross = stock.get('recent_death_cross', 'N/A')

        # --- Sentiment & Insiders ---
        insider_buys_count = stock.get('recent_insider_buys_count', 'N/A')
        insider_net_shares = stock.get('recent_insider_net_shares', 'N/A')
        options_metrics = stock.get("options_metrics")

        # --- Formatting Logic ---
        # Format options metrics if available
        options_metrics_str = "No options data available."
        if options_metrics and not options_metrics.get("error"):
            pc_vol = options_metrics.get("pc_volume_ratio", "N/A")
            pc_oi = options_metrics.get("pc_oi_ratio", "N/A")
            avg_iv_num = options_metrics.get("average_iv")
            avg_iv = f"{avg_iv_num * 100:.1f}%" if isinstance(avg_iv_num, (int, float)) else 'N/A'
            options_metrics_str = (
                f"Put/Call Vol Ratio: {pc_vol}, "
                f"Put/Call OI Ratio: {pc_oi}, "
                f"Avg Near-Term IV: {avg_iv}"
            )

        # Helper function for formatting numbers or returning 'N/A'
        def format_num(val, precision=2, is_pct=False, is_int=False):
            if val is None or val == 'N/A': return 'N/A'
            if not isinstance(val, (int, float)): return str(val) # Return as string if not number
            try:
                if is_int: return f"{val:,.0f}"
                formatted = f"{val:,.{precision}f}"
                return f"{formatted}%" if is_pct else formatted
            except (ValueError, TypeError):
                return str(val) # Fallback

        # Format numbers for readability
        price = format_num(price, 2)
        market_cap_str = "N/A"
        if isinstance(market_cap, (int, float)):
            if market_cap >= 1_000_000_000: market_cap_str = f"${market_cap/1_000_000_000:.2f}B"
            elif market_cap >= 1_000_000: market_cap_str = f"${market_cap/1_000_000:.2f}M"
            else: market_cap_str = f"${market_cap:,.0f}"
        market_cap = market_cap_str # Overwrite with formatted string
        
        volume = format_num(volume, is_int=True)
        avg_volume = format_num(avg_volume, is_int=True)
        pe_ratio = format_num(pe_ratio, 2)
        eps = format_num(eps, 2)
        beta = format_num(beta, 2)
        dividend_yield = format_num(dividend_yield, 2, is_pct=True)
        high_52w = format_num(high_52w, 2)
        low_52w = format_num(low_52w, 2)
        pct_off_52w_low = format_num(pct_off_52w_low, 1, is_pct=True)
        pct_off_52w_high = format_num(pct_off_52w_high, 1, is_pct=True)
        
        debt_to_equity = format_num(debt_to_equity, 2)
        gross_margin_pct = format_num(gross_margin_pct, 1, is_pct=True)
        profit_margin_pct = format_num(profit_margin_pct, 1, is_pct=True)
        if isinstance(cash_runway_years, (int, float)):
            cash_runway_years = "Positive Cash Flow" if cash_runway_years == float('inf') else f"{cash_runway_years:.1f} years"
        insider_net_shares = format_num(insider_net_shares, is_int=True)
        institutional_ownership_pct = format_num(institutional_ownership_pct, 1, is_pct=True)
        
        rsi_14 = format_num(rsi_14, 1)
        macd_line = format_num(macd_line, 4)
        macd_signal = format_num(macd_signal, 4)
        macd_hist = format_num(macd_hist, 4)
        sma_20 = format_num(sma_20, 2)
        sma_50 = format_num(sma_50, 2)
        sma_200 = format_num(sma_200, 2)

        # Construct the formatted string with new TA section
        data_str = f"""
Ticker: {ticker} ({company_name})
Sector: {sector} | Industry: {industry}

Key Financials & Fundamentals:
Price: {price}
Market Cap: {market_cap}
P/E Ratio: {pe_ratio}
EPS: {eps}
Dividend Yield: {dividend_yield}
Beta (Volatility): {beta}
Debt/Equity Ratio: {debt_to_equity}
Gross Margin: {gross_margin_pct}
Profit Margin: {profit_margin_pct}
Cash Runway: {cash_runway_years}
Institutional Ownership: {institutional_ownership_pct}

Technical Indicators & Price Action:
52-Week Range: {low_52w} ({pct_off_52w_low} from Low) - {high_52w} ({pct_off_52w_high} from High)
Price vs SMA(20): {price_above_sma20} | Price vs SMA(50): {price_above_sma50} | Price vs SMA(200): {price_above_sma200}
SMA(50) vs SMA(200): {sma50_above_sma200}
Recent Golden Cross (5d): {recent_golden_cross} | Recent Death Cross (5d): {recent_death_cross}
RSI(14): {rsi_14}
MACD Line: {macd_line} | Signal: {macd_signal} | Hist: {macd_hist}
Near 52w Low: {near_52w_low} | Near 52w High: {near_52w_high}
Breaking Out (60d High): {is_breaking_out_60d}

Volume & Sentiment:
Today's Volume: {volume}
Average Volume: {avg_volume}
Recent Volume Spike (>2.5x Avg): {recent_volume_spike}
Options Sentiment: {options_metrics_str}
Insider Activity (Last 6 Mo): Recent Buys: {insider_buys_count} | Net Shares Purchased: {insider_net_shares}

Company Description:
{description}
"""
        return data_str.strip()

    except Exception as e:
        logger.error(f"Error formatting stock data: {e}")
        return ""


@lru_cache(maxsize=128)
@retry(
    stop=stop_after_attempt(3),  # Default to 3 retries for LLM
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def generate_analysis(stock_data_str: str, ticker: str) -> str:
    """Generate an analysis for a stock using Llama 3.2 3B, with retry logic.

    Args:
        stock_data_str: Formatted string with stock data
        ticker: Stock ticker

    Returns:
        Generated analysis text
    """
    logger.info(f"Generating analysis for {ticker}")

    try:
        # Updated prompt to specifically mention new TA indicators
        prompt = f"""Analyze this stock based on the provided data:

{stock_data_str}

Provide a CONCISE investment analysis including:
1. Technical Analysis: Consider RSI, MACD, MA relationships (Price vs MAs, 50 vs 200, crossovers), volume patterns, and price action relative to 52w levels and recent breakouts. (3-4 bullet points)
2. Fundamental Analysis: Consider valuation (P/E, EPS, market cap), balance sheet health (Debt/Equity, Cash Runway), margins, and growth outlook (2-3 bullet points)
3. Risk Assessment: Major risks including financial health and market factors (2-3 bullet points)
4. Sentiment Check: Incorporate implications from Options Sentiment and Insider Activity.
5. Recommendation: Clear buy/hold/sell stance with brief rationale based on ALL factors.
6. Price Target: Short-term and long-term targets if applicable.

Note: Focus on the data available. Mention if key data points are missing or N/A.

IMPORTANT: Be extremely concise. Use short sentences. Avoid lengthy explanations.
Max 400 words.
"""

        # Call Llama through Ollama API
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "max_tokens": 800},
            },
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.text}")

        analysis = response.json()["response"].strip()
        return analysis

    except Exception as e:
        logger.error(f"Error generating analysis for {ticker}: {e}")
        return f"Error: Could not generate analysis for {ticker}. {str(e)}"


def analyze_stocks(stocks: List[Dict[str, Any]]) -> None:
    """
    Analyze a list of stocks using Llama 3.2 3B.

    Args:
        stocks: List of stock data dictionaries
    """
    if not stocks:
        logger.warning("No stocks provided for analysis")
        return

    # Analyze each stock
    stocks_analyzed = []

    for i, stock in enumerate(stocks):
        try:
            ticker = stock.get("ticker", "unknown")
            company_name = stock.get("company_name", "")
            logger.info(f"[{i+1}/{len(stocks)}] Analyzing {ticker}")

            # Generate analysis
            stock_data_str = format_stock_data(stock)
            if not stock_data_str:
                analysis = "Error: Could not format stock data."
            else:
                analysis = generate_analysis(stock_data_str, ticker)

            # Add analysis to the stock data
            stock["analysis"] = analysis
            stocks_analyzed.append(stock)

            # Print analysis for visibility with better formatting
            print(f"\nAnalysis for {ticker}")
            print("=" * 80)

            # Print a summary of key metrics before the analysis
            price = stock.get("price", "N/A")
            market_cap = stock.get("market_cap", "N/A")
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                if market_cap >= 1_000_000_000:
                    market_cap = f"${market_cap/1_000_000_000:.2f}B"
                elif market_cap >= 1_000_000:
                    market_cap = f"${market_cap/1_000_000:.2f}M"
                else:
                    market_cap = f"${market_cap:,.0f}"

            pe_ratio = stock.get("pe_ratio", "N/A")
            eps = stock.get("eps", "N/A")

            if company_name:
                ticker_display = f"{ticker} - {company_name}"
            else:
                ticker_display = ticker

            print(f"Stock: {ticker_display}")
            print(
                f"Price: ${price} | Market Cap: {market_cap} | "
                f"P/E: {pe_ratio} | EPS: {eps}"
            )
            print("-" * 80)

            # Print the analysis with proper line breaks
            print(analysis)
            print("=" * 80)

        except Exception as e:
            logger.error(f"Error analyzing stock {stock.get('ticker', 'unknown')}: {e}")
            stock["analysis"] = "Analysis error: Could not generate analysis."

    # Save analyses to file
    if stocks_analyzed:
        save_analyses_to_file(stocks_analyzed)


def save_analyses_to_file(stocks: List[Dict[str, Any]]) -> None:
    """
    Save stock analyses to a markdown file and send a summary via Telegram.

    Args:
        stocks: List of analyzed stock data dictionaries
    """
    try:
        # Create results directory if it doesn't exist
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = RESULTS_DIR / f"penny_stocks_analysis_{timestamp}.md"

        markdown_content = "# Penny Stocks Analysis\n\n"
        # Escape timestamp for Telegram summary header
        escaped_timestamp = escape_markdown(timestamp)
        telegram_summary = f"*Penny Stocks Analysis - {escaped_timestamp}*\n\n"
        telegram_summary += f"Found {len(stocks)} stocks matching criteria:\n\n"

        for stock in stocks:
            ticker = stock.get("ticker", "unknown")
            company_name = stock.get("company_name", "")
            analysis = stock.get("analysis", "No analysis available.")
            recommendation = "Recommendation: Not Found"  # Default

            # Improved recommendation extraction
            lines = analysis.split('\n')
            try:
                # Find the index of the line containing "Recommendation", case-insensitive
                idx = next(i for i, line in enumerate(lines) if "recommendation" in line.lower())
                # Find the next non-empty line after the header
                recommendation_line = next((lines[j].strip() for j in range(idx + 1, len(lines)) if lines[j].strip()), None)
                if recommendation_line:
                    # Prepend with 'Recommendation:' for consistency if not already present
                    if not recommendation_line.lower().startswith("recommendation"):
                         recommendation = f"Recommendation: {recommendation_line}"
                    else:
                         recommendation = recommendation_line # Use the line as is if it starts with it
            except StopIteration:
                # Keep the default if "recommendation" line is not found or no line follows
                pass

            ticker_display = f"## {ticker}"
            if company_name:
                ticker_display += f" - {company_name}"

            markdown_content += f"{ticker_display}\n\n{analysis}\n\n---\n\n"

            # Escape ticker and recommendation for Telegram summary
            escaped_ticker = escape_markdown(ticker)
            escaped_recommendation = escape_markdown(recommendation)

            # Add concise info to Telegram summary
            # Note: We keep the '*' for bolding the ticker, but escape the ticker itself
            telegram_summary += f"- *{escaped_ticker}*: {escaped_recommendation}\n"


        # --- Send Telegram Notification ---
        try:
            # We need to run the async function. Use asyncio.run()
            # Ensure message length is within Telegram limits (4096 chars)
            max_len = 4000 # Leave some buffer
            if len(telegram_summary) > max_len:
                telegram_summary = telegram_summary[:max_len] + "... (truncated)"

            logger.info("Sending analysis summary via Telegram...")
            asyncio.run(send_telegram_message(telegram_summary))
            logger.info("Telegram notification sent successfully.")
        except Exception as telegram_err:
            logger.error(f"Failed to send Telegram notification: {telegram_err}")
        # ---------------------------------


        # Write analyses to file
        with open(filename, "w") as f:
            f.write(markdown_content) # Write the full markdown content

        logger.info(f"Analyses saved to {filename}")

    except Exception as e:
        logger.error(f"Error saving analyses to file: {e}")
