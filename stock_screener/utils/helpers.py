"""
Utility functions for the stock screener.
"""

import logging
import pandas as pd
import numpy as np
import json
from typing import Any, List, Dict
from pathlib import Path
from datetime import datetime
from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_logging():
    """Set up and return a logger."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def convert_to_float(value):
    """Convert a value to float, handling various formats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    # Remove any non-numeric characters except decimal points and negative signs
    value = value.replace(",", "")
    value = "".join(c for c in value if c.isdigit() or c in ".-")

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that can handle numpy types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super().default(obj)


def save_json(filename_prefix: str, data: Any, logger: logging.Logger) -> None:
    """Save data to a JSON file in the results directory.

    Args:
        filename_prefix: Prefix for the filename (e.g., 'selected_tickers').
        data: The data to save (should be JSON serializable).
        logger: Logger instance.
    """
    timestamp_str = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{filename_prefix}_{timestamp_str}.json"
    output_path = settings.RESULTS_DIR / output_filename

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Data saved to {output_path}")
    except TypeError as e:
        logger.error(f"Error: Data is not JSON serializable for {output_filename}. {e}")
        # Optionally, try to save a string representation or log problematic data
    except Exception as e:
        logger.error(f"Error saving data to {output_path}: {e}")


def save_selected_tickers(tickers_data):
    """Save selected tickers and their basic data to a JSON file."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    tickers_file = (
        Path("stock_screener/data/results") / f"selected_tickers_{date_str}.json"
    )

    try:
        # Ensure the directory exists
        tickers_file.parent.mkdir(parents=True, exist_ok=True)

        # Save tickers data
        with open(tickers_file, "w") as f:
            json.dump(tickers_data, f, indent=2)
        logger.info(f"Selected tickers saved to {tickers_file}")
        return str(tickers_file)
    except Exception as e:
        logger.error(f"Error saving tickers data: {str(e)}")
        return None


def save_investment_summary(top_stocks: List[Dict[str, Any]]) -> None:
    """Create a markdown summary of top investment candidates.

    Args:
        top_stocks: List of stock dictionaries including score and analysis.
                    News should be under the 'news_summary' key if available.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    summary_file = (
        Path("stock_screener/data/results") / f"investment_summary_{date_str}.md"
    )

    try:
        # Ensure the directory exists
        summary_file.parent.mkdir(parents=True, exist_ok=True)

        with open(summary_file, "w") as f:
            # Write header
            f.write(f"# Investment Opportunities Summary - {date_str}\n\n")

            # Write overview
            f.write("## Overview\n")
            f.write(
                f"Analysis of top {len(top_stocks)} investment candidates based on our screening criteria.\n\n"
            )

            # Write each stock's summary
            for stock in top_stocks:
                f.write(
                    f"## {stock['ticker']} (Score: {stock.get('score', 'N/A')})\n\n"
                )

                # Basic info
                f.write("### Company Information\n")
                f.write(f"- **Price:** ${stock.get('price', 'N/A')}\n")

                # Handle different formats for market cap
                market_cap = stock.get("market_cap", "N/A")
                if isinstance(market_cap, (int, float)) and market_cap > 0:
                    if market_cap >= 1_000_000_000:
                        formatted_market_cap = f"${market_cap/1_000_000_000:.2f}B"
                    elif market_cap >= 1_000_000:
                        formatted_market_cap = f"${market_cap/1_000_000:.2f}M"
                    else:
                        formatted_market_cap = f"${market_cap:,.0f}"
                else:
                    formatted_market_cap = (
                        f"${market_cap}"
                        if isinstance(market_cap, (int, float))
                        else f"{market_cap}"
                    )

                f.write(f"- **Market Cap:** {formatted_market_cap}\n")
                f.write(f"- **Industry:** {stock.get('industry', 'N/A')}\n")

                # Add PE Ratio and EPS if available
                pe_ratio = stock.get("pe_ratio", "N/A")
                if pe_ratio != "N/A" and pe_ratio is not None:
                    f.write(f"- **P/E Ratio:** {pe_ratio}\n")

                eps = stock.get("eps", "N/A")
                if eps != "N/A" and eps is not None:
                    f.write(f"- **EPS:** {eps}\n")

                # Add Beta if available
                beta = stock.get("beta", "N/A")
                if beta != "N/A" and beta is not None:
                    f.write(f"- **Beta:** {beta}\n")

                f.write("\n")

                # Recent news
                f.write("### Recent News\n")
                news_summary = stock.get("news_summary", "No recent news found.")
                f.write(news_summary + "\n")
                f.write("\n")

                # Analysis
                f.write("### Analysis\n")
                if "analysis" in stock:
                    f.write("```\n")
                    f.write(stock["analysis"])
                    f.write("\n```\n")
                else:
                    f.write("No analysis available.\n")
                f.write("\n---\n\n")

        logger.info(f"Investment summary saved to {summary_file}")
    except Exception as e:
        logger.error(f"Error saving investment summary: {str(e)}")
