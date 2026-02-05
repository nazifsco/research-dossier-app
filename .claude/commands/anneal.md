# /anneal

Guide through the self-annealing process after an error occurs.

## When to Use

Run `/anneal` after any execution script fails or produces unexpected results.

## Instructions

### Step 1: Diagnose

1. Ask: "What script failed and what was the error?"
2. Read the script from `execution/`
3. Identify the root cause:
   - API error (rate limit, auth, endpoint change)
   - Data format issue
   - Missing dependency
   - Logic error

### Step 2: Fix

1. Propose a fix to the script
2. If the fix involves paid API calls or credits, **ask user permission first**
3. Apply the fix to the script

### Step 3: Test

1. Run the script with test inputs
2. Verify it succeeds
3. If it fails again, return to Step 1

### Step 4: Update Manifest

1. If the fix changed inputs/outputs, update `execution/manifest.json`
2. Add any new environment variables to the manifest entry

### Step 5: Update Directive

1. Find the directive that uses this script
2. Add what you learned to the appropriate section:
   - **Edge Cases**: New failure modes discovered
   - **Known Constraints**: API limits, timing, etc.
   - **Changelog**: Record the fix

### Step 6: Confirm

Output a summary:

```
## Anneal Complete

**Script:** execution/scrape_website.py
**Issue:** Rate limit exceeded after 100 requests
**Fix:** Added exponential backoff with max 3 retries
**Directive updated:** directives/scrape-website.md
**New constraint added:** API limit 100 req/min, backoff implemented

System is now stronger.
```

## Example Flow

```
User: /anneal
Agent: What script failed and what was the error?
User: scrape_website.py got a 429 error
Agent: [reads script, identifies missing rate limiting]
Agent: I'll add exponential backoff. This doesn't use paid credits, proceeding...
Agent: [fixes script, tests, updates directive]
Agent: Anneal complete. Added rate limiting with 60s max backoff.
```
