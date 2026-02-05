# State & Checkpointing

This directory stores workflow state for resumable multi-step operations.

## How It Works

When running a multi-step directive, the agent creates a state file:

```
state/
  workflow_<name>_<timestamp>.json
```

## State File Structure

```json
{
  "workflow": "directive_name",
  "started_at": "2024-01-28T10:00:00Z",
  "updated_at": "2024-01-28T10:05:00Z",
  "status": "in_progress",
  "total_steps": 5,
  "current_step": 3,
  "completed_steps": [
    {
      "step": 1,
      "name": "Fetch data",
      "completed_at": "2024-01-28T10:01:00Z",
      "output_file": ".tmp/step1_data.json"
    },
    {
      "step": 2,
      "name": "Process data",
      "completed_at": "2024-01-28T10:03:00Z",
      "output_file": ".tmp/step2_processed.json"
    }
  ],
  "failed_step": null,
  "error": null
}
```

## Resumption

If a workflow fails, the agent can:

1. Read the state file
2. Identify the last successful step
3. Resume from the next step
4. Skip re-running completed steps (outputs already in `.tmp/`)

## Cleanup

State files can be deleted after successful workflow completion, or kept for audit purposes.

To clean up old state files:
```bash
# Delete state files older than 7 days
find state/ -name "workflow_*.json" -mtime +7 -delete
```

## Agent Instructions

When starting a multi-step workflow:
1. Create a state file in `state/`
2. Update it after each step completes
3. On error, record the failure and stop
4. On resume, read state and continue from last checkpoint
