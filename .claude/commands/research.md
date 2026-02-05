# /research

Run the Deep Research Agent to generate a comprehensive dossier on a target.

## Usage

```
/research <target>
/research OpenAI
/research "Elon Musk"
/research "artificial intelligence market"
```

## Instructions

### Step 1: Parse Input

Extract from user input:
- **target**: The company, person, or topic to research
- **target_type**: Infer from context (company/person/topic)
- **depth**: Default to "standard" unless user specifies "quick" or "deep"

### Step 2: Initialize

1. Create checkpoint: `/checkpoint start deep-research`
2. Create working directory: `.tmp/research_<target>_<timestamp>/`
3. Inform user: "Starting research on [target]..."

### Step 3: Execute Research Pipeline

Follow the directive at `directives/deep-research.md`:

1. **Discovery Phase**
   ```bash
   python execution/search_web.py --query "<target>" --num_results 20 --output .tmp/research_<target>/01_search_results.json
   ```

2. **Fetch News**
   ```bash
   python execution/fetch_news.py --query "<target>" --days 90 --output .tmp/research_<target>/04_news.json
   ```

3. **Fetch Key Webpages** (top 5 from search results)
   ```bash
   mkdir .tmp/research_<target>/03_pages/
   python execution/fetch_webpage.py --url "<url>" --output .tmp/research_<target>/03_pages/page_1.json
   # Repeat for top URLs, with 2s delay between requests
   ```

4. **Fetch Social Presence**
   ```bash
   python execution/fetch_social.py --target "<target>" --output .tmp/research_<target>/06_social.json
   ```

5. **Fetch Financials** (if company with known ticker)
   ```bash
   python execution/fetch_financials.py --ticker "<TICKER>" --output .tmp/research_<target>/05_financials.json
   ```

6. **Analyze All Data**
   ```bash
   python execution/analyze_research.py --research_dir ".tmp/research_<target>/" --output .tmp/research_<target>/07_analysis.json
   ```

7. **Generate Dossier**
   ```bash
   python execution/generate_dossier.py --research_dir ".tmp/research_<target>/" --format markdown
   ```

### Step 4: Deliver Results

1. Read the generated dossier from `.tmp/research_<target>/DOSSIER.md`
2. Present key findings to user:
   - Executive summary
   - Key facts
   - Recent news highlights
   - Overall sentiment
3. Provide path to full dossier
4. Complete checkpoint: `/checkpoint complete`

### Step 5: Handle Errors

If any step fails:
1. Record error with `/checkpoint fail "<error>"`
2. Attempt to continue with available data
3. Note missing sections in final dossier
4. Suggest `/anneal` if systematic fix needed

## Example Output

```
## Research Complete: OpenAI

**Executive Summary:** OpenAI is a leading AI research company...

**Key Facts:**
- Founded: 2015
- Employees: ~1,500
- Valuation: $80B+
- Key People: Sam Altman (CEO), Greg Brockman (President)

**Recent Developments:**
- 2024-01-15: Launched GPT-5...
- 2024-01-10: Partnership with Microsoft expanded...

**Sentiment:** Positive (0.65)

Full dossier saved to: .tmp/research_openai_20240128/DOSSIER.md
```

## Notes

- Research typically completes in 2-5 minutes depending on depth
- Financial data only available for public companies
- Social media discovery is limited to public profiles
- All data is saved for reference in `.tmp/research_<target>/`
