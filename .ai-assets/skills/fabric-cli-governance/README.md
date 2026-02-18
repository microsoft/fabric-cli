# Fabric CLI Governance Skill

Task-specific instructions for AI agents helping users with Microsoft Fabric governance, security, and administration operations.

## Overview

This skill provides guidance for:

- **Access Control** — Workspace roles, item permissions, ACL management
- **Domain Management** — Creating and organizing domains, workspace assignment
- **Capacity Operations** — Capacity assignment, monitoring, SKU management
- **Sensitivity Labels** — Classifying and protecting data
- **Audit & Compliance** — Activity monitoring, permission audits

## When to Load

Load this skill when the user's task involves:

- Managing workspace or item permissions
- Setting up domains or organizational structures
- Assigning workspaces to capacities
- Applying sensitivity labels
- Auditing access or activities
- Configuring security policies (RLS, CLS, OLS)
- Managing connections or gateways

## Files

| File | Description |
|------|-------------|
| [SKILL.md](./SKILL.md) | Main skill definition (load this) |
| [references/](./references/) | Detailed reference documentation |

## Scripts

Automation scripts for governance tasks:

| Script | Description | Usage |
|--------|-------------|-------|
| `audit_workspace.py` | Generate comprehensive workspace audit report | `python scripts/audit_workspace.py <workspace> -o report.json` |
| `bulk_permissions.py` | Apply permissions from CSV/JSON file | `python scripts/bulk_permissions.py <workspace> -i perms.csv` |
| `validate_governance.py` | Check workspace against governance rules | `python scripts/validate_governance.py <workspace> --rules rules.json` |

## Quick Reference

### Common Commands

```bash
# View workspace permissions
fab acl get "Workspace.Workspace"

# Add user to workspace
fab acl set "Workspace.Workspace" -P principal=user@company.com,role=Contributor

# List domains
fab ls .domains -l

# List capacities
fab ls .capacities -l

# Assign workspace to capacity
fab assign "Workspace.Workspace" -P capacityId=<capacity-id>
```

## Dependencies

- Requires `fabric-cli-core` skill loaded first
- Admin or Member workspace role for permission management
- Fabric Admin role for tenant-level operations

## References

- [Fabric Permission Model](https://learn.microsoft.com/fabric/security/permission-model)
- [Workspace Roles](https://learn.microsoft.com/fabric/fundamentals/roles-workspaces)
- [Governance Overview](https://learn.microsoft.com/fabric/governance/governance-compliance-overview)
