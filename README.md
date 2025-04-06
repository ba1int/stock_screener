# Stock Screener

A comprehensive tool for screening, analyzing, and reporting on stocks, with a focus on penny stocks.

## Features

- Screen stocks based on financial metrics
- Fetch real-time stock data with Yahoo Finance
- Analyze options data for market sentiment
- Generate AI-powered analysis using Llama 3 via Ollama
- Save detailed investment reports and summaries

## Project Structure

```
stock_screener/
│
├── analysis/           # Stock analysis components
├── config/             # Configuration settings
├── data/               # Data retrieval and processing
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

5. Install Ollama (for local LLM support)
   - Follow instructions at [Ollama's GitHub](https://github.com/ollama/ollama)
   - Pull the Llama 3 model:
   ```bash
   ollama pull llama3:latest
   ```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file and add your configuration:
```
YAHOO_MAX_RETRIES=3
YAHOO_TIMEOUT=10
```

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

# Run AI analysis component
python run_specific_component.py --analyze
```

## Testing

```bash
# Run a single stock analysis test
python test_ai_analysis.py --single

# Test stock scoring
python test_stock_scoring.py
```

## Output Files

The screener generates several output files:

- `selected_tickers_[date].json`: Basic information about all selected stocks
- `investment_summary_[date].md`: Detailed investment summary with analysis
- `penny_stocks_analysis_[date].md`: Comprehensive analysis of screened stocks

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## AI Analysis Integration

The stock screener uses Llama 3 via Ollama for generating stock analyses. This provides:
- Local processing of analyses (no API costs)
- Privacy (data stays on your machine)
- Customizable analysis through prompt engineering
- Fast response times

### Requirements

- Ollama installed and running
- Llama 3 model pulled (`ollama pull llama3:latest`)
- Sufficient system resources for LLM inference 