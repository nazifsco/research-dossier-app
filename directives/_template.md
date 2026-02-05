# Directive: [Name]

> Copy this template when creating new directives. Delete this line.

## Goal

[One sentence: what does success look like?]

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `example_input` | string | yes | Description of the input |

## Execution Steps

1. **Validate inputs** — Check all required inputs are present
2. **Step name** — Run `execution/script_name.py` with inputs
3. **Validate output** — Confirm output meets expected criteria

## Outputs

| Name | Type | Destination |
|------|------|-------------|
| `example_output` | object | Google Sheets / `.tmp/` / etc |

## Edge Cases

- **If X happens** → Do Y
- **If rate limited** → Wait 60s and retry (max 3 attempts)
- **If auth fails** → Ask user to refresh credentials

## Known Constraints

- API rate limit: X requests/minute
- Requires env vars: `API_KEY`, `SECRET`
- Typical runtime: ~30 seconds

## Changelog

| Date | Change |
|------|--------|
| YYYY-MM-DD | Created directive |
