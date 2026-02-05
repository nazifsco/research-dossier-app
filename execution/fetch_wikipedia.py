#!/usr/bin/env python3
"""
Wikipedia Fetcher Script
Fetches company/person information from Wikipedia API (free, no key required).

Usage:
    python fetch_wikipedia.py --query "OpenAI"
    python fetch_wikipedia.py --query "Elon Musk" --type person

Output: JSON with summary, full content, infobox data, and links
"""

import argparse
import json
import sys
import re
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1"
WIKIPEDIA_ACTION_API = "https://en.wikipedia.org/w/api.php"


def search_wikipedia(query: str, limit: int = 5) -> list:
    """Search Wikipedia for matching articles."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json"
    }

    try:
        response = requests.get(WIKIPEDIA_ACTION_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("query", {}).get("search", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": re.sub(r'<[^>]+>', '', item.get("snippet", "")),
                "pageid": item.get("pageid")
            })
        return results
    except Exception as e:
        print(f"Wikipedia search error: {e}", file=sys.stderr)
        return []


def get_page_summary(title: str) -> dict:
    """Get page summary from Wikipedia REST API."""
    try:
        url = f"{WIKIPEDIA_API}/page/summary/{quote(title)}"
        response = requests.get(url, timeout=30)

        if response.status_code == 404:
            return {"error": "Page not found"}

        response.raise_for_status()
        data = response.json()

        return {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "extract": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "image": data.get("thumbnail", {}).get("source", ""),
            "type": data.get("type", "")
        }
    except Exception as e:
        print(f"Wikipedia summary error: {e}", file=sys.stderr)
        return {"error": str(e)}


def get_page_content(title: str) -> dict:
    """Get full page content and metadata."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts|info|categories|links|extlinks",
        "exintro": False,
        "explaintext": True,
        "inprop": "url",
        "cllimit": 20,
        "pllimit": 50,
        "ellimit": 20,
        "format": "json"
    }

    try:
        response = requests.get(WIKIPEDIA_ACTION_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return {"error": "No page data"}

        page = list(pages.values())[0]

        if "missing" in page:
            return {"error": "Page not found"}

        # Extract categories
        categories = [cat.get("title", "").replace("Category:", "")
                     for cat in page.get("categories", [])]

        # Extract external links
        external_links = [link.get("*", "") for link in page.get("extlinks", [])]

        return {
            "title": page.get("title", ""),
            "pageid": page.get("pageid"),
            "url": page.get("fullurl", ""),
            "content": page.get("extract", "")[:10000],  # Limit content size
            "content_length": len(page.get("extract", "")),
            "categories": categories,
            "external_links": external_links[:10]
        }
    except Exception as e:
        print(f"Wikipedia content error: {e}", file=sys.stderr)
        return {"error": str(e)}


def extract_infobox_data(title: str) -> dict:
    """Try to extract structured infobox data."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json"
    }

    try:
        response = requests.get(WIKIPEDIA_ACTION_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return {}

        page = list(pages.values())[0]
        content = page.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("*", "")

        # Parse infobox (simplified extraction)
        infobox = {}

        # Common patterns in infoboxes
        patterns = [
            (r'\|\s*founded\s*=\s*(.+?)(?:\n|\|)', 'founded'),
            (r'\|\s*founder\s*=\s*(.+?)(?:\n|\|)', 'founder'),
            (r'\|\s*headquarters\s*=\s*(.+?)(?:\n|\|)', 'headquarters'),
            (r'\|\s*location\s*=\s*(.+?)(?:\n|\|)', 'location'),
            (r'\|\s*industry\s*=\s*(.+?)(?:\n|\|)', 'industry'),
            (r'\|\s*products?\s*=\s*(.+?)(?:\n|\|)', 'products'),
            (r'\|\s*services?\s*=\s*(.+?)(?:\n|\|)', 'services'),
            (r'\|\s*revenue\s*=\s*(.+?)(?:\n|\|)', 'revenue'),
            (r'\|\s*num_employees\s*=\s*(.+?)(?:\n|\|)', 'employees'),
            (r'\|\s*website\s*=\s*(.+?)(?:\n|\|)', 'website'),
            (r'\|\s*type\s*=\s*(.+?)(?:\n|\|)', 'company_type'),
            (r'\|\s*ceo\s*=\s*(.+?)(?:\n|\|)', 'ceo'),
            (r'\|\s*key_people\s*=\s*(.+?)(?:\n|\|)', 'key_people'),
        ]

        for pattern, key in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up wiki markup
                value = re.sub(r'\[\[([^\]|]+)\|?[^\]]*\]\]', r'\1', value)
                value = re.sub(r'\{\{[^}]+\}\}', '', value)
                value = re.sub(r'<[^>]+>', '', value)
                value = value.strip()
                if value:
                    infobox[key] = value

        return infobox
    except Exception as e:
        print(f"Infobox extraction error: {e}", file=sys.stderr)
        return {}


def fetch_wikipedia(query: str, entity_type: str = "auto") -> dict:
    """
    Fetch Wikipedia data for a query.

    Args:
        query: Search query (company name, person name, etc.)
        entity_type: "company", "person", or "auto"

    Returns:
        Dict with Wikipedia data
    """
    # Search for the article
    search_results = search_wikipedia(query, limit=3)

    if not search_results:
        return {
            "success": False,
            "query": query,
            "error": "No Wikipedia article found"
        }

    # Use first result
    best_match = search_results[0]
    title = best_match["title"]

    # Get summary
    summary = get_page_summary(title)
    if "error" in summary:
        return {
            "success": False,
            "query": query,
            "error": summary["error"]
        }

    # Get full content
    content = get_page_content(title)

    # Try to extract infobox data
    infobox = extract_infobox_data(title)

    return {
        "success": True,
        "query": query,
        "title": summary.get("title", title),
        "description": summary.get("description", ""),
        "summary": summary.get("extract", ""),
        "url": summary.get("url", ""),
        "image": summary.get("image", ""),
        "full_content": content.get("content", "")[:5000],
        "categories": content.get("categories", []),
        "external_links": content.get("external_links", []),
        "infobox": infobox,
        "search_results": search_results,
        "source": "wikipedia"
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch Wikipedia data")
    parser.add_argument("--query", "-q", type=str, required=True, help="Search query")
    parser.add_argument("--type", "-t", type=str, default="auto",
                       choices=["auto", "company", "person"], help="Entity type")
    parser.add_argument("--output", "-o", type=str, help="Output file")

    args = parser.parse_args()

    result = fetch_wikipedia(args.query, args.type)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
