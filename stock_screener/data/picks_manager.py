"""
Module for managing and storing stock picks.
"""

import os
import json
from datetime import datetime
from ..utils.helpers import setup_logging

logger = setup_logging()

PICKS_DIR = "stock_picks"

def ensure_picks_directory():
    """Ensure the picks directory exists."""
    if not os.path.exists(PICKS_DIR):
        os.makedirs(PICKS_DIR)
        logger.info(f"Created directory for storing picks: {PICKS_DIR}")

def save_picks(stocks, date_str=None):
    """Save stock picks for a specific date."""
    ensure_picks_directory()
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    file_path = os.path.join(PICKS_DIR, f"{date_str}.json")
    
    # Convert stocks to serializable format
    serializable_stocks = []
    for stock in stocks:
        serializable_stock = stock.copy()
        # Convert any non-serializable values to strings
        for key, value in serializable_stock.items():
            if not isinstance(value, (str, int, float, bool, type(None))):
                serializable_stock[key] = str(value)
        serializable_stocks.append(serializable_stock)
    
    try:
        with open(file_path, 'w') as f:
            json.dump({
                'date': date_str,
                'stocks': serializable_stocks
            }, f, indent=2)
        logger.info(f"Saved {len(stocks)} picks to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save picks: {e}")
        return False

def load_picks(date_str=None):
    """Load stock picks for a specific date."""
    ensure_picks_directory()
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    file_path = os.path.join(PICKS_DIR, f"{date_str}.json")
    
    if not os.path.exists(file_path):
        logger.warning(f"No picks found for date {date_str}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data['stocks'])} picks from {file_path}")
        return data['stocks']
    except Exception as e:
        logger.error(f"Failed to load picks: {e}")
        return None

def list_available_dates():
    """List all dates for which we have stored picks."""
    ensure_picks_directory()
    
    dates = []
    for filename in os.listdir(PICKS_DIR):
        if filename.endswith('.json'):
            date_str = filename[:-5]  # Remove .json extension
            dates.append(date_str)
    
    return sorted(dates, reverse=True)  # Most recent first 