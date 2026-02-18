# Fabric CLI Real-Time Intelligence Skill

This skill provides comprehensive guidance for managing real-time analytics in Microsoft Fabric using the Fabric CLI.

## Overview

Real-time intelligence in Fabric enables streaming data analytics through:
- **Eventhouses** — Optimized streaming data stores
- **Eventstreams** — Stream ingestion and routing
- **KQL Databases** — Time-series analytics
- **Activator** — Alert triggers and actions

## Contents

### Main Skill File
- `SKILL.md` — Core skill definition and patterns

### Reference Files

| File | Description |
|------|-------------|
| `references/eventhouse-operations.md` | Eventhouse creation, configuration, and management |
| `references/eventstream-patterns.md` | Eventstream sources, destinations, and routing |
| `references/kql-queries.md` | KQL query patterns and CLI execution |
| `references/activator-alerts.md` | Alert triggers, conditions, and actions |
| `references/streaming-patterns.md` | End-to-end streaming architecture patterns |

### Scripts

Automation scripts for real-time intelligence tasks:

| Script | Description | Usage |
|--------|-------------|-------|
| `setup_streaming.py` | Create complete streaming pipeline | `python scripts/setup_streaming.py <workspace> --name <pipeline>` |
| `kql_query.py` | Execute KQL query and return results | `python scripts/kql_query.py <database> --query <kql-file>` |
| `monitor_eventstream.py` | Check eventstream health and throughput | `python scripts/monitor_eventstream.py <eventstream>` |

## Quick Start

```bash
# List all real-time items
fab ls "Workspace/*.Eventhouse"
fab ls "Workspace/*.Eventstream"
fab ls "Workspace/*.KQLDatabase"

# Get item details
fab get "Workspace/MyEventhouse.Eventhouse"
```

## When to Use This Skill

- Building real-time analytics solutions
- Setting up streaming data pipelines
- Configuring KQL-based analytics
- Creating automated alerts and triggers
- Managing time-series data stores
