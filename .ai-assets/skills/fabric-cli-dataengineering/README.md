# Fabric CLI Data Engineering Skill

Task-specific instructions for AI agents helping users with Microsoft Fabric data engineering operations.

## Overview

This skill provides guidance for:

- **Lakehouse & Warehouse** — Creating and managing data stores
- **Table Operations** — Load, optimize, vacuum Delta tables
- **Shortcuts** — Data federation with OneLake, ADLS, S3
- **Medallion Architecture** — Bronze/silver/gold layer patterns
- **Spark Jobs** — Notebook and pipeline execution

## When to Load

Load this skill when the user's task involves:

- Creating lakehouses or warehouses
- Managing files in OneLake
- Loading data into Delta tables
- Optimizing table performance
- Creating data shortcuts
- Running Spark notebooks or jobs
- Building ETL/ELT pipelines
- Implementing medallion architecture

## Files

| File | Description |
|------|-------------|
| [SKILL.md](./SKILL.md) | Main skill definition (load this) |
| [references/](./references/) | Detailed reference documentation |

## Scripts

Automation scripts for data engineering tasks:

| Script | Description | Usage |
|--------|-------------|-------|
| `setup_medallion.py` | Create medallion architecture (bronze/silver/gold) | `python scripts/setup_medallion.py <workspace> [--prefix NAME]` |
| `optimize_tables.py` | Run optimization on lakehouse tables | `python scripts/optimize_tables.py <lakehouse> [--vorder]` |
| `validate_shortcuts.py` | Verify all shortcuts are accessible | `python scripts/validate_shortcuts.py <lakehouse>` |

## Quick Reference

### Common Commands

```bash
# Create lakehouse
fab mkdir "Workspace.Workspace/DataLake.Lakehouse"

# Upload files
fab cp ./data.csv "Workspace.Workspace/LH.Lakehouse/Files/raw/"

# Load table
fab table load "Workspace.Workspace/LH.Lakehouse/Tables/customers" \
  --file "Workspace.Workspace/LH.Lakehouse/Files/raw/customers"

# Optimize table
fab table optimize "Workspace.Workspace/LH.Lakehouse/Tables/sales" --vorder

# Run notebook
fab job run "Workspace.Workspace/ETL.Notebook" --timeout 600
```

## Dependencies

- Requires `fabric-cli-core` skill loaded first
- Contributor or higher role for data operations
- Appropriate capacity for Spark workloads

## References

- [Lakehouse Overview](https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview)
- [Delta Lake in Fabric](https://learn.microsoft.com/fabric/data-engineering/delta-lake-interoperability)
- [OneLake Shortcuts](https://learn.microsoft.com/fabric/onelake/onelake-shortcuts)
