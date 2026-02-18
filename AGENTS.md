# AGENTS.md — AI Agent Guide for Microsoft Fabric CLI

This document provides guidance for AI agents assisting with the [Microsoft Fabric CLI](https://github.com/microsoft/fabric-cli) (`fab`) — a Python-based command-line interface for Microsoft Fabric.

---

## About Microsoft Fabric CLI

The Fabric CLI is a file-system-inspired command-line interface that lets users explore, automate, and script their Microsoft Fabric environment. Key characteristics:

- **Installation**: `pip install ms-fabric-cli`
- **Python versions**: 3.10, 3.11, 3.12, 3.13
- **Platforms**: Windows, macOS, Linux
- **Shells**: PowerShell, Bash, Zsh, cmd
- **Modes**: Interactive (REPL) and command-line (scripting)

**Repository**: https://github.com/microsoft/fabric-cli

---

## AI Assets

All AI-related resources (skills, context, prompts, modes) are organized in the `.ai-assets/` folder. See [`.ai-assets/README.md`](.ai-assets/README.md) for a complete catalog of available resources.

### Key Resources

| Resource | Location |
|----------|----------|
| AI Assets Overview | `.ai-assets/README.md` |
| Skills (Usage) | `.ai-assets/skills/` |
| Prompts (Templates) | `.ai-assets/prompts/` |
| Modes (Agents) | `.ai-assets/modes/` |
| Context (Contributor) | `.ai-assets/context/` |

### External Documentation

| Resource | URL |
|----------|-----|
| Documentation | https://microsoft.github.io/fabric-cli/ |
| Command Reference | https://microsoft.github.io/fabric-cli/commands/ |
| Usage Examples | https://microsoft.github.io/fabric-cli/examples/ |

---

## For AI Agents Helping Users (Operating Fabric CLI)

When assisting users who want to **use the CLI** (not develop it), load skills from `.ai-assets/skills/`:

### Available Skills

| Skill | When to Load |
|-------|--------------|
| `fabric-cli-core` | **Always load first** — paths, auth, safety, item types |
| `fabric-cli-cicd` | Deploying, CI/CD pipelines, automation |
| `fabric-cli-powerbi` | Semantic models, reports, DAX, refresh |
| `fabric-cli-governance` | Permissions, ACLs, domains, capacity |
| `fabric-cli-dataengineering` | Lakehouses, tables, shortcuts, Spark |
| `fabric-cli-realtime` | Eventhouses, KQL, eventstreams |

### Quick Start Commands

```bash
# Check authentication
fab auth status

# List workspaces
fab ls

# List items in workspace
fab ls "MyWorkspace.Workspace"

# Get help for any command
fab --help
fab ls --help
```

### Critical Operational Rules

1. **First run** — Always verify auth with `fab auth status`
2. **Learn before executing** — Use `fab <command> --help` to understand syntax
3. **Verify before acting** — Use `fab exists` or `fab ls` to confirm paths
4. **Non-interactive mode** — Use `-f` flag for automation
5. **Safety first** — Confirm before destructive operations

---

## For AI Agents Helping Contributors (Developing the CLI)

When assisting with **code contributions** to this repository (adding features, fixing bugs, writing tests), refer to the contributor context in `.ai-assets/context/`.

### Forking and Setting Up

Guide users through the contribution workflow:

1. **Fork the repository**: https://github.com/microsoft/fabric-cli/fork
2. **Clone locally**:
   ```bash
   git clone https://github.com/<username>/fabric-cli.git
   cd fabric-cli
   ```
3. **Set up development environment** (dev container recommended)
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-change
   ```

### Contribution Process

All PRs must follow this process:

1. **Find or create an issue** — Search [GitHub Issues](https://github.com/microsoft/fabric-cli/issues) first
2. **Look for `help-wanted` label** — Required before starting work
3. **Comment on the issue** — Describe your planned approach and wait for acknowledgment
4. **Link PR to issue** — Start PR description with `- Resolves #issue-number`
5. **Add changie entry** — Run `changie new` and select the appropriate change type

### Code Standards to Enforce

When reviewing or generating code, ensure:

| Requirement | Details |
|-------------|---------|
| **Type hints** | All functions must have proper type annotations |
| **Formatting** | Must pass `black src/ tests/` |
| **Type checking** | Must pass `mypy src/ tests/ --ignore-missing-imports` |
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes |
| **Imports** | Grouped: stdlib → third-party → local |
| **Copyright** | All new files need Microsoft copyright header |
| **Docstrings** | Required for public functions |

### Error Handling Pattern

Always use structured error classes:

```python
from fabric_cli.errors.common import CommonErrors
from fabric_cli import fab_constant

# Good
raise FabricCLIError(
    CommonErrors.invalid_path(path),
    fab_constant.ERROR_INVALID_INPUT
)

# Bad — hardcoded message
raise FabricCLIError("Invalid path provided")
```

### Testing Requirements

All new functionality must include tests:

```bash
# Unit tests
python3 -m pytest tests/test_core tests/test_utils

# Integration tests (with VCR playback)
python3 -m pytest tests/test_commands --playback
```

### Restricted Areas

Warn contributors that these areas require team involvement:

- **Authentication module** — Security implications require Fabric CLI team review
- **Core infrastructure** — Major architectural changes need team discussion

---

## Quick Reference Links

- **Repository**: https://github.com/microsoft/fabric-cli
- **Issues**: https://github.com/microsoft/fabric-cli/issues
- **Discussions**: https://github.com/microsoft/fabric-cli/discussions
- **Wiki (Engineering Guidelines)**: https://github.com/microsoft/fabric-cli/wiki
- **Contributing Guide**: https://github.com/microsoft/fabric-cli/blob/main/CONTRIBUTING.md
- **Documentation**: https://microsoft.github.io/fabric-cli/
