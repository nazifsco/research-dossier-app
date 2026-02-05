# /new-directive

Create a new directive following the standardized template.

## Instructions

1. Ask the user for:
   - Directive name (kebab-case, e.g., `scrape-website`)
   - Goal (one sentence describing success)
   - Required inputs (name, type, description for each)
   - Expected outputs (name, type, destination)
   - Any known constraints (API limits, required env vars)

2. Read the template from `directives/_template.md`

3. Create a new file at `directives/<name>.md` with the template filled in

4. If execution scripts are needed, ask if the user wants to:
   - Use an existing script (check `execution/manifest.json`)
   - Create a placeholder for a new script

5. Confirm creation and show the user where the file is located

## Example Usage

```
User: /new-directive
Agent: What should this directive be called? (use kebab-case, e.g., "fetch-company-data")
User: research-competitor
Agent: What's the goal? (one sentence describing what success looks like)
User: Gather public information about a competitor company and output a summary
Agent: [continues gathering inputs, then creates the directive]
```
