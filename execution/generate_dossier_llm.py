#!/usr/bin/env python3
"""
LLM-Powered Dossier Generator
Uses OpenAI to synthesize research data into comprehensive dossiers.

Usage:
    python generate_dossier_llm.py --research_dir ".tmp/research_company/" --api_key "sk-..."

Output: Comprehensive markdown dossier with executive summary, SWOT, insights, etc.
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)


def load_json_file(filepath: str) -> dict:
    """Load a JSON file, return empty dict on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def compile_research_context(research_dir: str) -> str:
    """Compile all research data into a context string for the LLM."""
    research_path = Path(research_dir)
    context_parts = []

    # Load search results
    search_data = load_json_file(research_path / "01_search_results.json")
    if search_data.get("results"):
        context_parts.append("## SEARCH RESULTS\n")
        for i, result in enumerate(search_data["results"][:15], 1):
            context_parts.append(f"{i}. **{result.get('title', 'N/A')}**")
            context_parts.append(f"   URL: {result.get('url', 'N/A')}")
            context_parts.append(f"   {result.get('snippet', '')}\n")

    # Load scraped page content
    pages_dir = research_path / "03_pages"
    if pages_dir.exists():
        context_parts.append("\n## SCRAPED PAGE CONTENT\n")
        for page_file in sorted(pages_dir.glob("*.json"))[:8]:
            page_data = load_json_file(page_file)
            if page_data.get("success") and page_data.get("content"):
                title = page_data.get("title", "Unknown Page")
                url = page_data.get("url", "")
                content = page_data.get("content", "")[:4000]  # Limit per page
                context_parts.append(f"### {title}")
                context_parts.append(f"Source: {url}\n")
                context_parts.append(content[:4000])
                context_parts.append("\n---\n")

    # Load news
    news_data = load_json_file(research_path / "04_news.json")
    if news_data.get("articles"):
        context_parts.append("\n## NEWS ARTICLES\n")
        for article in news_data["articles"][:10]:
            context_parts.append(f"- **{article.get('title', 'N/A')}** ({article.get('date', 'N/A')})")
            context_parts.append(f"  Source: {article.get('source', 'N/A')}")
            context_parts.append(f"  {article.get('snippet', '')}\n")

    # Load financials
    financials_data = load_json_file(research_path / "05_financials.json")
    if financials_data.get("success"):
        context_parts.append("\n## FINANCIAL DATA\n")
        company = financials_data.get("company", {})
        fin = financials_data.get("financials", {})
        context_parts.append(f"- Company: {company.get('name', 'N/A')}")
        context_parts.append(f"- Sector: {company.get('sector', 'N/A')}")
        context_parts.append(f"- Industry: {company.get('industry', 'N/A')}")
        context_parts.append(f"- Employees: {company.get('employees', 'N/A')}")
        context_parts.append(f"- Market Cap: {fin.get('market_cap_formatted', 'N/A')}")
        context_parts.append(f"- Revenue: {fin.get('revenue_formatted', 'N/A')}")

    # Load social
    social_data = load_json_file(research_path / "06_social.json")
    if social_data.get("profiles"):
        context_parts.append("\n## SOCIAL MEDIA PRESENCE\n")
        for platform, data in social_data["profiles"].items():
            context_parts.append(f"- {platform}: {data.get('url', 'N/A')}")

    # Load Wikipedia
    wiki_data = load_json_file(research_path / "07_wikipedia.json")
    if wiki_data.get("success") and wiki_data.get("summary"):
        context_parts.append("\n## WIKIPEDIA\n")
        context_parts.append(wiki_data.get("summary", "")[:2000])

    return "\n".join(context_parts)


def generate_dossier_with_llm(
    target: str,
    target_type: str,
    context: str,
    api_key: str,
    model: str = "gpt-4o-mini"
) -> str:
    """Use OpenAI to generate a comprehensive dossier."""

    client = OpenAI(api_key=api_key)

    system_prompt = """You are an expert business intelligence analyst. Your task is to synthesize research data into a comprehensive, professional dossier.

Write in a clear, factual style. Include specific details, numbers, and quotes where available. Structure your analysis with clear sections.

Format your response as a well-structured Markdown document."""

    user_prompt = f"""Create a comprehensive research dossier for: **{target}** (Type: {target_type})

Based on the following research data, create a detailed dossier with these sections:

1. **Executive Summary** - 2-3 paragraph overview of the entity, what they do, their market position, and key highlights

2. **Key Facts** - Table format with: Name, Website, Founded, Headquarters, Leadership, Industry, Size/Employees, Funding (if available)

3. **Leadership Team** - Key executives with their roles and brief backgrounds (if found in data)

4. **Products/Services** - What they offer, their main value proposition

5. **Online Presence** - Social media, website, content channels with actual URLs

6. **Recent News & Developments** - Timeline of recent events, announcements, coverage

7. **Competitive Positioning** - Market position, differentiators, target market

8. **SWOT Analysis** -
   - Strengths (3-5 points based on evidence)
   - Weaknesses (3-5 points based on evidence)
   - Opportunities (3-5 points)
   - Threats (3-5 points)

9. **Sources** - List key sources used

IMPORTANT:
- Only include information that is supported by the research data
- If information is not available, note it as "Not found in research"
- Be specific - include actual numbers, dates, names, URLs
- Write professionally as if this will be shared with executives

---

RESEARCH DATA:

{context}

---

Generate the dossier now:"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.3  # Lower for more factual output
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"# Error Generating Dossier\n\nFailed to generate dossier: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Generate LLM-powered research dossier")
    parser.add_argument("--research_dir", "-d", type=str, required=True, help="Research directory path")
    parser.add_argument("--api_key", "-k", type=str, help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o-mini", help="OpenAI model to use")
    parser.add_argument("--target", "-t", type=str, help="Target name (auto-detected if not provided)")
    parser.add_argument("--target_type", type=str, default="company", help="Target type: company or person")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: DOSSIER.md in research dir)")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key required. Use --api_key or set OPENAI_API_KEY", file=sys.stderr)
        sys.exit(1)

    research_path = Path(args.research_dir)
    if not research_path.exists():
        print(f"Error: Research directory not found: {args.research_dir}", file=sys.stderr)
        sys.exit(1)

    # Auto-detect target from search data
    target = args.target
    if not target:
        search_data = load_json_file(research_path / "01_search_results.json")
        target = search_data.get("query", "Unknown Target")

    print(f"Generating dossier for: {target}", file=sys.stderr)
    print(f"Using model: {args.model}", file=sys.stderr)

    # Compile research context
    print("Compiling research data...", file=sys.stderr)
    context = compile_research_context(args.research_dir)

    # Generate dossier
    print("Generating dossier with LLM...", file=sys.stderr)
    dossier = generate_dossier_with_llm(
        target=target,
        target_type=args.target_type,
        context=context,
        api_key=api_key,
        model=args.model
    )

    # Add header and footer
    full_dossier = f"""# Research Dossier: {target}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Research Type:** {args.target_type.title()} Profile
**Analysis:** AI-Synthesized Report

---

{dossier}

---

*This dossier was generated using AI analysis of collected research data. Verify critical information from primary sources.*
"""

    # Save to file
    output_file = args.output or str(research_path / "DOSSIER.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_dossier)

    print(f"Dossier saved to: {output_file}", file=sys.stderr)

    # Output result as JSON
    result = {
        "success": True,
        "target": target,
        "output_file": output_file,
        "model": args.model
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
