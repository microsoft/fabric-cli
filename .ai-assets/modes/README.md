# Modes (Custom Agents)

Custom agents (formerly "chat modes") configure AI behavior for specific tasks. When activated, they appear in the VS Code Copilot dropdown alongside Agent, Ask, and Edit.

## Available Modes

| Mode | File | Description |
|------|------|-------------|
| **Fab** | `fab.agent.md` | Operate Microsoft Fabric using the fab CLI |

## Setup

Copy the agent file to `.github/agents/` in any workspace where you want to use it:

```bash
# From repo root
mkdir -p .github/agents
cp .ai-assets/modes/fab.agent.md .github/agents/
```

Once installed, **Fab** appears in the Copilot mode dropdown (Ctrl+Shift+I → dropdown).

## What Fab Mode Provides

When you switch to Fab mode, the AI:

- **Knows the Fabric hierarchy** — Tenant → Workspace → Folder → Item → OneLakeItem
- **Uses dot suffixes correctly** — `.Workspace`, `.Notebook`, `.SemanticModel`
- **Runs fab commands** — Has terminal access to execute commands
- **Follows safety rules** — Confirms before destructive operations
- **Understands hidden entities** — `.capacities`, `.gateways`, `.sparkpools`

## File Format

Agent files use `.agent.md` extension with YAML frontmatter:

```markdown
---
name: Agent Name
description: Brief description shown in chat input
tools: ['runInTerminal', 'search', 'fetch']
---

# Instructions in Markdown
```

See [VS Code Custom Agents docs](https://code.visualstudio.com/docs/copilot/customization/custom-agents) for full specification.