#!/usr/bin/env python3
"""
Research Analyzer Script
Compiles and analyzes all collected research data.

Usage:
    python analyze_research.py --research_dir ".tmp/research_openai/"
    echo '{"research_dir": ".tmp/research_openai/"}' | python analyze_research.py --stdin

Output: JSON with compiled analysis, key facts, timeline, and insights
"""

import argparse
import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path
from collections import Counter


def load_json_file(filepath: str) -> dict:
    """Load a JSON file, return empty dict on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def extract_dates(text: str) -> list:
    """Extract dates from text."""
    patterns = [
        r'\b(\d{4}-\d{2}-\d{2})\b',
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
    ]

    dates = []
    for pattern in patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))

    return dates


def extract_numbers(text: str) -> list:
    """Extract significant numbers (funding, revenue, employees, etc.)."""
    patterns = [
        (r'\$[\d,]+(?:\.\d+)?\s*(?:billion|B)\b', 'billion'),
        (r'\$[\d,]+(?:\.\d+)?\s*(?:million|M)\b', 'million'),
        (r'\$[\d,]+(?:\.\d+)?\s*(?:thousand|K)\b', 'thousand'),
        (r'(\d{1,3}(?:,\d{3})+)\s*employees', 'employees'),
        (r'raised\s+\$[\d,]+(?:\.\d+)?\s*(?:billion|million|B|M)', 'funding'),
        (r'valued\s+at\s+\$[\d,]+(?:\.\d+)?\s*(?:billion|million|B|M)', 'valuation'),
    ]

    numbers = []
    for pattern, category in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            numbers.append({"value": match, "category": category})

    return numbers


def extract_people(text: str) -> list:
    """Extract people names and titles."""
    patterns = [
        r'(?:CEO|CTO|CFO|COO|founder|co-founder|president|chairman)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:the\s+)?(?:CEO|CTO|CFO|COO|founder|co-founder|president|chairman)',
    ]

    people = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        people.extend(matches)

    return list(set(people))


def extract_companies(text: str) -> list:
    """Extract company names mentioned."""
    # Common company suffixes
    pattern = r'\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)\s+(?:Inc\.?|Corp\.?|LLC|Ltd\.?|Company|Co\.?)\b'
    matches = re.findall(pattern, text)
    return list(set(matches))[:20]


def analyze_sentiment(text: str) -> dict:
    """Basic sentiment analysis based on keywords."""
    positive_words = ['growth', 'success', 'innovative', 'leading', 'profitable', 'expanding',
                      'breakthrough', 'achievement', 'partnership', 'launch', 'award']
    negative_words = ['lawsuit', 'decline', 'loss', 'layoff', 'controversy', 'investigation',
                      'failure', 'struggle', 'debt', 'scandal', 'criticism']

    text_lower = text.lower()

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    total = positive_count + negative_count
    if total == 0:
        return {"sentiment": "neutral", "score": 0, "positive": 0, "negative": 0}

    score = (positive_count - negative_count) / total

    if score > 0.2:
        sentiment = "positive"
    elif score < -0.2:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "score": round(score, 2),
        "positive_signals": positive_count,
        "negative_signals": negative_count
    }


def compile_timeline(news_data: dict, search_data: dict) -> list:
    """Compile a timeline of events from news and search results."""
    events = []

    # From news
    for article in news_data.get("articles", []):
        date = article.get("date", "")
        if date:
            events.append({
                "date": date[:10] if len(date) > 10 else date,
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "type": "news"
            })

    # Sort by date
    events.sort(key=lambda x: x.get("date", ""), reverse=True)

    return events[:20]  # Limit to 20 most recent


def analyze_research(research_dir: str) -> dict:
    """
    Analyze all research data in a directory.

    Args:
        research_dir: Path to research directory

    Returns:
        Compiled analysis with key facts, timeline, and insights
    """
    research_path = Path(research_dir)

    if not research_path.exists():
        return {"success": False, "error": f"Research directory not found: {research_dir}"}

    # Load available data files
    search_data = load_json_file(research_path / "01_search_results.json")
    sources_data = load_json_file(research_path / "02_sources.json")
    news_data = load_json_file(research_path / "04_news.json")
    financials_data = load_json_file(research_path / "05_financials.json")
    social_data = load_json_file(research_path / "06_social.json")

    # Load page content
    pages_dir = research_path / "03_pages"
    page_content = ""
    if pages_dir.exists():
        for page_file in pages_dir.glob("*.json"):
            page_data = load_json_file(page_file)
            page_content += page_data.get("content", "") + "\n"

    # Combine all text for analysis
    all_text = page_content
    all_text += " ".join([r.get("snippet", "") for r in search_data.get("results", [])])
    all_text += " ".join([a.get("snippet", "") for a in news_data.get("articles", [])])

    # Extract insights
    key_people = extract_people(all_text)
    key_numbers = extract_numbers(all_text)
    mentioned_companies = extract_companies(all_text)
    sentiment = analyze_sentiment(all_text)
    timeline = compile_timeline(news_data, search_data)

    # Compile key facts
    key_facts = {}

    # From financials
    if financials_data.get("success"):
        company = financials_data.get("company", {})
        key_facts["company_name"] = company.get("name")
        key_facts["sector"] = company.get("sector")
        key_facts["industry"] = company.get("industry")
        key_facts["employees"] = company.get("employees")
        key_facts["website"] = company.get("website")
        key_facts["description"] = company.get("description")

        fin = financials_data.get("financials", {})
        key_facts["market_cap"] = fin.get("market_cap_formatted")
        key_facts["revenue"] = fin.get("revenue_formatted")

    # From social
    if social_data:
        key_facts["social_profiles"] = list(social_data.get("profiles", {}).keys())
        key_facts["social_presence_score"] = social_data.get("presence_score")

    # SWOT analysis (basic)
    swot = {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": []
    }

    if sentiment["positive_signals"] > 3:
        swot["strengths"].append("Positive media coverage")
    if financials_data.get("financials", {}).get("revenue_growth"):
        growth = financials_data["financials"]["revenue_growth"]
        if growth and growth > 0:
            swot["strengths"].append(f"Revenue growth: {growth:.1%}")
    if len(social_data.get("profiles", {})) > 3:
        swot["strengths"].append("Strong social media presence")

    if sentiment["negative_signals"] > 2:
        swot["threats"].append("Some negative media coverage")

    return {
        "success": True,
        "research_dir": str(research_dir),
        "key_facts": key_facts,
        "key_people": key_people[:10],
        "key_numbers": key_numbers[:10],
        "mentioned_companies": mentioned_companies[:10],
        "sentiment": sentiment,
        "timeline": timeline,
        "swot": swot,
        "data_sources": {
            "search_results": len(search_data.get("results", [])),
            "news_articles": len(news_data.get("articles", [])),
            "has_financials": financials_data.get("success", False),
            "social_profiles": len(social_data.get("profiles", {}))
        },
        "analyzed_at": datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze research data")
    parser.add_argument("--research_dir", "-d", type=str, help="Research directory path")
    parser.add_argument("--stdin", action="store_true", help="Read JSON input from stdin")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")

    args = parser.parse_args()

    # Get input
    if args.stdin:
        input_data = json.load(sys.stdin)
        research_dir = input_data.get("research_dir", "")
    else:
        research_dir = args.research_dir

    if not research_dir:
        print("Error: No research directory provided", file=sys.stderr)
        sys.exit(1)

    # Analyze
    result = analyze_research(research_dir)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
