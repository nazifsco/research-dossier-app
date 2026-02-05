#!/usr/bin/env python3
"""
Web Search Script
Performs web searches using DuckDuckGo with retry logic and fallback.

Usage:
    python search_web.py --query "OpenAI" --num_results 20
    echo '{"query": "OpenAI", "num_results": 20}' | python search_web.py --stdin

Output: JSON array of search results with title, url, snippet

Improvements (annealed 2026-01-28):
- Added retry logic with exponential backoff
- Added timeout handling
- Added fallback to requests-based search if DDGS fails
"""

import argparse
import json
import sys
import time
import random
from urllib.parse import quote_plus, urljoin

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds
MAX_DELAY = 30  # seconds

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False
        print("Warning: ddgs/duckduckgo_search not installed. Using fallback.", file=sys.stderr)

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


def search_with_retry(search_func, *args, **kwargs) -> list:
    """Execute a search function with retry logic."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            results = search_func(*args, **kwargs)
            if results:  # Success
                return results
            # Empty results might be temporary, retry
            if attempt < MAX_RETRIES - 1:
                delay = exponential_backoff(attempt)
                print(f"Empty results, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(delay)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = exponential_backoff(attempt)
                print(f"Search error: {e}. Retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"Search failed after {MAX_RETRIES} attempts: {e}", file=sys.stderr)

    return []


def search_ddgs(query: str, num_results: int = 20, region: str = "wt-wt") -> list:
    """Search using DuckDuckGo DDGS library."""
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, region=region, max_results=num_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })

    return results


def search_ddgs_news(query: str, num_results: int = 20) -> list:
    """Search news using DuckDuckGo DDGS library."""
    results = []

    with DDGS() as ddgs:
        for r in ddgs.news(query, max_results=num_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("body", ""),
                "date": r.get("date", ""),
                "source": r.get("source", "")
            })

    return results


def search_fallback(query: str, num_results: int = 20) -> list:
    """Fallback search using direct HTML scraping of DuckDuckGo HTML version."""
    if not HAS_REQUESTS:
        print("Fallback requires requests and beautifulsoup4", file=sys.stderr)
        return []

    results = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Use DuckDuckGo HTML version (no JavaScript required)
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Parse results from HTML
        for result in soup.select(".result")[:num_results]:
            title_elem = result.select_one(".result__title")
            link_elem = result.select_one(".result__url")
            snippet_elem = result.select_one(".result__snippet")

            if title_elem:
                # Extract actual URL from DuckDuckGo redirect
                href = title_elem.find("a")
                if href and href.get("href"):
                    url = href.get("href")
                    # DDG uses redirect URLs, try to extract actual URL
                    if "uddg=" in url:
                        from urllib.parse import parse_qs, urlparse
                        parsed = urlparse(url)
                        params = parse_qs(parsed.query)
                        if "uddg" in params:
                            url = params["uddg"][0]

                results.append({
                    "title": title_elem.get_text(strip=True),
                    "url": url,
                    "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                })

        print(f"Fallback search returned {len(results)} results", file=sys.stderr)

    except Exception as e:
        print(f"Fallback search error: {e}", file=sys.stderr)

    return results


def search_web(query: str, num_results: int = 20, region: str = "wt-wt") -> list:
    """
    Perform a web search with retry and fallback.

    Args:
        query: Search query string
        num_results: Maximum number of results to return
        region: Region code (wt-wt = worldwide)

    Returns:
        List of search results with title, url, snippet
    """
    results = []

    # Try DDGS first with retry
    if HAS_DDGS:
        results = search_with_retry(search_ddgs, query, num_results, region)

    # Fallback if DDGS failed or returned empty
    if not results and HAS_REQUESTS:
        print("Primary search failed, trying fallback...", file=sys.stderr)
        results = search_with_retry(search_fallback, query, num_results)

    return results


def search_news(query: str, num_results: int = 20) -> list:
    """
    Perform a news search with retry.
    """
    if HAS_DDGS:
        return search_with_retry(search_ddgs_news, query, num_results)
    return []


def main():
    parser = argparse.ArgumentParser(description="Web search using DuckDuckGo")
    parser.add_argument("--query", "-q", type=str, help="Search query")
    parser.add_argument("--num_results", "-n", type=int, default=20, help="Number of results")
    parser.add_argument("--news", action="store_true", help="Search news instead of web")
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
        num_results = input_data.get("num_results", 20)
        news_mode = input_data.get("news", False)
    else:
        query = args.query
        num_results = args.num_results
        news_mode = args.news

    if not query:
        print("Error: No query provided", file=sys.stderr)
        sys.exit(1)

    # Perform search
    if news_mode:
        results = search_news(query, num_results)
    else:
        results = search_web(query, num_results)

    # Output results
    output = {
        "query": query,
        "num_results": len(results),
        "results": results,
        "search_method": "ddgs" if results and HAS_DDGS else "fallback"
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
