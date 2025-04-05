# Stock Screener Testing Guide

This document provides information on how to test specific components of the stock screener without running the entire application.

## Test Files Overview

The following test files are available to test individual components:

| File                 | Purpose                                           | API Calls? |
|----------------------|---------------------------------------------------|------------|
| `test_stock_scoring.py` | Test the stock scoring algorithm               | No         |
| `test_ai_analysis.py`   | Test the AI analysis component                 | Yes (GPT)  |
| `test_news_fetching.py` | Test retrieving news for stocks                | Yes (Yahoo) |
| `test_file_saving.py`   | Test saving data to files                      | No         |
| `run_specific_component.py` | Run specific components individually       | Varies     |

## Sample Data

Sample data for testing is available in `stock_screener/data/test_data.py`:
- `SAMPLE_STOCKS`: A list of sample stock data for testing
- `SAMPLE_NEWS_DATA`: Sample news data for stocks
- `SAMPLE_ANALYSIS`: Sample analysis content for testing

## News API Integration

The stock screener now uses NewsAPI.org instead of Yahoo Finance for fetching news articles. This provides more reliable and higher quality news data with proper formatting.

### Requirements

- A NewsAPI.org API key (should be added to your `.env` file as `NEWS_API_KEY`)
- The `newsapi-python` package (install with `pip install newsapi-python`)

### Configuration

The following settings have been added to control the news fetching behavior:

```python
# In stock_screener/config/settings.py
NEWS_CACHE_DURATION = 1800  # Cache news data for 30 minutes
MAX_NEWS_ARTICLES = 5      # Maximum number of news articles per stock
NEWS_LOOKBACK_DAYS = 7     # Look back this many days for news
```

### Testing the News API

You can test the NewsAPI integration using the test script:

```bash
# Test with a single stock
python test_news_fetching.py --single

# Test with multiple stocks
python test_news_fetching.py

# Test with sample data (no API calls)
python test_news_fetching.py --sample
```

## AI Analysis Improvements

The AI analysis component has been updated to provide more concise and better-formatted stock analyses:

### Key Features

1. **Concise Format**: Analysis is now structured with clear bullet points and sections, preventing truncation issues
2. **Complete Analysis**: Token limit has been increased to ensure analyses are never cut off mid-sentence
3. **Better Visualization**: Both terminal output and markdown files now present data in a more readable format
4. **Summary Table**: A summary table with key metrics is now included in the analysis report

### Example Output

The analysis now follows this structure:

```
Technical Analysis:
- Key price level information
- Volume trends
- Price action observations

Fundamental Analysis:
- Valuation assessment
- Growth outlook
- Market position

Risk Assessment:
- Volatility factors
- Company-specific risks
- Market/sector risks

Recommendation:
- Clear buy/hold/sell stance with brief rationale

Price Target:
- Short-term and long-term price targets
```

This new format ensures all critical information is presented while avoiding verbosity.

## How to Run Tests

### Individual Test Files

1. **Test Stock Scoring:**
   ```
   python test_stock_scoring.py
   ```
   This tests the scoring algorithm with sample stock data without making any API calls.

2. **Test AI Analysis:**
   ```
   python test_ai_analysis.py --format-only  # Just test formatting, no API calls
   python test_ai_analysis.py --single        # Test with a single stock
   python test_ai_analysis.py                 # Test with multiple stocks
   ```
   Note: This makes API calls to OpenAI GPT. Use `--format-only` to avoid making API calls.

3. **Test News Fetching:**
   ```
   python test_news_fetching.py --sample      # Use sample data, no API calls
   python test_news_fetching.py --single      # Test with a single stock
   python test_news_fetching.py               # Test with multiple stocks
   ```
   Note: This makes API calls to Yahoo Finance unless using `--sample`.

4. **Test File Saving:**
   ```
   python test_file_saving.py                 # Test all saving functions
   python test_file_saving.py --news          # Test only news data saving
   python test_file_saving.py --tickers       # Test only ticker data saving
   python test_file_saving.py --summary       # Test only investment summary saving
   ```
   This tests file saving functionality using sample data without making API calls.

### Running Specific Components

The `run_specific_component.py` script allows you to run specific parts of the stock screener:

```
python run_specific_component.py --fetch      # Run stock fetching component
python run_specific_component.py --screen     # Run stock screening component
python run_specific_component.py --news       # Run news fetching component
python run_specific_component.py --analyze    # Run AI analysis component
```

You can combine multiple flags to run multiple components:
```
python run_specific_component.py --fetch --screen  # Fetch and screen stocks
```

## API Usage Notes

- **Yahoo Finance API:** The news fetching and stock fetching components make API calls to Yahoo Finance.
- **OpenAI API:** The AI analysis component makes API calls to OpenAI's GPT-4o-mini model.

The application uses GPT-4o-mini instead of GPT-4o to reduce costs (approximately 1/10 the cost).

## Testing Tips

1. **Use Sample Data When Possible:** To avoid API calls, use the `--sample` flag when available.
2. **Limit Sample Size:** When testing with real API calls, limit the sample size to reduce costs.
3. **Check Results Directory:** Test results are saved in either `test_results/` or `component_results/`.
4. **Error Logs:** Check the logs for any errors or warnings during testing.

## Extending Test Files

If you need to create additional test files:

1. **Import Sample Data:**
   ```python
   from stock_screener.data.test_data import SAMPLE_STOCKS, SAMPLE_NEWS_DATA, SAMPLE_ANALYSIS
   ```

2. **Add New Sample Data:**
   Update `stock_screener/data/test_data.py` to include additional sample data.

3. **Command-Line Arguments:**
   Use `argparse` to define command-line arguments for different testing scenarios. 