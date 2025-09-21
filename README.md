# Microsoft Fabric CLI


[![PyPi version](https://badgen.net/pypi/v/ms-fabric-cli/)](https://pypi.org/project/ms-fabric-cli)
[![Python versions](https://img.shields.io/pypi/pyversions/ms-fabric-cli)](https://pypi.org/project/ms-fabric-cli)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

The Microsoft Fabric CLI (`fab`) is a powerful, file-system-inspired command-line interface for Microsoft Fabric. Explore, automate, and script your Fabric environment directly from your terminal with familiar commands like `ls`, `cd`, `mkdir`, `cp`, and more.

## 🚀 Quick Start

```bash
# Install the CLI
pip install ms-fabric-cli

# Authenticate
fab auth login

# Start exploring
fab ls                           # List workspaces and items
fab cd MyWorkspace.workspace     # Navigate to a workspace
fab ls -l                        # List items with details
fab get MyNotebook.notebook      # Get item properties
```

## ✨ Key Features

### 🗂️ **File-System Navigation**
Navigate Microsoft Fabric like your local file system with intuitive commands:
- **`ls`, `cd`, `pwd`** - Navigate workspaces and items
- **`mkdir`, `rm`, `mv`, `cp`** - Create, delete, move, and copy items
- **`exists`, `open`** - Check existence and open items in the Fabric portal

### 🔄 **Data & Item Management**
- **Import/Export** items with `import` and `export` commands
- **OneLake file operations** - Upload, download, and manage files
- **Table operations** - Load data, optimize tables, manage schemas
- **Shortcut management** - Create and manage OneLake shortcuts

### 🤖 **Automation Ready**
- **Scripting mode** - Perfect for CI/CD pipelines and automation
- **Interactive mode** - Live shell experience for exploration
- **Job management** - Run, schedule, and monitor Fabric jobs
- **API access** - Direct REST API calls with authentication handled

### 🔐 **Flexible Authentication**
- **Interactive login** - Browser-based authentication
- **Service Principal** - Client secrets, certificates, and federated tokens
- **Managed Identity** - System and user-assigned identities
- **Environment variables** - Headless authentication for automation

### 🌐 **Cross-Platform Support**
- **Windows, macOS, Linux** - Native support across all platforms
- **Multiple shells** - PowerShell, Bash, Zsh, and more
- **Shell completion** - Autocomplete for commands and arguments (in command-line mode)

## 📦 Installation

### Prerequisites
- **Python 3.10, 3.11, or 3.12**
- A **Microsoft Fabric** account with access to your tenant/workspaces.

### Install via pip
```bash
pip install ms-fabric-cli
```

### Upgrade existing installation
```bash
pip install --upgrade ms-fabric-cli
```

### Verify installation
```bash
fab --version
```

## 🔐 Authentication

### Interactive Login
```bash
fab auth login
# Select: "Interactive with a web browser"
```

### Service Principal
```bash
fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>
```

The CLI supports additional authentication methods including certificates, managed identity, and environment variables. See the [authentication documentation](https://microsoft.github.io/fabric-cli/examples/auth_examples/)) for complete details.

## 🎯 Usage Examples

### Basic Navigation
```bash
# List all workspaces
fab ls

# Navigate to a workspace
fab cd "Sales Analytics.workspace"

# List items in current workspace
fab ls -l

# Get current location
fab pwd
```

### Working with Items
```bash
# Create a new notebook
fab mkdir MyNotebook.notebook

# Copy an item between workspaces
fab cp notebook1.notebook /TargetWorkspace.workspace/

# Export an item definition
fab export MyReport.report -o ./backup/

# Import an item
fab import NewNotebook.notebook -i ./definitions/notebook.json
```

### OneLake File Operations
```bash
# Navigate to lakehouse files
fab cd MyLakehouse.lakehouse/Files

# Upload a file
fab cp ./local-data.csv ./remote-data.csv

# Download files
fab cp ./remote-data.csv ~/Downloads/

# List files with details
fab ls -l
```

### Job Management
```bash
# Run a notebook synchronously
fab job run MyNotebook.notebook

# Schedule a pipeline
fab job run-sch MyPipeline.datapipeline --type daily --interval "09:00"

# Check job status
fab job run-status MyNotebook.notebook --id <job-id>
```

### Table Operations
```bash
# Load CSV data into a table
fab table load Tables/SalesData --file Files/sales.csv --mode append

# Optimize a table
fab table optimize Tables/SalesData --vorder --zorder ProductID,Date

# View table schema
fab table schema Tables/SalesData
```

### API Integration
```bash
# Make authenticated API calls
fab api workspaces

# Query with JMESPath
fab api workspaces -q "value[?name=='MyWorkspace']"

# POST request with data
fab api capacities -X POST -i capacity-config.json
```

## 🔧 Configuration

### Interactive vs Command-Line Mode
```bash
# Switch to interactive mode
fab config set mode interactive
fab auth login  # Re-authenticate for interactive mode

# Switch back to command-line mode
fab config set mode command_line
```

### Common Settings
```bash
# Enable debug logging
fab config set debug_enabled true

# Set default capacity
fab config set default_capacity "My Capacity"

# Configure output sorting
fab config set output_item_sort_criteria bytype

# View all settings
fab config ls
```

## 📚 Documentation

| Resource | Description |
|----------|-------------|
| **[Command Reference](https://microsoft.github.io/fabric-cli/commands/)** | Complete command documentation |
| **[Usage Examples](https://microsoft.github.io/fabric-cli/examples/)** | Real-world scenarios and scripts | 
| **[API Integration](https://microsoft.github.io/fabric-cli/commands/api/)** | Direct REST API access patterns |
| **[CI/CD Integration](https://microsoft.github.io/fabric-cli/examples/#cicd-integration)** | GitHub Actions and Azure Pipelines |
| **[Settings](https://microsoft.github.io/fabric-cli/essentials/settings/)** | CLI Configuration |

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation, or helping other users, your contributions are valuable.

### Quick Start Contributing
1. **Check existing issues** - Look for issues labeled `help-wanted`
2. **Read our guidelines** - See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions
3. **Fork and clone** - Set up your development environment
4. **Create a pull request** - Link it to the related issue

Before contributing, please review our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## 🆘 Support & Community

### Getting Help
- **[GitHub Issues](https://github.com/microsoft/fabric-cli/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/microsoft/fabric-cli/discussions)** - Questions and community support
- **[Documentation](https://microsoft.github.io/fabric-cli/)** - Comprehensive guides and examples
- **[Microsoft Community](https://community.fabric.microsoft.com/t5/Developer/bd-p/Developer)** - Connect with other Fabric developers

### Feature Requests
- **[GitHub Issues](https://github.com/microsoft/fabric-cli/issues)** - Technical feature requests
- **[Fabric Ideas Portal](https://ideas.fabric.microsoft.com/)** - Product-level feature suggestions

### Enterprise Support
- Contact your Microsoft account manager
- **[Microsoft Fabric Support](https://support.fabric.microsoft.com/)** - Official Microsoft support



## 🔄 Release Notes

### Latest Release - v1.1.0
- ✨ Added support for folders in `fs` commands
- ✨ JSON output format support
- ✨ Context persistence in command-line mode
- ✨ Autocomplete support for commands (in command-line mode)
- 🆕 GraphQLApi items support
- 🔧 Multiple bug fixes and improvements

See the full [Release Notes](https://microsoft.github.io/fabric-cli/release-notes/) for detailed changelog.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 Microsoft Open Source

This project is part of Microsoft's commitment to open source. We follow Microsoft's [Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

For questions or concerns, contact [opencode@microsoft.com](mailto:opencode@microsoft.com).

---

<div align="center">
  <p><strong>Explore, Automate, and Build with Microsoft Fabric CLI</strong></p>
  <p>
    <a href="https://microsoft.github.io/fabric-cli/">📖 Documentation</a> •
    <a href="https://github.com/microsoft/fabric-cli/issues">🐛 Report Bug</a> •
    <a href="https://github.com/microsoft/fabric-cli/discussions">💬 Discuss</a> •
    <a href="https://ideas.fabric.microsoft.com/">💡 Request Feature</a>
  </p>
</div>
