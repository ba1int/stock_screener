"""
Simple Yahoo Finance integration for stock screening.
"""

import yfinance as yf
import logging
import time
from functools import lru_cache
from typing import List, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from requests.exceptions import RequestException
from ..config import settings
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import numpy as np
import stock_screener.config.settings as settings # Ensure settings is imported

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Expanded list of potential penny stock tickers across various sectors
PENNY_STOCKS_LIST = list(
    set(
        [
            # Technology
            "SIRI",
            "NOK",
            "GPRO",
            "BB",
            "SSYS",
            "IQ",
            "RAD",
            "PLTR",
            "SOFI",
            "CLSK",
            # Healthcare
            "ACRX",
            "SRNE",
            "NVAX",
            "MNKD",
            "PGNX",
            "CTXR",
            "SESN",
            "ATOS",
            "SNDL",
            "VXRT",
            # Energy
            "FCEL",
            "PLUG",
            "UUUU",
            "CPE",
            "SHIP",
            "BORR",
            "TELL",
            "WWR",
            "RIG",
            "NOG",
            # Retail
            "EXPR",
            "GME",
            "AMC",
            "BBBY",
            "WISH",
            "KOSS",
            "NAKD",
            "SFIX",
            "POSH",
            "REAL",
            # Mining
            "BTG",
            "NAK",
            "GPL",
            "EGO",
            "HL",
            "SVM",
            "MUX",
            "AG",
            "PAAS",
            "MAG",
            # Biotech
            "OCGN",
            "INO",
            "BCRX",
            "BNGO",
            "AMRN",
            "TTOO",
            "CODX",
            "ADMA",
            "IBIO",
            "OGEN",
            # Finance
            "FAMI",
            "METX",
            "BK",
            "IVR",
            "TWO",
            "XSPA",
            "CLOV",
            "UWMC",
            "GSAT",
            "MNMD",
            # Other
            "IDEX",
            "MARA",
            "RIOT",
            "SOS",
            "ZOM",
            "GEVO",
            "SENS",
            "TRCH",
            "CIDM",
            "MVIS",
        ]
    )
)  # Use set to remove duplicates

# Example list of 'normal' stocks (non-penny)
NORMAL_STOCKS_LIST = list(
    set([
        # Large Cap Tech
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
        # Large Cap Finance
        "JPM", "BAC", "WFC", "GS", "MS",
        # Large Cap Healthcare
        "JNJ", "PFE", "UNH", "MRK", "LLY",
        # Large Cap Consumer Goods
        "PG", "KO", "PEP", "COST", "WMT",
        # Large Cap Industrials
        "HON", "BA", "CAT", "GE",
        # Large Cap Energy
        "XOM", "CVX",
        # Popular ETFs
        "SPY", "QQQ", "VOO", "VTI", "ARKK",
        # Other popular stocks
        "DIS", "NFLX", "PYPL", "SQ", "AMD"
    ])
)


def get_potential_penny_stocks() -> List[str]: # Renamed from get_penny_stocks
    """Get a list of potential penny stocks based on a predefined list and price < $5."""
    logger.info("Starting potential penny stock identification")
    potential_stocks = []

    # Use our expanded predefined list
    for i, ticker in enumerate(PENNY_STOCKS_LIST):
        try:
            # Add delay every 3 requests
            if i > 0 and i % 3 == 0:
                time.sleep(0.5)

            # Get stock info
            logger.info(f"Checking {ticker} for penny stock potential...")
            stock = yf.Ticker(ticker)

            try:
                # Try to get the current price
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
                    # Use PRICE_MAX from settings
                    if 0 < price < settings.PRICE_MAX:
                        potential_stocks.append(ticker)
                        logger.info(f"Identified potential penny stock: {ticker} (${price:.2f})")
            except Exception as e:
                # Don't log error if it's a known delisted symbol pattern
                if "No data found, symbol may be delisted" not in str(e):
                     logger.warning(f"Error getting history for {ticker}: {e}")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")

    logger.info(f"Found {len(potential_stocks)} potential penny stocks")
    return potential_stocks


def get_potential_normal_stocks() -> List[str]:
    """Get a list of potential normal stocks based on a predefined list and price >= NORMAL_STOCK_PRICE_MIN."""
    logger.info("Starting potential normal stock identification")
    potential_stocks = []

    # Use our normal stock list
    for i, ticker in enumerate(NORMAL_STOCKS_LIST):
        try:
            # Add delay every 3 requests
            if i > 0 and i % 3 == 0:
                time.sleep(0.5)

            # Get stock info
            logger.info(f"Checking {ticker} for normal stock potential...")
            stock = yf.Ticker(ticker)

            try:
                # Try to get the current price
                hist = stock.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
                    # Use NORMAL_STOCK_PRICE_MIN from settings
                    if price >= settings.NORMAL_STOCK_PRICE_MIN:
                        potential_stocks.append(ticker)
                        logger.info(f"Identified potential normal stock: {ticker} (${price:.2f})")
            except Exception as e:
                if "No data found, symbol may be delisted" not in str(e):
                     logger.warning(f"Error getting history for {ticker}: {e}")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")

    logger.info(f"Found {len(potential_stocks)} potential normal stocks")
    return potential_stocks


@lru_cache(maxsize=256)
@retry(
    stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=settings.YAHOO_TIMEOUT // 2),
    retry=retry_if_exception_type(RequestException),
)
def get_stock_data(ticker: str) -> Dict[str, Any]:
    """Get detailed data for a stock, including enhanced metrics."""
    logger.info(f"Getting data for {ticker}")
    stock_data = {"ticker": ticker} # Initialize
    try:
        stock = yf.Ticker(ticker)

        # 1. Get basic info (ensure Beta is always present, even if None)
        info = {}
        try:
            info = stock.info
            stock_data.update({
                "company_name": info.get("shortName", "Unknown"),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap", None),
                "pe_ratio": info.get("trailingPE", None),
                "eps": info.get("trailingEps", None),
                "dividend_yield": info.get("dividendYield", None),
                "beta": info.get("beta", None), # Explicitly add beta, even if None
                "description": info.get("longBusinessSummary", None),
                "institutional_ownership_pct": info.get("heldPercentInstitutions", None) * 100 if info.get("heldPercentInstitutions") else None,
                "profit_margin_pct": info.get("profitMargins", None) * 100 if info.get("profitMargins") else None,
            })
        except Exception as e:
            logger.warning(f"Could not get info for {ticker}: {e}")
            # Ensure beta is still added if info fetch fails but Ticker object exists
            if 'beta' not in stock_data:
                 stock_data['beta'] = None

        # 2. Get recent price data and calculate TA & Risk Metrics
        price_data = {}
        hist = None # Initialize hist
        try:
            hist = stock.history(period="1y") # Fetches daily data for 1 year
            if not hist.empty:
                # Basic price data
                price_data = {
                    "price": hist["Close"].iloc[-1],
                    "volume": hist["Volume"].iloc[-1],
                    "high_52w": hist["High"].max(),
                    "low_52w": hist["Low"].min(),
                    "avg_volume": hist["Volume"].mean(),
                }
                stock_data.update(price_data)

                # Calculate Avg Dollar Volume
                if price_data.get('avg_volume') and price_data.get('price'):
                    avg_price_period = hist['Close'].mean()
                    stock_data['avg_dollar_volume'] = price_data['avg_volume'] * avg_price_period
                else:
                    stock_data['avg_dollar_volume'] = None

                # Calculate technical indicators using pandas_ta
                if len(hist) > 200: # Need enough data
                    ta_indicators = {} # Initialize dict for TA results
                    try: 
                         # --- Core TA Calculations --- 
                         hist.ta.sma(length=20, append=True)
                         hist.ta.sma(length=50, append=True)
                         hist.ta.sma(length=200, append=True)
                         hist.ta.rsi(length=14, append=True)
                         hist.ta.macd(fast=12, slow=26, signal=9, append=True)
                         hist.ta.atr(length=settings.ATR_PERIOD, append=True)
                         
                         # --- Extract Core TA Values Immediately --- 
                         latest_ta = hist.iloc[-1]
                         ta_indicators['sma_20'] = latest_ta.get('SMA_20')
                         ta_indicators['sma_50'] = latest_ta.get('SMA_50')
                         ta_indicators['sma_200'] = latest_ta.get('SMA_200')
                         ta_indicators['rsi_14'] = latest_ta.get('RSI_14')
                         ta_indicators['macd_line'] = latest_ta.get('MACD_12_26_9')
                         ta_indicators['macd_signal'] = latest_ta.get('MACDs_12_26_9')
                         ta_indicators['macd_hist'] = latest_ta.get('MACDh_12_26_9')
                         ta_indicators['atr_14'] = latest_ta.get(f'ATRr_{settings.ATR_PERIOD}')

                         # --- Calculate Historical Volatility --- 
                         hist['log_return'] = np.log(hist['Close'] / hist['Close'].shift(1))
                         hist['volatility_60d'] = hist['log_return'].rolling(window=60).std() * np.sqrt(252)
                         ta_indicators['hist_volatility_60d_annualized'] = hist['volatility_60d'].iloc[-1] * 100 if 'volatility_60d' in hist.columns else None

                         # --- Analyze TA Relationships & Other Metrics (using extracted values) --- 
                         current_price = latest_ta['Close']
                         sma20 = ta_indicators.get('sma_20')
                         sma50 = ta_indicators.get('sma_50')
                         sma200 = ta_indicators.get('sma_200')
                         
                         ta_indicators['price_above_sma20'] = current_price > sma20 if sma20 is not None else None
                         ta_indicators['price_above_sma50'] = current_price > sma50 if sma50 is not None else None
                         ta_indicators['price_above_sma200'] = current_price > sma200 if sma200 is not None else None
                         ta_indicators['sma50_above_sma200'] = sma50 > sma200 if sma50 is not None and sma200 is not None else None
                         
                         # Recent Crossovers
                         recent_hist = hist.iloc[-5:]
                         if 'SMA_50' in recent_hist.columns and 'SMA_200' in recent_hist.columns:
                             ta_indicators['recent_golden_cross'] = ((recent_hist['SMA_50'] > recent_hist['SMA_200']) & (recent_hist['SMA_50'].shift(1) < recent_hist['SMA_200'].shift(1))).any()
                             ta_indicators['recent_death_cross'] = ((recent_hist['SMA_50'] < recent_hist['SMA_200']) & (recent_hist['SMA_50'].shift(1) > recent_hist['SMA_200'].shift(1))).any()
                         else:
                             ta_indicators['recent_golden_cross'] = False
                             ta_indicators['recent_death_cross'] = False

                         # Support/Resistance/Breakout
                         low_52w = stock_data.get('low_52w')
                         high_52w = stock_data.get('high_52w')
                         ta_indicators['pct_off_52w_low'] = ((current_price / low_52w) - 1) * 100 if low_52w and low_52w != 0 else None
                         ta_indicators['pct_off_52w_high'] = (1 - (current_price / high_52w)) * 100 if high_52w and high_52w != 0 else None
                         ta_indicators['near_52w_low'] = ta_indicators['pct_off_52w_low'] is not None and ta_indicators['pct_off_52w_low'] <= 10
                         ta_indicators['near_52w_high'] = ta_indicators['pct_off_52w_high'] is not None and ta_indicators['pct_off_52w_high'] <= 10
                         
                         recent_high_60d = hist['High'].iloc[-60:].max()
                         ta_indicators['is_breaking_out_60d'] = current_price > recent_high_60d if not pd.isna(recent_high_60d) else None
                         
                         # Volume Spike
                         avg_vol = stock_data.get('avg_volume')
                         current_vol = stock_data.get('volume')
                         ta_indicators['recent_volume_spike'] = current_vol > (avg_vol * 2.5) if current_vol and avg_vol and avg_vol != 0 else None
                         
                         # ATR Stop Loss
                         atr = ta_indicators.get('atr_14')
                         if atr is not None and current_price is not None:
                             stop_distance = atr * settings.ATR_STOP_MULTIPLIER
                             ta_indicators['atr_stop_distance'] = stop_distance
                             ta_indicators['suggested_stop_price'] = current_price - stop_distance
                         else:
                             ta_indicators['atr_stop_distance'] = None
                             ta_indicators['suggested_stop_price'] = None
                             
                         stock_data.update(ta_indicators) # Update main dict with ALL TA results
                         
                    except Exception as ta_err:
                         logger.warning(f"Error calculating TA/Risk metrics for {ticker}: {ta_err}", exc_info=True)
                         # Ensure core keys exist even if calculation failed mid-way
                         for core_key in ['sma_20', 'sma_50', 'sma_200', 'rsi_14']:
                              if core_key not in stock_data: stock_data[core_key] = None

                else:
                     logger.warning(f"Not enough history data (need >200, got {len(hist)}) to calculate TA/Risk metrics for {ticker}")
                     # Ensure core keys exist if history was too short
                     for core_key in ['sma_20', 'sma_50', 'sma_200', 'rsi_14', 'hist_volatility_60d_annualized', 'atr_14']:
                         stock_data[core_key] = None
            else:
                 logger.warning(f"Empty history data for {ticker}")
                 # Ensure core keys exist if history was empty
                 for core_key in ['sma_20', 'sma_50', 'sma_200', 'rsi_14', 'hist_volatility_60d_annualized', 'atr_14', 'avg_dollar_volume']:
                     stock_data[core_key] = None
                 
        except Exception as e:
            logger.warning(f"Could not get price data or calculate TA/Risk for {ticker}: {e}", exc_info=True)
            # Ensure core keys exist if price history fetch failed
            for core_key in ['sma_20', 'sma_50', 'sma_200', 'rsi_14', 'hist_volatility_60d_annualized', 'atr_14', 'avg_dollar_volume']:
                 if core_key not in stock_data: stock_data[core_key] = None

        # --- Ensure Beta is present if info fetch failed earlier --- 
        if 'beta' not in stock_data:
            stock_data['beta'] = None 
            
        # --- 3. ENHANCED FINANCIAL METRICS (Keep as is) --- 
        financials_data = {}
        balance_sheet_data = {}
        cashflow_data = {}
        insider_tx_summary = {}

        # Fetch Financials (Income Statement - TTM)
        try:
            # Using .financials often gives TTM automatically
            financials = stock.financials 
            if not financials.empty:
                latest_financials = financials.iloc[:, 0] # Assuming latest TTM is first column
                revenue = latest_financials.get('Total Revenue')
                gross_profit = latest_financials.get('Gross Profit')
                net_income = latest_financials.get('Net Income') # Check exact name if error
                
                # Calculate Gross Margin if not already found in info
                if revenue and gross_profit is not None:
                    financials_data['gross_margin_pct'] = (gross_profit / revenue) * 100 if revenue != 0 else 0
                
                # Calculate Profit Margin if not found in info
                if stock_data.get('profit_margin_pct') is None and revenue and net_income is not None:
                     financials_data['profit_margin_pct'] = (net_income / revenue) * 100 if revenue != 0 else 0
                
                stock_data.update(financials_data)

        except Exception as e:
            logger.warning(f"Could not get financials for {ticker}: {e}")

        # Fetch Balance Sheet (Most Recent Quarter)
        try:
            balance_sheet = stock.balance_sheet
            if not balance_sheet.empty:
                latest_bs = balance_sheet.iloc[:, 0]
                # Find Total Debt (can be under different names)
                total_debt = latest_bs.get('Total Debt')
                if total_debt is None:
                     total_debt = latest_bs.get('Total Liab') # Fallback, less accurate
                
                total_equity = latest_bs.get('Stockholders Equity') # Or 'Total Stockholder Equity'
                balance_sheet_data['cash'] = latest_bs.get('Cash And Cash Equivalents') # Or similar name
                
                # Calculate Debt-to-Equity
                if total_equity and total_equity != 0 and total_debt is not None:
                    balance_sheet_data['debt_to_equity'] = total_debt / total_equity
                else:
                     balance_sheet_data['debt_to_equity'] = None
                
                stock_data.update(balance_sheet_data)
        except Exception as e:
            logger.warning(f"Could not get balance sheet for {ticker}: {e}")

        # Fetch Cash Flow (TTM) & Calculate Runway
        try:
            cashflow = stock.cashflow
            if not cashflow.empty and 'Free Cash Flow' in cashflow.index:
                # Sum last 4 quarters for TTM (assuming quarterly data in columns)
                # Or just use the first column if .cashflow provides TTM directly
                ttm_fcf = cashflow.loc['Free Cash Flow'].iloc[:, 0] if not cashflow.loc['Free Cash Flow'].iloc[:, 0:4].empty else None # Safer: check shape
                #ttm_fcf = cashflow.loc['Free Cash Flow'].sum() # If columns are quarters

                burn_rate_annual = None
                if ttm_fcf is not None and ttm_fcf < 0:
                    burn_rate_annual = abs(ttm_fcf)

                current_cash = stock_data.get('cash') # Get from previously fetched BS data
                if burn_rate_annual and current_cash:
                     cashflow_data['cash_runway_years'] = current_cash / burn_rate_annual
                elif current_cash is not None and ttm_fcf is not None and ttm_fcf >= 0:
                     cashflow_data['cash_runway_years'] = float('inf') # Positive cash flow
                else:
                     cashflow_data['cash_runway_years'] = None
                stock_data.update(cashflow_data)
            else:
                 logger.debug(f"No Free Cash Flow data found for {ticker} in cashflow statement.")
                 stock_data['cash_runway_years'] = None

        except Exception as e:
            logger.warning(f"Could not get cash flow or calculate runway for {ticker}: {e}")
            stock_data['cash_runway_years'] = None

        # Fetch Insider Transactions (Recent Buys)
        try:
            insider_tx = stock.insiderTransactions
            if insider_tx is not None and not insider_tx.empty:
                six_months_ago = pd.Timestamp.now() - pd.DateOffset(months=6)
                 # Ensure 'Start Date' is datetime
                insider_tx['Start Date'] = pd.to_datetime(insider_tx['Start Date'])
                
                # Check if 'Shares' column exists before filtering
                if 'Shares' in insider_tx.columns:
                    recent_purchases = insider_tx[
                        (insider_tx['Start Date'] >= six_months_ago) & 
                        (insider_tx['Shares'] > 0)
                    ]
                    insider_tx_summary['recent_insider_buys_count'] = len(recent_purchases)
                    insider_tx_summary['recent_insider_net_shares'] = recent_purchases['Shares'].sum()
                else:
                    logger.debug(f"'Shares' column not found in insider transactions for {ticker}")
                    insider_tx_summary['recent_insider_buys_count'] = 0
                    insider_tx_summary['recent_insider_net_shares'] = 0
            else:
                 insider_tx_summary['recent_insider_buys_count'] = 0
                 insider_tx_summary['recent_insider_net_shares'] = 0
            stock_data.update(insider_tx_summary)
        except Exception as e:
            logger.warning(f"Could not get insider transactions for {ticker}: {e}")
            stock_data['recent_insider_buys_count'] = None
            stock_data['recent_insider_net_shares'] = None

        # Fetch Institutional Ownership (If not found in info)
        if stock_data.get('institutional_ownership_pct') is None:
            try:
                inst_holders = stock.institutionalHolders
                if inst_holders is not None and not inst_holders.empty and '% Out' in inst_holders.columns:
                    # Attempt to sum the '% Out' column, converting errors to NaN
                    ownership_pct = pd.to_numeric(inst_holders['% Out'], errors='coerce').sum()
                    if pd.notna(ownership_pct):
                        stock_data['institutional_ownership_pct'] = ownership_pct * 100
            except Exception as e:
                logger.warning(f"Could not get institutional ownership details for {ticker}: {e}")

        # --- END NEW METRICS --- 

        # Final check for essential data like price
        if stock_data.get("price") is None:
             logger.warning(f"No valid current price found for {ticker}. Skipping score calculation potentially.")
             # Optionally return an error dict or None if price is critical
             # return {"error": f"No valid price for {ticker}"} 

        # Final check: replace any NaN values potentially introduced
        for key, value in stock_data.items():
             if isinstance(value, float) and np.isnan(value):
                  stock_data[key] = None
                  
    except Exception as e:
        logger.error(f"Major error getting data for {ticker}: {e}", exc_info=True)
        stock_data["error"] = str(e)

    return stock_data


@lru_cache(maxsize=128)
@retry(
    stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(RequestException),
)
def get_stock_news(ticker: str) -> str:
    """Get news for a stock, include date, with retry logic."""
    logger.info(f"Getting news for {ticker}")
    try:
        stock = yf.Ticker(ticker)

        # Get news
        news = []
        try:
            raw_news = stock.news
            if raw_news:
                news = raw_news
        except Exception as e:
            logger.warning(f"Could not get news for {ticker} via yfinance: {e}")
            # Optionally add a fallback news source here if needed

        if not news:
            logger.warning(f"No news found for {ticker}")
            return "No recent news found."

        news_text = ""
        for i, item in enumerate(news[:5]):  # Top 5 news items
            try:
                title = item.get("title", "No title")
                link = item.get("link", "#")
                publisher = item.get("publisher", "Unknown")
                publish_time = item.get("providerPublishTime")

                date_str = ""
                if publish_time:
                    try:
                        # Convert timestamp to readable date
                        date_str = datetime.fromtimestamp(publish_time).strftime(
                            "%Y-%m-%d"
                        )
                    except Exception as date_e:
                        logger.debug(
                            f"Could not parse news timestamp {publish_time}: {date_e}"
                        )
                        date_str = "(Date unknown)"
                else:
                    date_str = "(Date unknown)"

                news_text += f"- [{title}]({link}) - {publisher} {date_str}\n"
            except Exception as item_e:
                logger.debug(f"Error formatting news item for {ticker}: {item_e}")

        return news_text if news_text else "Error processing news."

    except RequestException as e:
        logger.error(f"Network error getting news for {ticker}: {e}")
        raise e  # Reraise for retry
    except Exception as e:
        logger.error(f"Unexpected error getting news for {ticker}: {e}")
        return "Error fetching news."


# --- Options Data --- #


@lru_cache(maxsize=256)
@retry(
    stop=stop_after_attempt(settings.YAHOO_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=settings.YAHOO_TIMEOUT // 2),
    retry=retry_if_exception_type(RequestException),
)
def get_options_metrics(ticker: str) -> Dict[str, Any]:
    """Fetch options chain data and calculate key metrics.

    Calculates Put/Call ratios (Volume & Open Interest) and a
    weighted average Implied Volatility for a near-term expiration.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A dictionary containing options metrics, or an error dict.
    """
    logger.info(f"Getting options metrics for {ticker}")
    try:
        stock = yf.Ticker(ticker)

        # 1. Get Expiration Dates
        try:
            expiries = stock.options
            if not expiries:
                logger.warning(f"No options expiration dates found for {ticker}")
                return {"error": "No options data available"}
        except Exception as e:
            logger.warning(f"Could not retrieve options expirations for {ticker}: {e}")
            return {"error": "Failed to retrieve options expirations"}

        # 2. Select Target Expiration (approx 30-60 days out)
        today = datetime.today().date()
        target_expiry = None
        min_days = 30
        max_days = 60

        valid_expiries = []
        for expiry_str in expiries:
            try:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                days_to_expiry = (expiry_date - today).days
                if min_days <= days_to_expiry <= max_days:
                    valid_expiries.append((days_to_expiry, expiry_str))
            except ValueError:
                logger.debug(f"Could not parse expiry date: {expiry_str} for {ticker}")
                continue

        if not valid_expiries:
            # Fallback: try nearest expiry if none in 30-60 day range
            logger.debug(
                f"No expiry found in {
                    min_days}-{max_days} days for {ticker}. Trying nearest."
            )
            for expiry_str in expiries:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    days_to_expiry = (expiry_date - today).days
                    if days_to_expiry > 0:  # Ensure it's in the future
                        valid_expiries.append((days_to_expiry, expiry_str))
                except ValueError:
                    continue
            if not valid_expiries:
                logger.warning(f"No valid future expiration dates found for {ticker}")
                return {"error": "No suitable options expiration dates found"}

        # Select the expiry closest to our target range (or just the nearest future)
        valid_expiries.sort()  # Sort by days_to_expiry
        target_expiry = valid_expiries[0][1]  # [1] gets the date string
        logger.info(f"Selected expiry {target_expiry} for {ticker}")

        # 3. Fetch Option Chain for selected expiry
        try:
            opt_chain = stock.option_chain(target_expiry)
            calls = opt_chain.calls
            puts = opt_chain.puts
        except Exception as e:
            logger.warning(
                f"Could not retrieve option chain for {
                    ticker} expiry {target_expiry}: {e}"
            )
            return {"error": f"Failed to retrieve option chain for {target_expiry}"}

        if calls.empty and puts.empty:
            logger.warning(f"Option chain empty for {ticker} expiry {target_expiry}")
            return {"error": "Option chain is empty"}

        # 4. Calculate Put/Call Ratios
        total_call_volume = calls["volume"].sum() if "volume" in calls.columns else 0
        total_put_volume = puts["volume"].sum() if "volume" in puts.columns else 0
        total_call_oi = (
            calls["openInterest"].sum() if "openInterest" in calls.columns else 0
        )
        total_put_oi = (
            puts["openInterest"].sum() if "openInterest" in puts.columns else 0
        )

        pc_volume_ratio = (
            total_put_volume / total_call_volume if total_call_volume > 0 else None
        )
        pc_oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else None

        # 5. Calculate Weighted Average IV
        # Combine calls and puts, filter out zero OI or IV
        all_options = pd.concat([calls, puts])
        valid_iv_options = all_options[
            (all_options["openInterest"] > 0) & (all_options["impliedVolatility"] > 0)
        ].copy()

        weighted_iv = None
        if not valid_iv_options.empty:
            valid_iv_options["iv_x_oi"] = (
                valid_iv_options["impliedVolatility"] * valid_iv_options["openInterest"]
            )
            total_oi_for_iv = valid_iv_options["openInterest"].sum()
            if total_oi_for_iv > 0:
                weighted_iv = valid_iv_options["iv_x_oi"].sum() / total_oi_for_iv

        # 6. Return results
        metrics = {
            "selected_expiry": target_expiry,
            "pc_volume_ratio": (
                round(pc_volume_ratio, 3) if pc_volume_ratio is not None else None
            ),
            "pc_oi_ratio": round(pc_oi_ratio, 3) if pc_oi_ratio is not None else None,
            "average_iv": round(weighted_iv, 4) if weighted_iv is not None else None,
            "total_volume": int(total_call_volume + total_put_volume),  # Cast to int
            "total_open_interest": int(total_call_oi + total_put_oi),  # Cast to int
        }
        logger.debug(f"Options metrics for {ticker}: {metrics}")
        return metrics

    except RequestException as e:
        logger.error(f"Network error fetching options data for {ticker}: {e}")
        raise e  # Reraise to trigger retry
    except Exception as e:
        logger.error(
            f"Unexpected error fetching options data for {ticker}: {e}", exc_info=True
        )
        return {"error": f"Unexpected error fetching options data for {ticker}"}
