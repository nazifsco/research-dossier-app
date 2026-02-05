#!/usr/bin/env python3
"""
Webpage Fetcher Script
Fetches a webpage and extracts clean text content.

Usage:
    python fetch_webpage.py --url "https://example.com"
    echo '{"url": "https://example.com"}' | python fetch_webpage.py --stdin

Output: JSON with url, title, content, links, metadata
"""

import argparse
import json
import sys
import time
import re
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed. Run: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


# Default headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """Extract metadata from HTML."""
    metadata = {
        "url": url,
        "domain": urlparse(url).netloc,
    }

    # Title
    if soup.title:
        metadata["title"] = clean_text(soup.title.string or "")

    # Meta description
    desc = soup.find("meta", attrs={"name": "description"})
    if desc:
        metadata["description"] = desc.get("content", "")

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    if og_title:
        metadata["og_title"] = og_title.get("content", "")

    og_desc = soup.find("meta", property="og:description")
    if og_desc:
        metadata["og_description"] = og_desc.get("content", "")

    og_image = soup.find("meta", property="og:image")
    if og_image:
        metadata["og_image"] = og_image.get("content", "")

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    if canonical:
        metadata["canonical"] = canonical.get("href", "")

    return metadata


def extract_content(soup: BeautifulSoup) -> str:
    """Extract main text content from HTML."""
    # Remove script, style, nav, footer, header elements
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        element.decompose()

    # Try to find main content area
    main_content = None
    for selector in ["main", "article", "[role='main']", ".content", "#content", ".post", ".entry"]:
        main_content = soup.select_one(selector)
        if main_content:
            break

    if main_content:
        text = main_content.get_text(separator="\n")
    else:
        # Fallback to body
        body = soup.find("body")
        text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

    # Clean up
    lines = [clean_text(line) for line in text.split("\n")]
    lines = [line for line in lines if line and len(line) > 20]  # Filter short lines

    return "\n".join(lines)


def extract_links(soup: BeautifulSoup, base_url: str) -> list:
    """Extract links from HTML."""
    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = clean_text(a.get_text())

        # Skip empty or anchor links
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        # Make absolute URL
        full_url = urljoin(base_url, href)

        # Skip duplicates
        if full_url in seen:
            continue
        seen.add(full_url)

        links.append({
            "url": full_url,
            "text": text[:100] if text else ""
        })

    return links[:50]  # Limit to 50 links


def fetch_webpage(url: str, timeout: int = 30) -> dict:
    """
    Fetch and parse a webpage.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Dict with url, title, content, links, metadata
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract data
        metadata = extract_metadata(soup, response.url)
        content = extract_content(soup)
        links = extract_links(soup, response.url)

        return {
            "success": True,
            "url": response.url,
            "status_code": response.status_code,
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
            "content": content[:50000],  # Limit content size
            "content_length": len(content),
            "links": links,
            "metadata": metadata
        }

    except requests.exceptions.Timeout:
        return {"success": False, "url": url, "error": "Request timed out"}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "url": url, "error": f"HTTP error: {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "url": url, "error": str(e)}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Fetch and parse a webpage")
    parser.add_argument("--url", "-u", type=str, help="URL to fetch")
    parser.add_argument("--stdin", action="store_true", help="Read JSON input from stdin")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")
    parser.add_argument("--timeout", "-t", type=int, default=30, help="Request timeout")

    args = parser.parse_args()

    # Get input
    if args.stdin:
        input_data = json.load(sys.stdin)
        url = input_data.get("url", "")
        timeout = input_data.get("timeout", 30)
    else:
        url = args.url
        timeout = args.timeout

    if not url:
        print("Error: No URL provided", file=sys.stderr)
        sys.exit(1)

    # Fetch page
    result = fetch_webpage(url, timeout)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit with error if fetch failed
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
