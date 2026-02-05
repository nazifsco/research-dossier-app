# /checkpoint

Manage workflow state for resumable multi-step operations.

## Subcommands

### /checkpoint start <workflow-name>

Create a new checkpoint for a workflow:

1. Generate state file: `state/workflow_<name>_<timestamp>.json`
2. Initialize with:
   - workflow name
   - start time
   - status: "in_progress"
   - empty completed_steps array

### /checkpoint update <step-number> <step-name>

Mark a step as completed:

1. Find the active state file for current workflow
2. Add step to completed_steps with timestamp
3. Update current_step number
4. Save intermediate output path if provided

### /checkpoint fail <error-message>

Record a failure:

1. Set status to "failed"
2. Record failed_step number
3. Record error message
4. Do NOT delete the state file (needed for resume)

### /checkpoint resume

Resume a failed workflow:

1. List all state files with status "failed" or "in_progress"
2. Ask user which to resume (if multiple)
3. Load the state file
4. Report last successful step and what's next
5. Continue execution from next step

### /checkpoint complete

Mark workflow as successfully completed:

1. Set status to "completed"
2. Record completion timestamp
3. Optionally archive or delete the state file

### /checkpoint list

Show all workflow states:

```
| Workflow | Status | Progress | Last Updated |
|----------|--------|----------|--------------|
| research-competitor | in_progress | 3/5 | 10 min ago |
| scrape-data | failed | 2/4 | 1 hour ago |
```

## Usage Examples

```
/checkpoint start research-competitor
/checkpoint update 1 "Fetched company data"
/checkpoint update 2 "Processed financials"
/checkpoint fail "API rate limit exceeded"
... later ...
/checkpoint resume
/checkpoint update 3 "Completed analysis"
/checkpoint complete
```
