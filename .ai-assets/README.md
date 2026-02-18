# AI Assets for Microsoft Fabric CLI

This folder contains AI-related resources for agents working with the Fabric CLI.

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `context/` | Background context and contributor instructions for different AI tools |
| `modes/` | Custom agents (chat modes) for VS Code Copilot |
| `prompts/` | Reusable prompt templates |
| `skills/` | Task-specific skill definitions |

## Skills

| Skill | Location | Description |
|-------|----------|-------------|
| `fabric-cli-core` | `skills/fabric-cli-core/SKILL.md` | Core CLI operations, auth, paths, safety rules |
| `fabric-cli-cicd` | `skills/fabric-cli-cicd/SKILL.md` | CI/CD pipelines, deployments, Git integration |
| `fabric-cli-powerbi` | `skills/fabric-cli-powerbi/SKILL.md` | Power BI — semantic models, reports, refresh, DAX, gateways |
| `fabric-cli-governance` | `skills/fabric-cli-governance/SKILL.md` | Governance — ACLs, permissions, domains, capacity, audit |
| `fabric-cli-dataengineering` | `skills/fabric-cli-dataengineering/SKILL.md` | Data engineering — lakehouses, medallion, shortcuts, Spark |
| `fabric-cli-realtime` | `skills/fabric-cli-realtime/SKILL.md` | Real-time — eventhouses, eventstreams, KQL, Activator |

### Skill Scripts

Each skill includes automation scripts for common tasks:

| Skill | Scripts |
|-------|---------|
| `fabric-cli-core` | `health_check.py` |
| `fabric-cli-cicd` | `deploy.py`, `export_workspace.py`, `diff_definitions.py` |
| `fabric-cli-powerbi` | `refresh_model.py`, `list_refresh_history.py`, `rebind_report.py` |
| `fabric-cli-governance` | `audit_workspace.py`, `bulk_permissions.py`, `validate_governance.py` |
| `fabric-cli-dataengineering` | `setup_medallion.py`, `optimize_tables.py`, `validate_shortcuts.py` |
| `fabric-cli-realtime` | `setup_streaming.py`, `kql_query.py`, `monitor_eventstream.py` |

Scripts are located in each skill's `scripts/` folder. Run with `python scripts/<script>.py --help` for usage.

## Modes (Custom Agents)

Custom agents appear in the VS Code Copilot dropdown. See `modes/README.md` for setup.

| Mode | File | Deploy Location |
|------|------|-----------------|
| **Fab** | `modes/fab.agent.md` | `.github/agents/fab.agent.md` |

## Prompts

Reusable prompt templates for common Fabric CLI tasks. See `prompts/README.md` for details.

| Prompt | Description |
|--------|-------------|
| `deploy-to-workspace` | Deploy items from source to target workspace |
| `analyze-semantic-model` | Analyze semantic model structure, tables, measures |
| `troubleshoot-refresh` | Diagnose and fix refresh failures |
| `create-lakehouse-pipeline` | Create a data pipeline to load a Lakehouse |
| `workspace-audit` | Audit workspace items, permissions, capacity |
| `migrate-items` | Migrate items between workspaces with validation |

## Context Files

Context files provide project instructions for different AI coding assistants. See `context/README.md` for setup instructions.

| File | Target Tool | Deploy Location |
|------|-------------|-----------------|
| `context/copilot-instructions.md` | GitHub Copilot | `.github/copilot-instructions.md` |
| `context/CLAUDE.md` | Claude Code | `CLAUDE.md` or `.claude/CLAUDE.md` |
| `context/cursorrules.md` | Cursor | `.cursorrules` (no extension) |