# Skills

Skills are task-specific instruction sets that guide AI agents when helping users with Microsoft Fabric CLI operations.

## Available Skills

| Skill | Description |
|-------|-------------|
| [fabric-cli-core](./fabric-cli-core/) | Core CLI operations - paths, auth, safety rules, item types |
| [fabric-cli-powerbi](./fabric-cli-powerbi/) | Power BI operations - semantic models, reports, refresh, DAX |

## Usage

Load skills based on the user's task:

- **Always load `fabric-cli-core` first** - Provides foundational guidance for all CLI operations
- **Load `fabric-cli-powerbi`** when working with semantic models, reports, DAX queries, or gateways

## Skill Structure

Each skill folder contains:

```
<skill-name>/
├── SKILL.md           # Main skill definition (load this)
├── README.md          # Human-readable overview
├── references/        # Detailed reference docs and examples
└── scripts/           # Python automation scripts
```