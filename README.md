# Stock Screener

A comprehensive tool for screening, analyzing, and reporting on stocks, with a focus on penny stocks.

## Features

- Screen stocks based on financial metrics
- Fetch real-time stock data with Yahoo Finance
- Fetch relevant news articles with NewsAPI.org
- Generate AI-powered analysis using GPT models
- Save detailed investment reports and summaries

## Project Structure

```
stock_screener/
│
├── analysis/           # Stock analysis components
├── config/             # Configuration settings
├── data/               # Data retrieval and processing
│   ├── newsapi_fetcher.py  # News fetching using NewsAPI
│   ├── simple_yahoo.py     # Yahoo Finance integration
│   ├── stock_screener.py   # Main screening logic
│   └── test_data.py        # Sample data for testing
├── utils/              # Utility functions
└── main.py             # Main entry point
```

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/stock_screener.git
cd stock_screener
```

2. Create a virtual environment
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. Install requirements
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key
NEWS_API_KEY=your_newsapi_key
YAHOO_MAX_RETRIES=3
YAHOO_TIMEOUT=10
```

You'll need:
- An OpenAI API key from [OpenAI](https://platform.openai.com/)
- A NewsAPI key from [NewsAPI.org](https://newsapi.org/)

## Usage

### Running the Full Screener

```bash
# Run the full stock screener
python -m stock_screener.main
```

### Running Individual Components

```bash
# Run stock fetching component
python run_specific_component.py --fetch

# Run stock screening component
python run_specific_component.py --screen

# Run news fetching component
python run_specific_component.py --news

# Run AI analysis component
python run_specific_component.py --analyze
```

## Testing

See [README_TESTING.md](README_TESTING.md) for detailed information on testing individual components.

```bash
# Run a single stock analysis test
python test_ai_analysis.py --single

# Test news fetching with sample data
python test_news_fetching.py --sample
```

## Output Files

The screener generates several output files:

- `selected_tickers_[date].json`: Basic information about all selected stocks
- `investment_summary_[date].md`: Detailed investment summary with analysis
- `news_data_[date].json`: News articles for each stock
- `analysis_reports/[ticker]_analysis_[date].txt`: Detailed AI analysis per stock

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## News API Integration

The stock screener uses NewsAPI.org for fetching news articles, providing high-quality, well-formatted news data for each stock.

### Requirements

- A NewsAPI.org API key (add to `.env` file as `NEWS_API_KEY`)
- The newsapi-python package: `pip install newsapi-python` 