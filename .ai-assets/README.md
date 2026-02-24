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
| `fabric-cli-powerbi` | `skills/fabric-cli-powerbi/SKILL.md` | Power BI operations, semantic models, reports, refresh, DAX |

### Skill Scripts

Each skill includes automation scripts for common tasks:

| Skill | Scripts |
|-------|---------|
| `fabric-cli-core` | `health_check.py` |
| `fabric-cli-powerbi` | `refresh_model.py`, `list_refresh_history.py`, `rebind_report.py` |

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
| `create-workspace` | Create a new Microsoft Fabric workspace with configuration |

## Context Files

Context files provide project instructions for different AI coding assistants. See `context/README.md` for setup instructions.

| File | Target Tool | Deploy Location |
|------|-------------|-----------------|
| `context/copilot-instructions.md` | GitHub Copilot | `.github/copilot-instructions.md` |
| `context/CLAUDE.md` | Claude Code | `CLAUDE.md` or `.claude/CLAUDE.md` |
| `context/cursorrules.md` | Cursor | `.cursorrules` (no extension) |