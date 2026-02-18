# Skills

Skills are task-specific instruction sets that guide AI agents when helping users with Microsoft Fabric CLI operations.

## Available Skills

| Skill | Description |
|-------|-------------|
| [fabric-cli-core](./fabric-cli-core/) | Core CLI operations — paths, auth, safety rules, item types |
| [fabric-cli-cicd](./fabric-cli-cicd/) | CI/CD pipelines — deployments, Git integration, automation |
| [fabric-cli-powerbi](./fabric-cli-powerbi/) | Power BI operations — semantic models, reports, refresh, DAX, gateways |
| [fabric-cli-governance](./fabric-cli-governance/) | Governance — ACLs, permissions, domains, capacity, sensitivity labels, audit |
| [fabric-cli-dataengineering](./fabric-cli-dataengineering/) | Data engineering — lakehouses, medallion architecture, shortcuts, Spark |
| [fabric-cli-realtime](./fabric-cli-realtime/) | Real-time intelligence — eventhouses, eventstreams, KQL, Activator alerts |

## Usage

Load skills based on the user's task:

- **Always load `fabric-cli-core` first** — Provides foundational guidance for all CLI operations
- **Load `fabric-cli-cicd`** when working with pipelines, deployments, or automation
- **Load `fabric-cli-powerbi`** when working with semantic models, reports, DAX queries, or gateways
- **Load `fabric-cli-governance`** when working with permissions, ACLs, domains, capacity, or compliance
- **Load `fabric-cli-dataengineering`** when working with lakehouses, medallion architecture, shortcuts, or Spark
- **Load `fabric-cli-realtime`** when working with eventhouses, eventstreams, KQL queries, or real-time alerts

## Skill Structure

Each skill folder contains:

```
<skill-name>/
├── SKILL.md           # Main skill definition (load this)
├── README.md          # Human-readable overview
├── references/        # Detailed reference docs and examples
└── scripts/           # Python automation scripts
```