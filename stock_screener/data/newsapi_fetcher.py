"""
Module for fetching and processing stock news using NewsAPI.
"""

from datetime import datetime, timedelta
from functools import lru_cache
from ..utils.helpers import setup_logging
from ..config.settings import (
    NEWS_API_KEY,
    NEWS_CACHE_DURATION,
    MAX_NEWS_ARTICLES,
    NEWS_LOOKBACK_DAYS,
)
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException
from tenacity import retry, stop_after_attempt, wait_exponential

logger = setup_logging()

# Cache for news
news_cache = {}


@lru_cache(maxsize=128)
@retry(
    stop=stop_after_attempt(MAX_NEWS_ARTICLES),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def get_stock_news(ticker, max_articles=MAX_NEWS_ARTICLES):
    """Get stock news with caching and improved error handling using NewsAPI."""
    logger.info(f"Fetching news for {ticker}...")

    # Check cache first
    if ticker in news_cache:
        cached_data, timestamp = news_cache[ticker]
        if datetime.now() - timestamp < timedelta(seconds=NEWS_CACHE_DURATION):
            logger.info("Using cached news data")
            return cached_data

    try:
        # Initialize NewsAPI client
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)

        # Calculate date range (last N days)
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=NEWS_LOOKBACK_DAYS)).strftime(
            "%Y-%m-%d"
        )

        # Get articles about the stock
        # Add company name to search if available to improve results
        query = ticker

        logger.info(
            f"Searching for news with query: {query} from {from_date} to {to_date}"
        )
        articles = newsapi.get_everything(
            q=query,
            from_param=from_date,
            to=to_date,
            language="en",
            sort_by="relevancy",
            page_size=max_articles,
        )

        articles_list = articles.get("articles", [])

        if not articles_list:
            logger.warning(f"No news articles found for {ticker}")
            return f"No news found for {ticker}."

        logger.info(f"Found {len(articles_list)} articles.")

        news_summary = ""
        for article in articles_list[:max_articles]:
            title = article.get("title", "No title")
            description = article.get("description", "No description available")
            published_at = article.get("publishedAt", "")
            source = article.get("source", {}).get("name", "Unknown")
            url = article.get("url", "#")

            news_summary += (
                f"Source: {source}\n"
                f"Date: {published_at}\n"
                f"Headline: {title}\n"
                f"Summary: {description}\n"
                f"URL: {url}\n\n"
            )

        # Cache the results
        news_cache[ticker] = (news_summary, datetime.now())
        return news_summary

    except NewsAPIException as e:
        logger.error(f"NewsAPI Error fetching news for {ticker}: {e}")
        # Reraise the exception to trigger tenacity retry
        raise e
    except Exception as e:
        logger.error(f"Unexpected error fetching news for {ticker}: {e}")
        # Don't retry on unexpected errors, return error message
        return f"Error fetching news for {ticker}."
