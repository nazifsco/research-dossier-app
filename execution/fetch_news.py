#!/usr/bin/env python3
"""
News Fetcher Script
Fetches recent news articles about a topic using multiple sources.

Usage:
    python fetch_news.py --query "OpenAI" --days 30
    echo '{"query": "OpenAI", "days": 30}' | python fetch_news.py --stdin

Output: JSON with news articles including title, url, snippet, date, source

Improvements (annealed 2026-01-28):
- Added retry logic with exponential backoff
- Added Google News RSS fallback
- Better error handling and graceful degradation
"""

import argparse
import json
import sys
import os
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 2
MAX_DELAY = 30

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def exponential_backoff(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


def retry_wrapper(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """Execute a function with retry logic."""
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if result:
                return result
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt)
                print(f"Empty results, retrying in {delay:.1f}s...", file=sys.stderr)
                time.sleep(delay)
        except Exception as e:
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt)
                print(f"Error: {e}. Retrying in {delay:.1f}s...", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"Failed after {max_retries} attempts: {e}", file=sys.stderr)
    return []


def fetch_news_ddg(query: str, max_results: int = 20) -> list:
    """Fetch news using DuckDuckGo (free, no API key)."""
    if not HAS_DDGS:
        return []

    results = []

    with DDGS() as ddgs:
        for r in ddgs.news(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("body", ""),
                "date": r.get("date", ""),
                "source": r.get("source", ""),
                "provider": "duckduckgo"
            })

    return results


def fetch_news_google_rss(query: str, max_results: int = 20) -> list:
    """Fetch news using Google News RSS (free, no API key, more reliable)."""
    if not HAS_REQUESTS:
        return []

    results = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # Google News RSS feed
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "xml")

        for item in soup.find_all("item")[:max_results]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            source = item.find("source")

            # Extract description/snippet
            description = item.find("description")
            snippet = ""
            if description:
                # Google wraps content in CDATA, parse it
                desc_soup = BeautifulSoup(description.text, "html.parser")
                snippet = desc_soup.get_text(strip=True)[:300]

            results.append({
                "title": title.text if title else "",
                "url": link.text if link else "",
                "snippet": snippet,
                "date": pub_date.text if pub_date else "",
                "source": source.text if source else "",
                "provider": "google_rss"
            })

        print(f"Google News RSS returned {len(results)} results", file=sys.stderr)

    except Exception as e:
        print(f"Google News RSS error: {e}", file=sys.stderr)

    return results


def fetch_news_newsapi(query: str, days: int = 30, max_results: int = 20) -> list:
    """Fetch news using NewsAPI (requires API key)."""
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key or not HAS_REQUESTS:
        return []

    results = []
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "pageSize": max_results,
            "apiKey": api_key
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        for article in data.get("articles", []):
            results.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "snippet": article.get("description", ""),
                "date": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", ""),
                "author": article.get("author", ""),
                "image": article.get("urlToImage", ""),
                "provider": "newsapi"
            })

    except Exception as e:
        print(f"NewsAPI error: {e}", file=sys.stderr)

    return results


def deduplicate_news(articles: list) -> list:
    """Remove duplicate articles based on URL and similar titles."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for article in articles:
        url = article.get("url", "")
        title = article.get("title", "").lower().strip()

        # Skip if URL already seen
        if url and url in seen_urls:
            continue

        # Skip if very similar title already seen (fuzzy dedup)
        title_key = re.sub(r'[^a-z0-9]', '', title)[:50]
        if title_key and title_key in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title_key:
            seen_titles.add(title_key)
        unique.append(article)

    return unique


def parse_date_flexible(date_str: str) -> datetime:
    """Parse date from various formats."""
    if not date_str:
        return datetime.min

    # Common date formats
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.replace("GMT", "+0000"), fmt)
        except ValueError:
            continue

    # Try ISO format as fallback
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.min


def fetch_news(query: str, days: int = 30, max_results: int = 20) -> dict:
    """
    Fetch news from multiple sources with fallback.

    Args:
        query: Search query
        days: Number of days to look back
        max_results: Maximum number of results per source

    Returns:
        Dict with query, results, and metadata
    """
    all_results = []
    sources_used = []
    errors = []

    # Try DuckDuckGo first (with retry)
    if HAS_DDGS:
        ddg_results = retry_wrapper(fetch_news_ddg, query, max_results)
        if ddg_results:
            all_results.extend(ddg_results)
            sources_used.append("duckduckgo")

    # Try Google News RSS as fallback/supplement (more reliable)
    if HAS_REQUESTS:
        google_results = retry_wrapper(fetch_news_google_rss, query, max_results)
        if google_results:
            all_results.extend(google_results)
            sources_used.append("google_rss")

    # Try NewsAPI if key is available
    newsapi_results = fetch_news_newsapi(query, days, max_results)
    if newsapi_results:
        all_results.extend(newsapi_results)
        sources_used.append("newsapi")

    # If still no results, note it
    if not all_results:
        errors.append("All news sources failed or returned empty results")

    # Deduplicate
    all_results = deduplicate_news(all_results)

    # Sort by date (newest first)
    all_results.sort(key=lambda x: parse_date_flexible(x.get("date", "")), reverse=True)

    return {
        "query": query,
        "days": days,
        "num_results": len(all_results),
        "sources_used": sources_used,
        "articles": all_results[:max_results * 2],
        "errors": errors if errors else None,
        "fetched_at": datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch news articles")
    parser.add_argument("--query", "-q", type=str, help="Search query")
    parser.add_argument("--days", "-d", type=int, default=30, help="Days to look back")
    parser.add_argument("--max_results", "-n", type=int, default=20, help="Max results per source")
    parser.add_argument("--stdin", action="store_true", help="Read JSON input from stdin")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")
    parser.add_argument("--retries", "-r", type=int, default=3, help="Max retry attempts")

    args = parser.parse_args()

    # Update global retry config
    global MAX_RETRIES
    MAX_RETRIES = args.retries

    # Get input
    if args.stdin:
        input_data = json.load(sys.stdin)
        query = input_data.get("query", "")
        days = input_data.get("days", 30)
        max_results = input_data.get("max_results", 20)
    else:
        query = args.query
        days = args.days
        max_results = args.max_results

    if not query:
        print("Error: No query provided", file=sys.stderr)
        sys.exit(1)

    # Fetch news
    result = fetch_news(query, days, max_results)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
