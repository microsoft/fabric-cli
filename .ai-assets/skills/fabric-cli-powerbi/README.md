# Fabric CLI Power BI Skill

Skill for working with Power BI items (semantic models, reports, dashboards) using the Fabric CLI.

## When to Load

Load this skill when:
- Working with semantic models (datasets) — refresh, DAX, TMDL
- Managing Power BI reports — export, rebind, clone
- Querying data via DAX
- Managing gateways and data sources
- Troubleshooting refresh failures

## Prerequisites

- Load `fabric-cli-core` skill first
- User authenticated via `fab auth login`
- Access to workspace containing Power BI items

## Contents

| File | Description |
|------|-------------|
| [SKILL.md](./SKILL.md) | Main skill definition |
| [references/semantic-models.md](./references/semantic-models.md) | Semantic model operations |
| [references/reports.md](./references/reports.md) | Report operations |
| [references/refresh.md](./references/refresh.md) | Refresh operations and troubleshooting |
| [references/dax-queries.md](./references/dax-queries.md) | DAX query execution |
| [references/gateways.md](./references/gateways.md) | Gateway and data source management |

## Scripts

Automation scripts for Power BI tasks:

| Script | Description | Usage |
|--------|-------------|-------|
| `refresh_model.py` | Trigger and monitor semantic model refresh | `python scripts/refresh_model.py <model> [--wait]` |
| `list_refresh_history.py` | Show refresh history and failure details | `python scripts/list_refresh_history.py <model> [--last N]` |
| `rebind_report.py` | Rebind report to different semantic model | `python scripts/rebind_report.py <report> --model <new-model>` |
