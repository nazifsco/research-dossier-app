#!/usr/bin/env python3
"""
Dossier Generator Script
Generates a comprehensive research dossier from analyzed data.

Usage:
    python generate_dossier.py --research_dir ".tmp/research_openai/" --format markdown
    echo '{"research_dir": ".tmp/research_openai/"}' | python generate_dossier.py --stdin

Output: Formatted dossier in markdown or JSON
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path


def load_json_file(filepath: str) -> dict:
    """Load a JSON file, return empty dict on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def format_list(items: list, bullet: str = "-") -> str:
    """Format a list as markdown bullets."""
    if not items:
        return "_No data available_"
    return "\n".join([f"{bullet} {item}" for item in items])


def format_timeline(events: list) -> str:
    """Format timeline events."""
    if not events:
        return "_No recent events found_"

    lines = []
    for event in events[:10]:
        date = event.get("date", "Unknown date")
        title = event.get("title", "")
        source = event.get("source", "")
        lines.append(f"- **{date}**: {title}" + (f" _({source})_" if source else ""))

    return "\n".join(lines)


def format_swot(swot: dict) -> str:
    """Format SWOT analysis."""
    sections = []

    for category in ["strengths", "weaknesses", "opportunities", "threats"]:
        items = swot.get(category, [])
        title = category.capitalize()
        if items:
            sections.append(f"**{title}:**\n" + format_list(items))
        else:
            sections.append(f"**{title}:**\n_None identified_")

    return "\n\n".join(sections)


def generate_markdown_dossier(
    target: str,
    analysis: dict,
    financials: dict,
    social: dict,
    news: dict,
    search: dict
) -> str:
    """Generate a markdown formatted dossier."""

    key_facts = analysis.get("key_facts", {})
    sentiment = analysis.get("sentiment", {})
    timeline = analysis.get("timeline", [])
    swot = analysis.get("swot", {})
    key_people = analysis.get("key_people", [])
    mentioned_companies = analysis.get("mentioned_companies", [])

    # Build dossier sections
    sections = []

    # Header
    sections.append(f"""# Research Dossier: {target}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Data Sources:** {analysis.get('data_sources', {}).get('search_results', 0)} search results, {analysis.get('data_sources', {}).get('news_articles', 0)} news articles

---
""")

    # Executive Summary
    description = key_facts.get("description", "")
    if description:
        summary = description[:500] + "..." if len(description) > 500 else description
    else:
        summary = f"Research compilation for {target}."

    sections.append(f"""## Executive Summary

{summary}

**Overall Sentiment:** {sentiment.get('sentiment', 'neutral').capitalize()} (score: {sentiment.get('score', 0)})

---
""")

    # Key Facts
    facts_lines = []
    if key_facts.get("company_name"):
        facts_lines.append(f"- **Name:** {key_facts['company_name']}")
    if key_facts.get("sector"):
        facts_lines.append(f"- **Sector:** {key_facts['sector']}")
    if key_facts.get("industry"):
        facts_lines.append(f"- **Industry:** {key_facts['industry']}")
    if key_facts.get("employees"):
        facts_lines.append(f"- **Employees:** {key_facts['employees']:,}" if isinstance(key_facts['employees'], int) else f"- **Employees:** {key_facts['employees']}")
    if key_facts.get("website"):
        facts_lines.append(f"- **Website:** {key_facts['website']}")
    if key_facts.get("market_cap"):
        facts_lines.append(f"- **Market Cap:** {key_facts['market_cap']}")
    if key_facts.get("revenue"):
        facts_lines.append(f"- **Revenue:** {key_facts['revenue']}")

    sections.append(f"""## Key Facts

{chr(10).join(facts_lines) if facts_lines else "_No structured data available_"}

---
""")

    # Financial Overview (if available)
    if financials.get("success"):
        fin = financials.get("financials", {})
        val = financials.get("valuation", {})
        stock = financials.get("stock", {})

        sections.append(f"""## Financial Overview

**Stock Performance:**
- Current Price: ${stock.get('current_price', 'N/A')}
- 52-Week High: ${stock.get('52_week_high', 'N/A')}
- 52-Week Low: ${stock.get('52_week_low', 'N/A')}

**Key Metrics:**
- Market Cap: {fin.get('market_cap_formatted', 'N/A')}
- Revenue: {fin.get('revenue_formatted', 'N/A')}
- Profit Margin: {f"{fin['profit_margin']:.1%}" if fin.get('profit_margin') else 'N/A'}
- Revenue Growth: {f"{fin['revenue_growth']:.1%}" if fin.get('revenue_growth') else 'N/A'}

**Valuation:**
- P/E Ratio: {val.get('pe_ratio', 'N/A')}
- Price to Book: {val.get('price_to_book', 'N/A')}

**Analyst Recommendations:**
- Target Price (Mean): ${financials.get('recommendations', {}).get('target_mean_price', 'N/A')}
- Recommendation: {financials.get('recommendations', {}).get('recommendation', 'N/A')}

---
""")

    # Recent News & Developments
    sections.append(f"""## Recent News & Developments

{format_timeline(timeline)}

---
""")

    # Online Presence
    profiles = social.get("profiles", {})
    if profiles:
        profile_lines = []
        for platform, data in profiles.items():
            url = data.get("url", "")
            profile_lines.append(f"- **{platform.replace('_', ' ').title()}:** {url}")
        presence_section = "\n".join(profile_lines)
    else:
        presence_section = "_No social profiles found_"

    sections.append(f"""## Online Presence

**Presence Score:** {social.get('presence_score', 0)}%

{presence_section}

---
""")

    # Key People
    sections.append(f"""## Key People Identified

{format_list(key_people) if key_people else "_No key people identified_"}

---
""")

    # Related Companies
    sections.append(f"""## Related Companies Mentioned

{format_list(mentioned_companies) if mentioned_companies else "_No related companies identified_"}

---
""")

    # SWOT Analysis
    sections.append(f"""## SWOT Analysis

{format_swot(swot)}

---
""")

    # Sources
    source_urls = []
    for result in search.get("results", [])[:10]:
        url = result.get("url", "")
        title = result.get("title", url)
        source_urls.append(f"- [{title}]({url})")

    sections.append(f"""## Sources

{chr(10).join(source_urls) if source_urls else "_No sources recorded_"}

---

_This dossier was automatically generated. Verify critical information from primary sources._
""")

    return "\n".join(sections)


def generate_dossier(research_dir: str, output_format: str = "markdown") -> dict:
    """
    Generate a dossier from research data.

    Args:
        research_dir: Path to research directory
        output_format: "markdown" or "json"

    Returns:
        Dict with dossier content
    """
    research_path = Path(research_dir)

    if not research_path.exists():
        return {"success": False, "error": f"Research directory not found: {research_dir}"}

    # Load all data
    search_data = load_json_file(research_path / "01_search_results.json")
    news_data = load_json_file(research_path / "04_news.json")
    financials_data = load_json_file(research_path / "05_financials.json")
    social_data = load_json_file(research_path / "06_social.json")
    # Try 09_analysis.json first (new pipeline), fall back to 07_analysis.json (legacy)
    analysis_data = load_json_file(research_path / "09_analysis.json")
    if not analysis_data:
        analysis_data = load_json_file(research_path / "07_analysis.json")

    # Determine target name
    target = search_data.get("query", "Unknown Target")
    if financials_data.get("company", {}).get("name"):
        target = financials_data["company"]["name"]

    # Generate dossier
    if output_format == "markdown":
        content = generate_markdown_dossier(
            target=target,
            analysis=analysis_data,
            financials=financials_data,
            social=social_data,
            news=news_data,
            search=search_data
        )

        # Save markdown file
        output_file = research_path / "DOSSIER.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "target": target,
            "format": "markdown",
            "output_file": str(output_file),
            "content": content
        }

    else:  # JSON format
        return {
            "success": True,
            "target": target,
            "format": "json",
            "dossier": {
                "target": target,
                "generated_at": datetime.now().isoformat(),
                "key_facts": analysis_data.get("key_facts", {}),
                "financials": financials_data,
                "social": social_data,
                "news": news_data.get("articles", [])[:10],
                "analysis": analysis_data
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Generate research dossier")
    parser.add_argument("--research_dir", "-d", type=str, help="Research directory path")
    parser.add_argument("--format", "-f", type=str, default="markdown",
                       choices=["markdown", "json"], help="Output format")
    parser.add_argument("--stdin", action="store_true", help="Read JSON input from stdin")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")

    args = parser.parse_args()

    # Get input
    if args.stdin:
        input_data = json.load(sys.stdin)
        research_dir = input_data.get("research_dir", "")
        output_format = input_data.get("format", "markdown")
    else:
        research_dir = args.research_dir
        output_format = args.format

    if not research_dir:
        print("Error: No research directory provided", file=sys.stderr)
        sys.exit(1)

    # Generate dossier
    result = generate_dossier(research_dir, output_format)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            if output_format == "markdown" and result.get("content"):
                f.write(result["content"])
            else:
                json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        if output_format == "markdown" and result.get("content"):
            print(result["content"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
