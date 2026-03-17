# Context Files

This folder contains context/instruction files for different AI coding assistants. Each file provides the same core project information, formatted for the specific tool.

## Available Files

| File | Target Tool | Usage |
|------|-------------|-------|
| `copilot-instructions.md` | GitHub Copilot | Copy to `.github/copilot-instructions.md` |
| `CLAUDE.md` | Claude Code | Copy to repo root as `CLAUDE.md` or `.claude/CLAUDE.md` |
| `cursorrules.md` | Cursor | Copy content to `.cursorrules` in repo root (no extension) |

## Setup Instructions

### GitHub Copilot

```bash
# From repo root
cp .ai-assets/context/copilot-instructions.md .github/copilot-instructions.md
```

Copilot automatically loads `.github/copilot-instructions.md` for all chat and code generation requests.

### Claude Code

```bash
# From repo root
cp .ai-assets/context/CLAUDE.md ./CLAUDE.md
# Or use .claude directory
mkdir -p .claude && cp .ai-assets/context/CLAUDE.md .claude/CLAUDE.md
```

Claude Code automatically loads `CLAUDE.md` at session start.

### Cursor

```bash
# From repo root - note: no file extension
cp .ai-assets/context/cursorrules.md .cursorrules
```

Cursor automatically loads `.cursorrules` for all AI interactions.

## Content Differences

All files contain the same core information about:
- Project overview and design patterns
- Code structure and layout
- Build/test commands
- Error handling patterns
- Code standards and security rules

The main differences are:
- **Copilot**: Full detailed instructions optimized for chat and code review
- **Claude Code**: Concise format optimized for Claude's memory system (first 200 lines loaded)
- **Cursor**: Compact rules format for Cursor's context window