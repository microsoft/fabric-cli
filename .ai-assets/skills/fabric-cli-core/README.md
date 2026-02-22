# fabric-cli-core

Core skill for Microsoft Fabric CLI operations. **Load this skill first** for any Fabric CLI task.

## What This Skill Provides

- Fabric hierarchy mental model (Tenant → Workspace → Folder → Item → OneLakeItem)
- Path conventions with dot entity suffixes (e.g., `.Workspace`, `.Notebook`)
- Authentication patterns (interactive, SPN, managed identity)
- Hidden entity discovery (`ls -a`)
- Security and sensitive data handling rules
- Critical operational rules
- Common item types reference

## Entry Point

Load [`SKILL.md`](./SKILL.md) to activate this skill.

## References

Detailed documentation in the `references/` folder:

| Reference | Description |
|-----------|-------------|
| [quickstart.md](./references/quickstart.md) | Copy-paste examples for common tasks |
| [reference.md](./references/reference.md) | All commands with flags and patterns |
| [semantic-models.md](./references/semantic-models.md) | TMDL, DAX queries, refresh, storage modes |
| [notebooks.md](./references/notebooks.md) | Job execution, parameters, scheduling |
| [reports.md](./references/reports.md) | Export, import, rebind to models |
| [workspaces.md](./references/workspaces.md) | Create, manage, permissions |
| [querying-data.md](./references/querying-data.md) | DAX and lakehouse table queries |
| [fab-api.md](./references/fab-api.md) | Direct REST API access patterns |
| [create-workspaces.md](./references/create-workspaces.md) | Workspace creation workflows |
