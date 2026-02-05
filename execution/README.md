# Execution Scripts

Deterministic Python scripts that do the actual work.

## Adding a New Script

1. Create your script in this directory (e.g., `my_script.py`)
2. Register it in `manifest.json`:

```json
{
  "scripts": {
    "my_script": {
      "file": "my_script.py",
      "description": "What this script does",
      "inputs": {
        "param1": "string",
        "param2": "number"
      },
      "outputs": {
        "result": "object"
      },
      "requires_env": ["API_KEY"],
      "cost": "free|paid",
      "idempotent": true
    }
  }
}
```

## Manifest Fields

| Field | Required | Description |
|-------|----------|-------------|
| `file` | yes | Script filename |
| `description` | yes | What the script does |
| `inputs` | yes | Input parameters and their types |
| `outputs` | yes | Output structure |
| `requires_env` | no | Environment variables needed |
| `cost` | no | "free" or "paid" (affects auto-retry behavior) |
| `idempotent` | no | Can be safely re-run without side effects |

## Script Standards

- All scripts should be runnable standalone for testing
- Accept inputs via command line args or stdin JSON
- Output results to stdout as JSON
- Exit code 0 on success, non-zero on failure
- Log errors to stderr
