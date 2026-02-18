# fabric-cli-cicd

CI/CD skill for automating Microsoft Fabric deployments. Load after `fabric-cli-core`.

## What This Skill Provides

- GitHub Actions and Azure Pipelines examples
- Environment promotion strategies (dev → test → prod)
- Export/import automation patterns
- Git integration for Fabric items
- Error handling and rollback strategies
- Secrets management guidance

## When to Use

Activate when tasks involve:

- Setting up deployment pipelines
- Environment promotion (dev → test → prod)
- Automating Fabric item exports/imports
- Git-based source control for Fabric definitions
- Service principal authentication for automation

## Prerequisites

Load [`fabric-cli-core`](../fabric-cli-core/) first for foundational guidance.

## Entry Point

Load [`SKILL.md`](./SKILL.md) to activate this skill.

## Scripts

Automation scripts for CI/CD tasks:

| Script | Description | Usage |
|--------|-------------|-------|
| `deploy.py` | Deploy items from local folder to workspace | `python scripts/deploy.py <source> <target-ws> [--dry-run]` |
| `export_workspace.py` | Export all workspace items for version control | `python scripts/export_workspace.py <workspace> -o <dir>` |
| `diff_definitions.py` | Compare item definitions between environments | `python scripts/diff_definitions.py <item1> <item2>` |

## References

Detailed documentation in the `references/` folder:

| Reference | Description |
|-----------|-------------|
| [github-actions.md](./references/github-actions.md) | Complete GitHub Actions workflow examples |
| [azure-pipelines.md](./references/azure-pipelines.md) | Azure Pipelines YAML templates |
| [environment-promotion.md](./references/environment-promotion.md) | Dev/test/prod promotion strategies |
| [git-integration.md](./references/git-integration.md) | Source control patterns |
| [automation-patterns.md](./references/automation-patterns.md) | Scripts and error handling |
