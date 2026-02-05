#!/usr/bin/env python3
"""
Social Presence Fetcher Script
Discovers and fetches social media presence for a target.

Usage:
    python fetch_social.py --target "OpenAI" --platforms linkedin,twitter
    echo '{"target": "OpenAI"}' | python fetch_social.py --stdin

Output: JSON with discovered social profiles and basic info
"""

import argparse
import json
import sys
import re
from urllib.parse import quote_plus

try:
    from duckduckgo_search import DDGS
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed. Run: pip install duckduckgo-search requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Social platform patterns
SOCIAL_PATTERNS = {
    "linkedin_company": r"linkedin\.com/company/([^/\?]+)",
    "linkedin_person": r"linkedin\.com/in/([^/\?]+)",
    "twitter": r"(?:twitter\.com|x\.com)/([^/\?]+)",
    "facebook": r"facebook\.com/([^/\?]+)",
    "instagram": r"instagram\.com/([^/\?]+)",
    "youtube": r"youtube\.com/(?:c/|channel/|@)([^/\?]+)",
    "github": r"github\.com/([^/\?]+)",
    "crunchbase": r"crunchbase\.com/organization/([^/\?]+)",
}


def search_social_profiles(target: str) -> dict:
    """
    Search for social media profiles using web search.
    """
    profiles = {}

    # Search queries for different platforms
    searches = [
        f"{target} site:linkedin.com",
        f"{target} site:twitter.com OR site:x.com",
        f"{target} site:crunchbase.com",
        f"{target} official site",
    ]

    all_urls = []

    try:
        with DDGS() as ddgs:
            for query in searches:
                for r in ddgs.text(query, max_results=5):
                    url = r.get("href", "")
                    title = r.get("title", "")
                    snippet = r.get("body", "")
                    all_urls.append({"url": url, "title": title, "snippet": snippet})
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)

    # Extract social profiles from URLs
    for item in all_urls:
        url = item["url"]

        for platform, pattern in SOCIAL_PATTERNS.items():
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                handle = match.group(1)
                if platform not in profiles:
                    profiles[platform] = {
                        "url": url,
                        "handle": handle,
                        "title": item["title"],
                        "snippet": item["snippet"]
                    }

    return profiles


def find_official_website(target: str, search_results: list) -> str:
    """Try to identify the official website."""
    # Look for common patterns
    target_lower = target.lower().replace(" ", "")

    for result in search_results:
        url = result.get("url", "").lower()
        # Check if domain contains target name
        if target_lower in url.replace("www.", "").split("/")[0]:
            return result.get("url", "")

    return ""


def fetch_social_presence(target: str, platforms: list = None) -> dict:
    """
    Discover social media presence for a target.

    Args:
        target: Company or person name
        platforms: List of platforms to focus on (optional)

    Returns:
        Dict with discovered profiles and metadata
    """
    profiles = search_social_profiles(target)

    # Filter to requested platforms if specified
    if platforms:
        profiles = {k: v for k, v in profiles.items()
                   if any(p in k for p in platforms)}

    # Calculate presence score
    presence_score = len(profiles) / len(SOCIAL_PATTERNS) * 100

    # Identify primary platforms
    primary_platforms = []
    if "linkedin_company" in profiles or "linkedin_person" in profiles:
        primary_platforms.append("LinkedIn")
    if "twitter" in profiles:
        primary_platforms.append("Twitter/X")
    if "crunchbase" in profiles:
        primary_platforms.append("Crunchbase")

    return {
        "target": target,
        "profiles": profiles,
        "num_profiles_found": len(profiles),
        "presence_score": round(presence_score, 1),
        "primary_platforms": primary_platforms,
        "platforms_checked": list(SOCIAL_PATTERNS.keys())
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch social media presence")
    parser.add_argument("--target", "-t", type=str, help="Target to research")
    parser.add_argument("--platforms", "-p", type=str, help="Comma-separated platforms")
    parser.add_argument("--stdin", action="store_true", help="Read JSON input from stdin")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")

    args = parser.parse_args()

    # Get input
    if args.stdin:
        input_data = json.load(sys.stdin)
        target = input_data.get("target", "")
        platforms = input_data.get("platforms", [])
        if isinstance(platforms, str):
            platforms = [p.strip() for p in platforms.split(",")]
    else:
        target = args.target
        platforms = args.platforms.split(",") if args.platforms else None

    if not target:
        print("Error: No target provided", file=sys.stderr)
        sys.exit(1)

    # Fetch social presence
    result = fetch_social_presence(target, platforms)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
