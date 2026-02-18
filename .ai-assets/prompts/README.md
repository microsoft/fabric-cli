# Fabric CLI Prompts

Reusable prompt templates for common Fabric CLI tasks. Use these with any AI coding assistant.

## Available Prompts

| Prompt | Description |
|--------|-------------|
| [deploy-to-workspace](deploy-to-workspace.prompt.md) | Deploy Fabric items from source to target workspace |
| [analyze-semantic-model](analyze-semantic-model.prompt.md) | Analyze a semantic model's structure, tables, and measures |
| [troubleshoot-refresh](troubleshoot-refresh.prompt.md) | Diagnose and fix refresh failures |
| [create-lakehouse-pipeline](create-lakehouse-pipeline.prompt.md) | Create a data pipeline to load a Lakehouse |
| [workspace-audit](workspace-audit.prompt.md) | Audit workspace items, permissions, and capacity |
| [migrate-items](migrate-items.prompt.md) | Migrate items between workspaces with validation |

## Usage

Copy the prompt content into your AI assistant, or reference the file directly. Each prompt includes:

- Step-by-step instructions
- Relevant `fab` CLI commands
- Safety guidelines and best practices
- Validation steps

## Customization

Adapt prompts to your needs:
- Replace `{workspaceName}` placeholders with actual values
- Add organization-specific policies
- Include environment-specific defaults

## References

- [fabric-cli Documentation](https://microsoft.github.io/fabric-cli/)
