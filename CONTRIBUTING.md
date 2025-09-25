# Contributing

This project welcomes contributions and suggestions. Most contributions require you to
agree to a Contributor License Agreement (CLA) declaring that you have the right to,
and actually do, grant us the rights to use your contribution. For details, visit
https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need
to provide a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the
instructions provided by the bot. You will only need to do this once across all repositories using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/)
or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Ways to Contribute

We welcome several types of contributions:

- 🐛 **Bug fixes** - Fix issues and improve reliability
- ✨ **New features** - Add new commands or functionality  
- 📖 **Documentation** - Improve guides, examples, and API docs
- 🧪 **Tests** - Add or improve test coverage
- 💬 **Help others** - Answer questions and provide support
- 💡 **Feature suggestions** - Propose new capabilities

## Contribution process
To avoid cases where submitted PRs are rejected, please follow the following steps:
- To report a new issue, follow [Create an issue](#creating-an-issue)
- To work on existing issue, follow [Find an issue to work on](#finding-an-issue-to-work-on)
- To contribute code, follow [Pull request process](#pull-request-process)

### Creating an issue

Before reporting a new bug or suggesting a feature, please search the [GitHub Issues page](https://github.com/microsoft/fabric-cli/issues) to check if one already exists.

All reported bugs or feature suggestions must start with creating an issue in the GitHub Issues pane. Please add as much information as possible to help us with triage and understanding. Once the issue is triaged, labels will be added to indicate its status (e.g., "need more info", "help wanted").

When creating an issue please select the relevant topic - bug, new feature or general question - and provide all required input.

We aim to respond to new issues promptly, but response times may vary depending on workload and priority.

### Finding an issue to work on

#### For Beginners
If you're new to contributing, look for issues with these labels:
- **`good-first-issue`** - Beginner-friendly tasks that are well-scoped and documented
- **`help wanted`** - Issues where community contributions are especially welcome
- **`documentation`** - Improve docs, examples, or help text (great for first contributions)

#### Getting Started Tips
1. **Start small** - Look for typo fixes, documentation improvements, or simple bug fixes
2. **Read existing code** - Familiarize yourself with the codebase by exploring similar commands
3. **Ask questions** - Comment on issues to clarify requirements or get guidance
4. **Test locally** - Always test your changes thoroughly before submitting

#### Before You Code
All PRs must be linked with a "help wanted" issue. To avoid rework after investing effort:
1. **Comment on the issue** - Express interest and describe your planned approach
2. **Wait for acknowledgment** - Get team confirmation before starting significant work
3. **Ask for clarification** - Don't hesitate to ask questions about requirements
Please review [engineering guidelines](#engineering-guidelines) for coding guidelines and common flows to help you with your task. 

### Pull request process

Please use a descriptive title and provide a clear summary of your changes.

All pull requests (PRs) should be linked to an approved issue, please start the PR description with `- Resolves #issue-number`

Before submitting the pull request please verify that:
- The PR is focused on the related task
- Tests coverage is kept and all tests pass
- Your code is aligned with the code conventions of this project

Before your PR can be merged, make sure to address and resolve all review comments. PR will be labeled as "need author feedback" when there are comments to resolve. Approved PRs will be merged by the Fabric CLI team.

## Resources to help you get started
Here are some resources to help you get started:
- A good place to start learning about Fabric CLI is the [Fabric CLI documentation](https://microsoft.github.io/fabric-cli/)
- If you want to contribute code, please check more details about coding guidelines, major code flows and code building block in [Engineering guidelines](#engineering-guidelines)
- Browse [existing commands](https://microsoft.github.io/fabric-cli/commands/) to understand patterns and conventions
- Check out [usage examples](https://microsoft.github.io/fabric-cli/examples/) to see the CLI in action

## Engineering guidelines

### How to build and run

#### Working with Docker
Working with Docker provides a ready-to-use development environment with all dependencies pre-installed.

Prerequisites:
- Docker Desktop
- Visual Studio Code
- Dev Container extension installed on Visual Studio Code

Open the repository in VSCode with Dev Container:
1. Ensure Docker is up and running.
2. Open the repo in VSCode.
3. Ensure the Dev Containers extension is installed.
4. If prompted by VSCode, select "Reopen in Container." Otherwise, open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P), search for and select "Dev Containers: Reopen Folder in Container."
5. Wait for VSCode to build and start the container. This process might take a few minutes the first time.
6. Run the code (F5 with VSCode) and on first prompt type `auth login`.

### Architecture Overview

Fabric CLI is designed with a modular architecture centered around these key concepts:

#### Elements Hierarchy
Fabric CLI uses an element hierarchy system:
- **Tenants** - Top-level containers (capacities, gateways, domains)
- **Workspaces** - Project containers within tenants
- **Folders** - Organizational containers within workspaces for grouping items
- **Items** - Fabric entities (notebooks, datasets, reports, etc.)
- **OneLake** - File storage within items

Each element type has specific supported operations and properties.

### Common flows
#### Adding a new Command
Before starting implementation, review your new command's design with the Fabric CLI team through the relevant issue or task. Clearly describe the command's purpose, expected usage, and rationale to ensure alignment and avoid unnecessary rework.

When adding a new command:
- Follow naming conventions and code style used in the project.
- Add the command to the appropriate parser module under the `parsers` folder, or create a new module if needed. Fabric CLI uses Python argparse to parse command prompts; see the [argparse documentation](https://docs.python.org/3/library/argparse.html) for details.
- Implement the command handler in the relevant module under the `commands` folder, reusing existing modules and functions where possible.
- Decorate the handler with exception handling and context-setting decorators.
- Validate that the command is supported by the execution context before running its logic.
- Handle failures by raising `FabricCLIError` with clear, actionable messages. See the [Error handling](#error-handling) section for more details.
- Support both text and JSON output formats using the output functions. Refer to the [Output format](#output-format) section for guidelines.
- Provide usage examples and update documentation (e.g., help text and docs folder) to ensure users understand how to use the new command.
- Add tests for the new command, including edge cases and error scenarios. Refer to the [E2E command tests](#e2e-command-tests) section for guidelines.

### Output format
When developing new commands, it's important to consider the supported output formats and use the appropriate print functions for displaying command results (print_output_format, print_error_format) and for user-facing messages during execution (print_info, print_warning, etc.). Currently, we support two formats: json and text (default).

### Error handling
#### Error type
Fabric CLI errors should be raised using the `FabricCLIError` type. Use this for user-facing errors that need to be reported to the CLI user, not for internal exceptions. All Fabric CLI commands are wrapped to handle this error type, printing the error message and error code to the user.

#### Error messages
- Create new error messages under the `errors` folder inside a module relevant to the error.
- Before creating a new error message, check if an existing one can be reused.
- Error messages should be clear, user-friendly, and avoid technical jargon unless necessary.
- Where possible, include actionable advice (e.g., "Check your network connection").

#### Error codes
- All error codes should be created inside the `constant.py` module under the error codes region.
- Before creating a new error code, check for reusing an existing one.
#### Example
```python
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages

# Example of raising an error
raise FabricCLIError(ErrorMessages.Common.file_or_directory_not_exists(), fab_constant.ERROR_INVALID_PATH)
```

### Code Style and Standards

- **Python Style**: Follow PEP 8 guidelines and use Black for formatting
- **Type Hints**: Include type hints where helpful
- **Documentation**: Add docstrings to functions and classes explaining purpose, arguments, return values, and exceptions
- **Naming**: Use descriptive variable and function names
- **Comments**: Explain 'why' not 'what' in code comments

### Testing
Write tests for error scenarios to ensure errors are raised and handled as expected.

#### Fabric CLI tests
Fabric CLI supports 2 types of tests, E2E for commands and unit tests for non-commands code like utils and core functionality.

#### E2E command tests
Please see [Test authoring](./tests/authoring_tests.md)

#### Test Requirements for Contributions
- **Maintain coverage**: Keep test coverage at current levels (~90% for commands, ~80% overall)
- **Add tests for new features**: All new functionality must include appropriate tests
- **Test both success and failure cases**: Cover normal operation and error conditions
- **Use descriptive test names**: Test names should clearly describe what is being tested

## Areas with Restricted Contributions

Some areas require special consideration:
- **Authentication module** - Changes preferred to be made by Fabric CLI team due to security implications
- **Core infrastructure** - Major architectural changes require team discussion

## Need Help?

### Getting Support
- **[GitHub Discussions](https://github.com/microsoft/fabric-cli/discussions)** - Ask questions and discuss ideas
- **[GitHub Issues](https://github.com/microsoft/fabric-cli/issues)** - Report specific problems
- **[Documentation](https://microsoft.github.io/fabric-cli/)** - Check comprehensive guides

### Communication Guidelines
- **Be patient** - Maintainers balance multiple responsibilities
- **Be respectful** - Follow the code of conduct
- **Be specific** - Provide clear, detailed information
- **Be collaborative** - Work together to improve the project

Thank you for contributing to Microsoft Fabric CLI! Your contributions help make this tool better for the entire Fabric community.
