"""
Sample stock data for testing components.
"""

# Sample stock data for testing
SAMPLE_STOCKS = [
    {
        'ticker': 'AAPL',
        'price': 175.50,
        'volume': 65000000,
        'avg_volume': 70000000,
        'high_52w': 200.30,
        'low_52w': 150.10,
        'company_name': 'Apple Inc.',
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'market_cap': 2800000000000,
        'pe_ratio': 28.5,
        'eps': 6.15,
        'dividend_yield': 0.65,
        'beta': 1.21,
        'description': 'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.'
    },
    {
        'ticker': 'FCEL',
        'price': 4.46,
        'volume': 2500000,
        'avg_volume': 1325169,
        'high_52w': 7.80,
        'low_52w': 0.80,
        'company_name': 'FuelCell Energy, Inc.',
        'sector': 'Industrials',
        'industry': 'Electrical Equipment & Parts',
        'market_cap': 94301352,
        'pe_ratio': None,
        'eps': -7.88,
        'dividend_yield': None,
        'beta': 3.94,
        'description': 'FuelCell Energy, Inc. designs, manufactures, sells, installs, operates, and services stationary fuel cell power plants for distributed baseload power generation.'
    },
    {
        'ticker': 'OCGN',
        'price': 0.66,
        'volume': 3500000,
        'avg_volume': 5008865,
        'high_52w': 1.25,
        'low_52w': 0.25,
        'company_name': 'Ocugen, Inc.',
        'sector': 'Healthcare',
        'industry': 'Biotechnology',
        'market_cap': 193310000,
        'pe_ratio': None,
        'eps': -0.20,
        'dividend_yield': None,
        'beta': 3.79,
        'description': 'Ocugen, Inc., a clinical-stage biopharmaceutical company, focuses on discovering, developing, and commercializing gene therapies, vaccines, and biologics.'
    },
    {
        'ticker': 'NOK',
        'price': 4.78,
        'volume': 26028400,
        'avg_volume': 17341087,
        'high_52w': 5.48,
        'low_52w': 3.20,
        'company_name': 'Nokia Corporation',
        'sector': 'Technology',
        'industry': 'Communication Equipment',
        'market_cap': 26523791360,
        'pe_ratio': 14.06,
        'eps': 0.34,
        'dividend_yield': 2.61,
        'beta': 0.78,
        'description': 'Nokia Corporation engages in the network and technology businesses worldwide.'
    },
    {
        'ticker': 'AMC',
        'price': 2.65,
        'volume': 30000000,
        'avg_volume': 23616373,
        'high_52w': 10.20,
        'low_52w': 1.85,
        'company_name': 'AMC Entertainment Holdings, Inc.',
        'sector': 'Communication Services',
        'industry': 'Entertainment',
        'market_cap': 1150000000,
        'pe_ratio': None,
        'eps': -1.06,
        'dividend_yield': None,
        'beta': 1.83,
        'description': 'AMC Entertainment Holdings, Inc. operates as a theatrical exhibition company.'
    }
]

# Sample news data for testing
SAMPLE_NEWS_DATA = {
    'AAPL': '- [Apple announces new iPhone models](https://example.com/news1) - TechCrunch (2025-04-01)\n- [Apple reports record Q1 earnings](https://example.com/news2) - CNBC (2025-03-15)\n',
    'FCEL': '- [FuelCell Energy partners with major utility](https://example.com/news3) - Reuters (2025-04-02)\n- [Hydrogen stocks gain momentum](https://example.com/news4) - Bloomberg (2025-03-20)\n',
    'OCGN': '- [Ocugen announces positive trial results](https://example.com/news5) - BioSpace (2025-04-03)\n- [Ocugen secures new funding](https://example.com/news6) - BioPharma Dive (2025-03-28)\n',
    'NOK': '- [Nokia wins major 5G contract](https://example.com/news7) - Reuters (2025-04-02)\n- [Nokia expands in emerging markets](https://example.com/news8) - Financial Times (2025-03-25)\n',
    'AMC': '- [AMC introduces new subscription service](https://example.com/news9) - Variety (2025-04-01)\n- [Movie theater attendance rebounds](https://example.com/news10) - Hollywood Reporter (2025-03-18)\n'
}

# Sample analysis results for testing
SAMPLE_ANALYSIS = {
    'AAPL': 'Apple presents a strong investment opportunity with consistent revenue growth and a loyal customer base. The company continues to innovate in its product lineup while expanding services revenue. Strong financial position with large cash reserves.',
    'FCEL': 'FuelCell Energy operates in the promising clean energy sector but faces significant challenges in achieving profitability. High volatility makes this a speculative investment. Consider only as a small position in a diversified portfolio.',
    'OCGN': 'Ocugen is a high-risk biotech play with significant binary outcome potential based on clinical trial results. Current losses and cash burn rate present challenges, but successful trials could provide substantial upside.',
    'NOK': 'Nokia offers stability with modest growth potential in the expanding 5G infrastructure market. Lower volatility than peers makes it suitable for more conservative investors seeking exposure to telecommunications equipment.',
    'AMC': 'AMC faces continued challenges from streaming competition and debt levels. While recent retail investor interest has supported the stock price, fundamental concerns remain about long-term profitability and industry trends.'
} 