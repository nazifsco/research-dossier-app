#!/usr/bin/env python3
"""
HTML Report Generator
Generates a visually appealing HTML report from research data that can be printed to PDF.

Usage:
    python generate_html_report.py --research_dir ".tmp/research_leftclick/"
    python generate_html_report.py --research_dir ".tmp/research_leftclick/" --output "report.html"

Output: Styled HTML file that can be opened in browser and printed to PDF
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from html import escape


# Color scheme matching the template
ACCENT_COLOR = "#E94B3C"  # Coral red
ACCENT_LIGHT = "#F5A59E"
TEXT_DARK = "#333333"
TEXT_LIGHT = "#666666"


def load_json_file(filepath: str) -> dict:
    """Load a JSON file, return empty dict on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def escape_html(text: str) -> str:
    """Safely escape HTML characters."""
    if text is None:
        return ""
    return escape(str(text))


def generate_html_report(research_dir: str, title: str = None) -> str:
    """
    Generate a styled HTML report from research data.

    Args:
        research_dir: Path to research directory
        title: Optional custom title

    Returns:
        HTML string
    """
    research_path = Path(research_dir)

    # Load all data files
    search_data = load_json_file(research_path / "01_search_results.json")
    news_data = load_json_file(research_path / "04_news.json")
    financials_data = load_json_file(research_path / "05_financials.json")
    social_data = load_json_file(research_path / "06_social.json")
    analysis_data = load_json_file(research_path / "07_analysis.json")

    # Load main page content if available
    main_page = {}
    pages_dir = research_path / "03_pages"
    if pages_dir.exists():
        for page_file in pages_dir.glob("*.json"):
            page_data = load_json_file(page_file)
            if page_data.get("success") and "main" in page_file.stem.lower():
                main_page = page_data
                break
            elif page_data.get("success") and not main_page:
                main_page = page_data

    # Determine target name and basic info
    target_name = title or search_data.get("query", "Research Target")
    if financials_data.get("company", {}).get("name"):
        target_name = financials_data["company"]["name"]

    # Extract key facts
    key_facts = analysis_data.get("key_facts", {})
    company_info = financials_data.get("company", {})

    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Dossier: {escape_html(target_name)}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            color: {TEXT_DARK};
            line-height: 1.6;
            background: #fff;
        }}

        .page {{
            width: 210mm;
            min-height: 297mm;
            padding: 20mm;
            margin: 0 auto 20px;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            position: relative;
            page-break-after: always;
        }}

        .page:last-child {{
            page-break-after: auto;
        }}

        /* Cover page */
        .cover-page {{
            display: flex;
            flex-direction: column;
            padding: 0;
            overflow: hidden;
        }}

        .cover-header {{
            display: flex;
            justify-content: space-between;
            padding: 20mm 20mm 10mm;
        }}

        .cover-brand {{
            font-weight: 600;
            font-size: 12px;
            letter-spacing: 1px;
        }}

        .cover-date {{
            font-size: 12px;
            color: {TEXT_LIGHT};
        }}

        .cover-content {{
            padding: 0 20mm;
            flex-grow: 1;
        }}

        .cover-title {{
            font-size: 48px;
            font-weight: 700;
            color: {ACCENT_COLOR};
            line-height: 1.1;
            margin-bottom: 20px;
        }}

        .cover-subtitle {{
            font-size: 18px;
            color: {TEXT_LIGHT};
            margin-bottom: 40px;
        }}

        .cover-meta {{
            display: flex;
            gap: 60px;
            margin-bottom: 40px;
        }}

        .cover-meta-item label {{
            display: block;
            font-size: 10px;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: {TEXT_LIGHT};
            margin-bottom: 4px;
        }}

        .cover-meta-item span {{
            font-weight: 500;
        }}

        .cover-graphic {{
            background: {ACCENT_COLOR};
            height: 45%;
            position: relative;
            overflow: hidden;
        }}

        .cover-graphic svg {{
            position: absolute;
            width: 100%;
            height: 100%;
            opacity: 0.3;
        }}

        /* Section headers */
        .section-header {{
            font-size: 10px;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: {TEXT_LIGHT};
            margin-bottom: 10px;
        }}

        h1 {{
            font-size: 36px;
            font-weight: 700;
            color: {ACCENT_COLOR};
            margin-bottom: 20px;
        }}

        h2 {{
            font-size: 24px;
            font-weight: 600;
            color: {ACCENT_COLOR};
            margin: 30px 0 15px;
        }}

        h3 {{
            font-size: 18px;
            font-weight: 600;
            margin: 20px 0 10px;
        }}

        p {{
            margin-bottom: 15px;
            color: {TEXT_DARK};
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        th {{
            background: {ACCENT_COLOR};
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 500;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}

        tr:nth-child(even) {{
            background: #f9f9f9;
        }}

        /* Key metric cards */
        .metric-cards {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}

        .metric-card {{
            background: #f8f8f8;
            padding: 20px;
            border-left: 4px solid {ACCENT_COLOR};
        }}

        .metric-card .value {{
            font-size: 28px;
            font-weight: 700;
            color: {ACCENT_COLOR};
        }}

        .metric-card .label {{
            font-size: 12px;
            color: {TEXT_LIGHT};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Lists */
        ul {{
            margin: 15px 0;
            padding-left: 20px;
        }}

        li {{
            margin-bottom: 8px;
        }}

        /* SWOT grid */
        .swot-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }}

        .swot-item {{
            padding: 15px;
            background: #f8f8f8;
        }}

        .swot-item h4 {{
            color: {ACCENT_COLOR};
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .swot-item ul {{
            font-size: 14px;
            margin: 0;
            padding-left: 18px;
        }}

        /* Social links */
        .social-links {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }}

        .social-link {{
            background: {ACCENT_COLOR};
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
        }}

        /* Sidebar accent */
        .sidebar-accent {{
            position: absolute;
            right: 0;
            top: 0;
            width: 30mm;
            height: 100%;
            background: {ACCENT_COLOR};
            overflow: hidden;
        }}

        .sidebar-accent svg {{
            position: absolute;
            width: 100%;
            height: 100%;
            opacity: 0.3;
        }}

        /* Page footer */
        .page-footer {{
            position: absolute;
            bottom: 15mm;
            left: 20mm;
            font-size: 10px;
            color: {TEXT_LIGHT};
        }}

        /* Print styles */
        @media print {{
            body {{
                background: white;
            }}
            .page {{
                box-shadow: none;
                margin: 0;
                width: 100%;
                min-height: 100vh;
            }}
        }}

        /* Sources */
        .sources {{
            font-size: 13px;
        }}

        .sources a {{
            color: {ACCENT_COLOR};
            text-decoration: none;
        }}

        .sources a:hover {{
            text-decoration: underline;
        }}

        /* Timeline */
        .timeline {{
            margin: 20px 0;
        }}

        .timeline-item {{
            display: flex;
            margin-bottom: 15px;
            padding-left: 20px;
            border-left: 2px solid {ACCENT_LIGHT};
        }}

        .timeline-date {{
            font-weight: 600;
            color: {ACCENT_COLOR};
            min-width: 100px;
        }}

        .timeline-content {{
            flex: 1;
        }}
    </style>
</head>
<body>
'''

    # Cover page
    html += f'''
    <div class="page cover-page">
        <div class="cover-header">
            <div class="cover-brand">RESEARCH DOSSIER</div>
            <div class="cover-date">{datetime.now().strftime("%B %Y").upper()}</div>
        </div>
        <div class="cover-content">
            <h1 class="cover-title">{escape_html(target_name)}</h1>
            <p class="cover-subtitle">{escape_html(main_page.get("description", company_info.get("description", "Comprehensive research and analysis")[:200]))}</p>
            <div class="cover-meta">
                <div class="cover-meta-item">
                    <label>Generated</label>
                    <span>{datetime.now().strftime("%Y-%m-%d")}</span>
                </div>
                <div class="cover-meta-item">
                    <label>Data Sources</label>
                    <span>{analysis_data.get("data_sources", {}).get("search_results", 0)} search results, {analysis_data.get("data_sources", {}).get("news_articles", 0)} articles</span>
                </div>
            </div>
        </div>
        <div class="cover-graphic">
            <svg viewBox="0 0 400 200" preserveAspectRatio="none">
                <path d="M0,100 L50,50 L100,80 L150,30 L200,90 L250,40 L300,100 L350,60 L400,100 L400,200 L0,200 Z" fill="white" opacity="0.1"/>
                <path d="M0,150 L80,100 L160,130 L240,80 L320,140 L400,90 L400,200 L0,200 Z" fill="white" opacity="0.1"/>
            </svg>
        </div>
    </div>
'''

    # At a Glance page
    html += f'''
    <div class="page" style="padding-right: 50mm;">
        <div class="sidebar-accent">
            <svg viewBox="0 0 100 300" preserveAspectRatio="none">
                <path d="M0,0 L100,50 L50,100 L100,150 L0,200 L80,250 L0,300" fill="none" stroke="white" stroke-width="2" opacity="0.5"/>
            </svg>
        </div>
        <p class="section-header">RESEARCH DOSSIER</p>
        <h1>{escape_html(target_name)}<br>At A Glance</h1>

        <div class="metric-cards">
'''

    # Add key metrics
    if company_info.get("employees"):
        html += f'''
            <div class="metric-card">
                <div class="value">{company_info.get("employees"):,}</div>
                <div class="label">Employees</div>
            </div>
'''

    if financials_data.get("financials", {}).get("market_cap_formatted"):
        html += f'''
            <div class="metric-card">
                <div class="value">{escape_html(financials_data["financials"]["market_cap_formatted"])}</div>
                <div class="label">Market Cap</div>
            </div>
'''

    if social_data.get("presence_score"):
        html += f'''
            <div class="metric-card">
                <div class="value">{social_data.get("presence_score")}%</div>
                <div class="label">Social Presence Score</div>
            </div>
'''

    if analysis_data.get("sentiment", {}).get("sentiment"):
        sentiment = analysis_data["sentiment"]
        html += f'''
            <div class="metric-card">
                <div class="value">{sentiment.get("sentiment", "N/A").capitalize()}</div>
                <div class="label">Overall Sentiment</div>
            </div>
'''

    html += '''
        </div>

        <h2>Key Facts</h2>
        <table>
            <tr>
                <th>Attribute</th>
                <th>Value</th>
            </tr>
'''

    # Key facts table
    facts = [
        ("Company", company_info.get("name") or target_name),
        ("Industry", company_info.get("industry")),
        ("Sector", company_info.get("sector")),
        ("Website", company_info.get("website")),
        ("Country", company_info.get("country")),
    ]

    for label, value in facts:
        if value:
            html += f'''
            <tr>
                <td><strong>{escape_html(label)}</strong></td>
                <td>{escape_html(str(value))}</td>
            </tr>
'''

    html += '''
        </table>
        <div class="page-footer">RESEARCH DOSSIER</div>
    </div>
'''

    # Executive Summary page
    description = company_info.get("description") or main_page.get("content", "")[:1500]
    if description:
        html += f'''
    <div class="page" style="padding-right: 50mm;">
        <div class="sidebar-accent">
            <svg viewBox="0 0 100 300" preserveAspectRatio="none">
                <path d="M50,0 L100,80 L30,120 L100,180 L0,250 L60,300" fill="none" stroke="white" stroke-width="2" opacity="0.5"/>
            </svg>
        </div>
        <p class="section-header">RESEARCH DOSSIER</p>
        <h1>Executive<br>Summary</h1>
        <p>{escape_html(description[:2000])}</p>
        <div class="page-footer">RESEARCH DOSSIER</div>
    </div>
'''

    # Online Presence page
    profiles = social_data.get("profiles", {})
    if profiles:
        html += f'''
    <div class="page">
        <p class="section-header">RESEARCH DOSSIER</p>
        <h1>Online Presence</h1>

        <div class="social-links">
'''
        for platform, data in profiles.items():
            platform_name = platform.replace("_", " ").title()
            url = data.get("url", "#")
            html += f'            <a href="{escape_html(url)}" class="social-link" target="_blank">{escape_html(platform_name)}</a>\n'

        html += '''
        </div>

        <table>
            <tr>
                <th>Platform</th>
                <th>URL</th>
            </tr>
'''
        for platform, data in profiles.items():
            html += f'''
            <tr>
                <td><strong>{escape_html(platform.replace("_", " ").title())}</strong></td>
                <td><a href="{escape_html(data.get("url", ""))}" target="_blank">{escape_html(data.get("url", "N/A"))}</a></td>
            </tr>
'''
        html += '''
        </table>
        <div class="page-footer">RESEARCH DOSSIER</div>
    </div>
'''

    # SWOT Analysis page
    swot = analysis_data.get("swot", {})
    if any(swot.get(k) for k in ["strengths", "weaknesses", "opportunities", "threats"]):
        html += f'''
    <div class="page">
        <p class="section-header">RESEARCH DOSSIER</p>
        <h1>SWOT Analysis</h1>

        <div class="swot-grid">
            <div class="swot-item">
                <h4>Strengths</h4>
                <ul>
'''
        for item in swot.get("strengths", []) or ["No data"]:
            html += f'                    <li>{escape_html(item)}</li>\n'
        html += '''
                </ul>
            </div>
            <div class="swot-item">
                <h4>Weaknesses</h4>
                <ul>
'''
        for item in swot.get("weaknesses", []) or ["No data"]:
            html += f'                    <li>{escape_html(item)}</li>\n'
        html += '''
                </ul>
            </div>
            <div class="swot-item">
                <h4>Opportunities</h4>
                <ul>
'''
        for item in swot.get("opportunities", []) or ["No data"]:
            html += f'                    <li>{escape_html(item)}</li>\n'
        html += '''
                </ul>
            </div>
            <div class="swot-item">
                <h4>Threats</h4>
                <ul>
'''
        for item in swot.get("threats", []) or ["No data"]:
            html += f'                    <li>{escape_html(item)}</li>\n'
        html += '''
                </ul>
            </div>
        </div>
        <div class="page-footer">RESEARCH DOSSIER</div>
    </div>
'''

    # News & Timeline page
    articles = news_data.get("articles", [])[:10]
    if articles:
        html += f'''
    <div class="page">
        <p class="section-header">RESEARCH DOSSIER</p>
        <h1>Recent News</h1>

        <div class="timeline">
'''
        for article in articles:
            date = article.get("date", "")[:10] if article.get("date") else "N/A"
            title = article.get("title", "Untitled")
            source = article.get("source", "")
            html += f'''
            <div class="timeline-item">
                <div class="timeline-date">{escape_html(date)}</div>
                <div class="timeline-content">
                    <strong>{escape_html(title)}</strong>
                    {f'<br><small>{escape_html(source)}</small>' if source else ''}
                </div>
            </div>
'''
        html += '''
        </div>
        <div class="page-footer">RESEARCH DOSSIER</div>
    </div>
'''

    # Sources page
    sources = search_data.get("results", [])
    if sources:
        html += f'''
    <div class="page">
        <p class="section-header">RESEARCH DOSSIER</p>
        <h1>Sources</h1>

        <div class="sources">
            <ol>
'''
        for source in sources[:15]:
            title = source.get("title", "Untitled")
            url = source.get("url", "#")
            html += f'                <li><a href="{escape_html(url)}" target="_blank">{escape_html(title)}</a></li>\n'
        html += '''
            </ol>
        </div>

        <p style="margin-top: 40px; font-size: 13px; color: #666;">
            <em>This report was automatically generated using the Deep Research Agent.
            Verify critical information from primary sources.</em>
        </p>
        <div class="page-footer">RESEARCH DOSSIER</div>
    </div>
'''

    html += '''
</body>
</html>
'''

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML research report")
    parser.add_argument("--research_dir", "-d", type=str, required=True, help="Research directory path")
    parser.add_argument("--output", "-o", type=str, help="Output HTML file path")
    parser.add_argument("--title", "-t", type=str, help="Custom report title")

    args = parser.parse_args()

    # Generate HTML
    html = generate_html_report(args.research_dir, args.title)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        research_path = Path(args.research_dir)
        output_path = research_path / "REPORT.html"

    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {output_path}")
    print(f"Open in browser and use Print > Save as PDF for best results")


if __name__ == "__main__":
    main()
