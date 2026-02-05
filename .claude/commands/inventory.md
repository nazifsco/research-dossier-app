# /inventory

List all available directives and execution scripts in the system.

## Instructions

1. **Read execution manifest**
   - Load `execution/manifest.json`
   - List all registered scripts with their descriptions, inputs, and outputs

2. **Scan directives**
   - List all `.md` files in `directives/` (exclude `_template.md`)
   - For each directive, extract:
     - Name (from filename)
     - Goal (from ## Goal section)
     - Status (has all required scripts? check against manifest)

3. **Check for orphans**
   - Scripts in `execution/` not in manifest
   - Scripts referenced in directives but missing from `execution/`

4. **Output format**

```
## Execution Scripts (from manifest)
| Script | Description | Inputs | Outputs |
|--------|-------------|--------|---------|
| ... | ... | ... | ... |

## Directives
| Directive | Goal | Status |
|-----------|------|--------|
| ... | ... | Ready / Missing scripts |

## Warnings
- Script `x.py` exists but not in manifest
- Directive `y.md` references missing script `z.py`
```

## Usage

Run `/inventory` anytime to understand what tools and workflows are available in the system.
