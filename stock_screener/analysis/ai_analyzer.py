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
    Format stock data for Llama analysis, including enhanced metrics.

    Args:
        stock: Stock data dictionary

    Returns:
        Formatted string with stock data
    """
    try:
        # Extract key data points, handle None gracefully
        ticker = stock.get("ticker", "N/A")
        company_name = stock.get("company_name", "N/A")
        sector = stock.get("sector", "N/A")
        industry = stock.get("industry", "N/A")
        price = stock.get("price", "N/A")
        market_cap = stock.get("market_cap", "N/A")
        volume = stock.get("volume", "N/A")
        avg_volume = stock.get("avg_volume", "N/A")
        pe_ratio = stock.get("pe_ratio", "N/A")
        eps = stock.get("eps", "N/A")
        beta = stock.get("beta", "N/A")
        high_52w = stock.get("high_52w", "N/A")
        low_52w = stock.get("low_52w", "N/A")
        dividend_yield = stock.get("dividend_yield", "N/A")
        description = stock.get("description", "N/A")

        # --- New Metrics ---
        debt_to_equity = stock.get('debt_to_equity', 'N/A')
        gross_margin_pct = stock.get('gross_margin_pct', 'N/A')
        profit_margin_pct = stock.get('profit_margin_pct', 'N/A')
        cash_runway_years = stock.get('cash_runway_years', 'N/A')
        insider_buys_count = stock.get('recent_insider_buys_count', 'N/A')
        insider_net_shares = stock.get('recent_insider_net_shares', 'N/A')
        institutional_ownership_pct = stock.get('institutional_ownership_pct', 'N/A')
        # --- End New Metrics ---

        # Format options metrics if available
        options_metrics_str = "No options data available."
        options_metrics = stock.get("options_metrics")
        if options_metrics and not options_metrics.get("error"):
            pc_vol = options_metrics.get("pc_volume_ratio", "N/A")
            pc_oi = options_metrics.get("pc_oi_ratio", "N/A")
            avg_iv = options_metrics.get("average_iv", "N/A")
            if avg_iv != "N/A": # Check if avg_iv is not 'N/A' before formatting
                 avg_iv_num = options_metrics.get("average_iv") # Get raw number for comparison
                 if isinstance(avg_iv_num, (int, float)): 
                     avg_iv = f"{avg_iv_num * 100:.1f}%"  # Format IV as percentage
                 else:
                     avg_iv = 'N/A' # Handle case where it might be None or other type
            
            options_metrics_str = (
                f"Put/Call Vol Ratio: {pc_vol}, "
                f"Put/Call OI Ratio: {pc_oi}, "
                f"Avg Near-Term IV: {avg_iv}"
            )

        # Format numbers for readability
        if isinstance(market_cap, (int, float)):
            if market_cap >= 1_000_000_000:
                market_cap = f"${market_cap/1_000_000_000:.2f}B"
            elif market_cap >= 1_000_000:
                market_cap = f"${market_cap/1_000_000:.2f}M"
            else:
                market_cap = f"${market_cap:,.0f}"
        if isinstance(volume, (int, float)):
            volume = f"{volume:,.0f}"
        if isinstance(avg_volume, (int, float)):
            avg_volume = f"{avg_volume:,.0f}"
        if isinstance(pe_ratio, (int, float)):
            pe_ratio = f"{pe_ratio:.2f}"
        if isinstance(eps, (int, float)):
            eps = f"{eps:.2f}"
        if isinstance(beta, (int, float)):
            beta = f"{beta:.2f}"
        if isinstance(dividend_yield, (int, float)):
            dividend_yield = f"{dividend_yield:.2f}%"
        # --- Format New Metrics ---
        if isinstance(debt_to_equity, (int, float)):
             debt_to_equity = f"{debt_to_equity:.2f}"
        if isinstance(gross_margin_pct, (int, float)):
            gross_margin_pct = f"{gross_margin_pct:.1f}%"
        if isinstance(profit_margin_pct, (int, float)):
            profit_margin_pct = f"{profit_margin_pct:.1f}%"
        if isinstance(cash_runway_years, (int, float)):
            if cash_runway_years == float('inf'):
                cash_runway_years = "Positive Cash Flow"
            else:
                cash_runway_years = f"{cash_runway_years:.1f} years"
        if isinstance(insider_net_shares, (int, float)):
            insider_net_shares = f"{insider_net_shares:,.0f}"
        if isinstance(institutional_ownership_pct, (int, float)):
            institutional_ownership_pct = f"{institutional_ownership_pct:.1f}%"
        # --- End Format New Metrics ---

        # Construct the formatted string with new sections
        data_str = f"""
Ticker: {ticker} ({company_name})
Sector: {sector} | Industry: {industry}

Key Financials:
Price: {price}
Market Cap: {market_cap}
P/E Ratio: {pe_ratio}
EPS: {eps}
Dividend Yield: {dividend_yield}
Beta (Volatility): {beta}
52-Week Range: {low_52w} - {high_52w}

Balance Sheet & Margins:
Debt/Equity Ratio: {debt_to_equity}
Gross Margin: {gross_margin_pct}
Profit Margin: {profit_margin_pct}
Cash Runway: {cash_runway_years}
Institutional Ownership: {institutional_ownership_pct}

Volume:
Today's Volume: {volume}
Average Volume: {avg_volume}

Options Sentiment:
{options_metrics_str}

Insider Activity (Last 6 Mo):
Recent Buys Count: {insider_buys_count}
Net Shares Purchased: {insider_net_shares}

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
        # Updated prompt to mention new metrics
        prompt = f"""Analyze this stock based on the provided data:

{stock_data_str}

Provide a CONCISE investment analysis including:
1. Technical Analysis: Key price levels and volume trends (2-3 bullet points)
2. Fundamental Analysis: Consider valuation (P/E, EPS, market cap), balance sheet health (Debt/Equity, Cash Runway), margins, and growth outlook (2-3 bullet points)
3. Risk Assessment: Major risks including financial health and market factors (2-3 bullet points)
4. Sentiment Check: Incorporate implications from Options Sentiment and Insider Activity.
5. Recommendation: Clear buy/hold/sell stance with brief rationale.
6. Price Target: Short-term and long-term targets if applicable.

Note: Focus on the data available. Mention if key data points (like runway or margins) are missing or N/A.

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
