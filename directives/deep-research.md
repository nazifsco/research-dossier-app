# Directive: Deep Research Agent

## Goal

Given a company, person, or topic, produce a comprehensive research dossier with all publicly available information compiled, analyzed, and presented in an actionable format.

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `target` | string | yes | Company name, person name, or topic to research |
| `target_type` | enum | yes | One of: `company`, `person`, `topic` |
| `depth` | enum | no | `quick` (5 min), `standard` (15 min), `deep` (30+ min). Default: `standard` |
| `focus_areas` | list | no | Specific areas to emphasize (e.g., "financials", "competitors", "leadership") |
| `output_format` | enum | no | `markdown`, `google_doc`, `google_sheet`. Default: `markdown` |

## Execution Steps

### Phase 1: Discovery (Checkpoint: `discovery`)

1. **Initialize research state**
   - Create checkpoint: `/checkpoint start deep-research-<target>`
   - Create working directory: `.tmp/research_<target>_<timestamp>/`

2. **Run initial web search**
   - Execute: `execution/search_web.py`
   - Inputs: `{"query": "<target>", "num_results": 20}`
   - Save to: `.tmp/research_<target>/01_search_results.json`
   - Extract key URLs to investigate

3. **Identify official sources**
   - Find official website, LinkedIn, Twitter/X, Crunchbase, news mentions
   - Save source list to: `.tmp/research_<target>/02_sources.json`

### Phase 2: Data Collection (Checkpoint: `collection`)

4. **Fetch and parse key webpages**
   - Execute: `execution/fetch_webpage.py` for each key URL
   - Save parsed content to: `.tmp/research_<target>/03_pages/`

5. **Fetch recent news**
   - Execute: `execution/fetch_news.py`
   - Inputs: `{"query": "<target>", "days": 90, "max_articles": 20}`
   - Save to: `.tmp/research_<target>/04_news.json`

6. **Fetch financial data** (if company and public)
   - Execute: `execution/fetch_financials.py`
   - Inputs: `{"ticker": "<ticker_symbol>"}`
   - Save to: `.tmp/research_<target>/05_financials.json`

7. **Fetch social presence**
   - Execute: `execution/fetch_social.py`
   - Inputs: `{"target": "<target>", "platforms": ["linkedin", "twitter"]}`
   - Save to: `.tmp/research_<target>/06_social.json`

8. **Fetch Wikipedia data**
   - Execute: `execution/fetch_wikipedia.py`
   - Inputs: `{"query": "<target>", "entity_type": "<target_type>"}`
   - Save to: `.tmp/research_<target>/07_wikipedia.json`
   - Extracts: summary, infobox data (founding date, HQ, key people), categories

9. **Fetch SEC EDGAR data** (if US public company)
   - Execute: `execution/fetch_sec_edgar.py`
   - Inputs: `{"ticker": "<ticker_symbol>"}` or `{"company": "<company_name>"}`
   - Save to: `.tmp/research_<target>/08_sec_edgar.json`
   - Extracts: official filings (10-K, 10-Q, 8-K), XBRL financial facts, company metadata

### Phase 3: Analysis (Checkpoint: `analysis`)

10. **Compile and analyze data**
    - Execute: `execution/analyze_research.py`
    - Inputs: `{"research_dir": ".tmp/research_<target>/"}`
    - Outputs:
      - Key facts and figures
      - Timeline of events
      - Strengths/weaknesses/opportunities/threats
      - Key people identified
      - Competitive landscape (if company)
    - Save to: `.tmp/research_<target>/09_analysis.json`

### Phase 4: Output Generation (Checkpoint: `output`)

11. **Generate dossier**
   - Execute: `execution/generate_dossier.py`
   - Inputs: `{"research_dir": ".tmp/research_<target>/", "format": "<output_format>"}`
   - Outputs:
     - Executive summary (1 paragraph)
     - Full dossier (structured sections)
     - Key data points (structured JSON)

12. **Export deliverable**
    - If `google_doc`: Execute `execution/export_to_gdoc.py`
    - If `google_sheet`: Execute `execution/export_to_gsheet.py`
    - If `markdown`: Save to `.tmp/research_<target>/DOSSIER.md`

13. **Complete checkpoint**
    - `/checkpoint complete`
    - Report deliverable location to user

## Outputs

| Name | Type | Destination |
|------|------|-------------|
| `dossier` | document | Google Doc or `.tmp/research_<target>/DOSSIER.md` |
| `raw_data` | folder | `.tmp/research_<target>/` (intermediate files) |
| `key_facts` | JSON | Structured data extracted for further use |

## Dossier Structure

```markdown
# Research Dossier: [Target Name]
Generated: [Date]

## Executive Summary
[1-2 paragraph overview]

## Key Facts
- Founded: [year]
- Headquarters: [location]
- Size: [employees/revenue]
- Industry: [industry]
- Key People: [names and roles]

## Overview
[Detailed description]

## Recent News & Developments
[Timeline of recent events]

## Financial Overview (if applicable)
[Revenue, funding, growth metrics]

## Competitive Landscape
[Key competitors and positioning]

## Online Presence
[Website, social media, sentiment]

## SWOT Analysis
- Strengths: ...
- Weaknesses: ...
- Opportunities: ...
- Threats: ...

## Key Contacts
[People identified with roles]

## Sources
[All URLs and sources used]
```

## Edge Cases

- **If target not found** → Expand search query, try variations (e.g., "OpenAI" vs "Open AI")
- **If website blocks scraping** → Use cached/archived versions, skip and note in dossier
- **If no financial data** → Note as "Private company" or "Data not available"
- **If rate limited** → Wait and retry (max 3 attempts with exponential backoff)
- **If ambiguous target** → Ask user for clarification (e.g., "Apple" - company or fruit?)

## Known Constraints

- Web search: ~20 requests/minute (DuckDuckGo) - may timeout, has HTML fallback
- News API: 100 requests/day on free tier (NewsAPI.org)
- News fallback: Google News RSS is more reliable than DuckDuckGo for news
- Webpage fetch: 2-second delay between requests to avoid blocks
- Financial data: Only available for public companies with ticker symbols
- Social data: Limited without API access (LinkedIn blocks scraping)
- Some sites (Crunchbase, ProductizedHQ) block automated scraping
- Wikipedia: Free, no rate limits for reasonable use. Best for established entities with Wikipedia pages
- SEC EDGAR: Free, only works for US public companies. Provides official financial data from XBRL filings

## Fallback Behavior (Annealed 2026-01-28)

Scripts now include automatic fallback mechanisms:

1. **search_web.py**: If DDGS fails → falls back to DuckDuckGo HTML scraping
2. **fetch_news.py**: If DDGS fails → falls back to Google News RSS feed
3. All scripts: Retry with exponential backoff (3 attempts, 2-30s delay)

If primary sources fail, check the `search_method` field in output to see which method succeeded.

## Environment Variables Required

```
NEWSAPI_KEY=xxx        # Optional: for news fetching (free tier available)
OPENAI_API_KEY=xxx     # Optional: for AI-powered analysis
ANTHROPIC_API_KEY=xxx  # Optional: for AI-powered analysis (alternative)
```

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Added Wikipedia and SEC EDGAR data sources (steps 8-9) |
| 2026-01-28 | Annealed: Added retry logic, fallbacks to search_web.py and fetch_news.py |
| 2026-01-28 | Created directive |
