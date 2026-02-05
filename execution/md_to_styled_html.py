#!/usr/bin/env python3
"""
Markdown to Styled HTML Converter
Converts DOSSIER.md to a professionally styled HTML report for client delivery.

Usage:
    python md_to_styled_html.py --input ".tmp/research_leftclick/DOSSIER.md"
    python md_to_styled_html.py --input ".tmp/research_leftclick/DOSSIER.md" --output "report.html"

Output: Styled HTML file ready for client presentation (print to PDF from browser)

This is the PRODUCTION script for generating client deliverables.
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from html import escape


# Design tokens matching the professional template
STYLES = {
    "accent": "#E94B3C",
    "accent_light": "#F5A59E",
    "accent_dark": "#C43E32",
    "text_dark": "#1a1a1a",
    "text_medium": "#4a4a4a",
    "text_light": "#6a6a6a",
    "bg_light": "#f8f8f8",
    "border": "#e0e0e0",
}


def parse_markdown(md_content: str) -> dict:
    """
    Parse markdown content into structured sections.

    Returns dict with:
    - title: Main title
    - subtitle: First paragraph or description
    - sections: List of {level, title, content} dicts
    - metadata: Extracted metadata (Generated date, etc.)
    """
    lines = md_content.split('\n')

    result = {
        "title": "",
        "subtitle": "",
        "sections": [],
        "metadata": {},
        "raw": md_content
    }

    current_section = None
    current_content = []

    for line in lines:
        # Main title (# )
        if line.startswith('# ') and not result["title"]:
            result["title"] = line[2:].strip()
            continue

        # Extract metadata from **Key:** Value patterns at top
        meta_match = re.match(r'\*\*([^*]+)\*\*:\s*(.+)', line)
        if meta_match and not current_section:
            key = meta_match.group(1).lower().replace(" ", "_")
            result["metadata"][key] = meta_match.group(2).strip()
            continue

        # H2 sections (## )
        if line.startswith('## '):
            # Save previous section
            if current_section:
                current_section["content"] = '\n'.join(current_content).strip()
                result["sections"].append(current_section)

            current_section = {
                "level": 2,
                "title": line[3:].strip(),
                "content": ""
            }
            current_content = []
            continue

        # H3 subsections (### )
        if line.startswith('### '):
            if current_section:
                current_content.append(f'<h3>{escape(line[4:].strip())}</h3>')
            continue

        # Collect content
        if current_section:
            current_content.append(line)

    # Don't forget last section
    if current_section:
        current_section["content"] = '\n'.join(current_content).strip()
        result["sections"].append(current_section)

    return result


def md_to_html_content(md_text: str) -> str:
    """Convert markdown text to HTML."""
    html = escape(md_text)

    # Already escaped, now convert markdown syntax

    # Bold **text**
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)

    # Italic *text*
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)

    # Links [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html)

    # Inline code `code`
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Headers that were added as HTML
    html = re.sub(r'&lt;h3&gt;(.+?)&lt;/h3&gt;', r'<h3>\1</h3>', html)

    # Tables
    if '|' in html:
        html = convert_md_table(html)

    # Bullet lists
    lines = html.split('\n')
    in_list = False
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            new_lines.append(f'<li>{stripped[2:]}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            # Paragraphs
            if stripped and not stripped.startswith('<'):
                new_lines.append(f'<p>{stripped}</p>')
            elif stripped:
                new_lines.append(line)

    if in_list:
        new_lines.append('</ul>')

    return '\n'.join(new_lines)


def convert_md_table(html: str) -> str:
    """Convert markdown tables to HTML tables."""
    lines = html.split('\n')
    result = []
    in_table = False
    header_done = False

    for line in lines:
        stripped = line.strip()

        if '|' in stripped and stripped.startswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]

            if not in_table:
                result.append('<table>')
                in_table = True
                header_done = False

            # Skip separator row
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue

            if not header_done:
                result.append('<thead><tr>')
                for cell in cells:
                    result.append(f'<th>{cell}</th>')
                result.append('</tr></thead><tbody>')
                header_done = True
            else:
                result.append('<tr>')
                for cell in cells:
                    result.append(f'<td>{cell}</td>')
                result.append('</tr>')
        else:
            if in_table:
                result.append('</tbody></table>')
                in_table = False
                header_done = False
            result.append(line)

    if in_table:
        result.append('</tbody></table>')

    return '\n'.join(result)


def generate_styled_html(parsed: dict) -> str:
    """Generate the full styled HTML document."""

    title = parsed["title"].replace("Research Dossier: ", "")
    generated = parsed["metadata"].get("generated", datetime.now().strftime("%Y-%m-%d"))

    # Find executive summary for subtitle
    subtitle = ""
    for section in parsed["sections"]:
        if "summary" in section["title"].lower():
            # Get first paragraph
            content = section["content"]
            first_para = content.split('\n\n')[0] if '\n\n' in content else content
            subtitle = first_para.replace('**', '').replace('*', '')[:200]
            break

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Dossier: {escape(title)}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {{
            --accent: {STYLES["accent"]};
            --accent-light: {STYLES["accent_light"]};
            --accent-dark: {STYLES["accent_dark"]};
            --text-dark: {STYLES["text_dark"]};
            --text-medium: {STYLES["text_medium"]};
            --text-light: {STYLES["text_light"]};
            --bg-light: {STYLES["bg_light"]};
            --border: {STYLES["border"]};
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-dark);
            line-height: 1.7;
            background: #f0f0f0;
            font-size: 14px;
        }}

        .document {{
            max-width: 210mm;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 30px rgba(0,0,0,0.1);
        }}

        /* Cover Page */
        .cover {{
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }}

        .cover-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 30px 40px;
        }}

        .cover-brand {{
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        .cover-date {{
            font-size: 11px;
            letter-spacing: 1px;
            color: var(--text-light);
        }}

        .cover-body {{
            flex: 1;
            padding: 40px 40px 60px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .cover-title {{
            font-size: 52px;
            font-weight: 800;
            color: var(--accent);
            line-height: 1.1;
            margin-bottom: 24px;
            letter-spacing: -1px;
        }}

        .cover-subtitle {{
            font-size: 18px;
            color: var(--text-medium);
            line-height: 1.6;
            max-width: 500px;
        }}

        .cover-graphic {{
            height: 40vh;
            background: var(--accent);
            position: relative;
            overflow: hidden;
        }}

        .cover-graphic::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background:
                linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.1) 40%, rgba(255,255,255,0.1) 60%, transparent 60%),
                linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.05) 30%, rgba(255,255,255,0.05) 70%, transparent 70%);
        }}

        .geo-lines {{
            position: absolute;
            width: 100%;
            height: 100%;
            opacity: 0.3;
        }}

        .geo-lines path {{
            fill: none;
            stroke: white;
            stroke-width: 1.5;
        }}

        /* Content Pages */
        .page {{
            padding: 50px 40px 70px;
            min-height: 100vh;
            position: relative;
            page-break-after: always;
        }}

        .page:last-child {{
            page-break-after: auto;
        }}

        .page-header {{
            font-size: 10px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-light);
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }}

        .page-title {{
            font-size: 36px;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 30px;
            line-height: 1.2;
        }}

        .page-footer {{
            position: absolute;
            bottom: 30px;
            left: 40px;
            right: 40px;
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: var(--text-light);
            padding-top: 15px;
            border-top: 1px solid var(--border);
        }}

        /* Typography */
        h2 {{
            font-size: 28px;
            font-weight: 700;
            color: var(--accent);
            margin: 40px 0 20px;
            line-height: 1.3;
        }}

        h3 {{
            font-size: 18px;
            font-weight: 600;
            color: var(--text-dark);
            margin: 25px 0 12px;
        }}

        p {{
            margin-bottom: 16px;
            color: var(--text-medium);
        }}

        strong {{
            color: var(--text-dark);
            font-weight: 600;
        }}

        a {{
            color: var(--accent);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        code {{
            background: var(--bg-light);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 13px;
        }}

        /* Lists */
        ul {{
            margin: 16px 0;
            padding-left: 24px;
        }}

        li {{
            margin-bottom: 10px;
            color: var(--text-medium);
        }}

        li::marker {{
            color: var(--accent);
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            font-size: 13px;
        }}

        thead {{
            background: var(--accent);
        }}

        th {{
            color: white;
            font-weight: 600;
            text-align: left;
            padding: 14px 16px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            color: var(--text-medium);
        }}

        tr:nth-child(even) {{
            background: var(--bg-light);
        }}

        /* Section styling */
        .section {{
            margin-bottom: 40px;
        }}

        .section-divider {{
            height: 4px;
            background: var(--accent);
            width: 60px;
            margin: 40px 0;
        }}

        /* Accent sidebar for some pages */
        .with-sidebar {{
            padding-right: 80px;
            position: relative;
        }}

        .with-sidebar::after {{
            content: '';
            position: absolute;
            right: 0;
            top: 0;
            width: 40px;
            height: 100%;
            background: var(--accent);
        }}

        /* Print optimization */
        @media print {{
            body {{
                background: white;
            }}

            .document {{
                box-shadow: none;
                max-width: 100%;
            }}

            .page {{
                min-height: auto;
                page-break-inside: avoid;
            }}

            .cover {{
                min-height: auto;
                height: 100vh;
            }}

            .cover-graphic {{
                height: 35vh;
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}

            thead {{
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}
        }}

        /* Horizontal rule */
        hr {{
            border: none;
            height: 1px;
            background: var(--border);
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="document">
        <!-- Cover Page -->
        <div class="cover">
            <div class="cover-header">
                <div class="cover-brand">Research Dossier</div>
                <div class="cover-date">{datetime.now().strftime("%B %Y").upper()}</div>
            </div>
            <div class="cover-body">
                <h1 class="cover-title">{escape(title)}</h1>
                <p class="cover-subtitle">{escape(subtitle)}</p>
            </div>
            <div class="cover-graphic">
                <svg class="geo-lines" viewBox="0 0 800 400" preserveAspectRatio="none">
                    <path d="M0,200 L100,150 L200,220 L300,100 L400,180 L500,80 L600,200 L700,120 L800,200"/>
                    <path d="M0,300 L150,250 L300,320 L450,200 L600,280 L750,180 L800,250"/>
                    <path d="M0,100 L200,50 L400,150 L600,30 L800,100"/>
                </svg>
            </div>
        </div>
'''

    # Generate content pages
    page_num = 2
    for i, section in enumerate(parsed["sections"]):
        section_title = section["title"]
        section_content = md_to_html_content(section["content"])

        # Skip empty sections
        if not section_content.strip():
            continue

        html += f'''
        <!-- {section_title} -->
        <div class="page">
            <div class="page-header">RESEARCH DOSSIER</div>
            <h1 class="page-title">{escape(section_title)}</h1>
            <div class="section">
                {section_content}
            </div>
            <div class="page-footer">
                <span>{escape(title)}</span>
                <span>Page {page_num}</span>
            </div>
        </div>
'''
        page_num += 1

    html += '''
    </div>
</body>
</html>
'''

    return html


def convert_md_to_html(input_path: str, output_path: str = None) -> str:
    """
    Main conversion function.

    Args:
        input_path: Path to DOSSIER.md
        output_path: Optional output path (defaults to same dir as REPORT.html)

    Returns:
        Path to generated HTML file
    """
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read markdown
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Parse and convert
    parsed = parse_markdown(md_content)
    html = generate_styled_html(parsed)

    # Determine output path
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = input_file.parent / "REPORT.html"

    # Write HTML
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)

    return str(out_file)


def main():
    parser = argparse.ArgumentParser(
        description="Convert DOSSIER.md to styled HTML report"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to DOSSIER.md file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output HTML path (default: REPORT.html in same directory)"
    )

    args = parser.parse_args()

    try:
        output = convert_md_to_html(args.input, args.output)
        print(f"Report generated: {output}")
        print("Open in browser and Print > Save as PDF for client delivery")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
