# Tab Completion for Fabric CLI

## Disclaimer

The following scripts are provided as samples to demonstrate how to enable `fab` tab completion on specific shells. Users are solely responsible for reviewing, testing, and executing these scripts in their environment.

## Introduction

The Fabric CLI (`fab`) supports comprehensive tab completion functionality for commands, subcommands, and flags when used in command line mode. This feature enhances productivity by providing auto-completion suggestions as you type, reducing the need to memorize command syntax and available options.

## Current Limitations/Support

The tab completion feature currently supports the following functionality:

- **Command Completion** - Auto-complete main commands (e.g., `fab <Tab>`)
- **Subcommand Completion** - Auto-complete subcommands for each command (e.g., `fab acl <Tab>`)
- **Flag Completion** - Auto-complete available flags and options (e.g., `fab acl --<Tab>`)

**Note**: Fabric-specific path argument completion (for workspaces, items, etc.) is in our backlog.

## Shell Support

Tab completion is supported across the following shell environments:

- **PowerShell** (Windows PowerShell and PowerShell Core)
- **Bash** (Linux/macOS and Windows Subsystem for Linux)
- **Zsh** (Z shell - popular on macOS and Linux)

## Installation Instructions

**Note**: Ensure that ms-fabric-cli is properly installed before setting up completion.

To enable fab tab completion, follow these steps:
### PowerShell

1. Create or edit the profile stored in the variable `$PROFILE`. The simplest way is to run `notepad $PROFILE` in PowerShell. For more information, see [How to create your profile](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles#how-to-create-a-profile) and [Profiles and execution policy](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles#profiles-and-execution-policy). Add the following script to your profile:</search>
</search_and_replace>

```powershell
Register-ArgumentCompleter -Native -CommandName fab -ScriptBlock {
    param($commandName, $fullCommandLine, $cursorPosition)
    $completion_file = New-TemporaryFile
    $env:ARGCOMPLETE_USE_TEMPFILES = 1
    $env:_ARGCOMPLETE_STDOUT_FILENAME = $completion_file.FullName

    $env:COMP_LINE = $fullCommandLine
    $env:COMP_POINT = $cursorPosition
    $env:_ARGCOMPLETE = 1
    $env:_ARGCOMPLETE_SUPPRESS_SPACE = 0
    $env:_ARGCOMPLETE_IFS = "`n"
    $env:_ARGCOMPLETE_SHELL = "powershell"
    fab 2>&1 | Out-Null

    Get-Content $completion_file | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)
    }
    Remove-Item $completion_file, Env:_ARGCOMPLETE_STDOUT_FILENAME, Env:ARGCOMPLETE_USE_TEMPFILES, Env:COMP_LINE, Env:COMP_POINT, Env:_ARGCOMPLETE, Env:_ARGCOMPLETE_SUPPRESS_SPACE, Env:_ARGCOMPLETE_IFS, Env:_ARGCOMPLETE_SHELL
}
```

2. Restart your terminal or run `. $PROFILE` to apply changes.

### Zsh

1. Open your Zsh profile (`~/.zshrc`) and add the following script:

```bash
eval "$(register-python-argcomplete fab)"
```

2. Restart your terminal or run `source ~/.zshrc` to apply changes.

### Bash

1. Open your Bash profile (`~/.bashrc`) and add the following script:

```bash
eval "$(register-python-argcomplete fab)"
```

2. Restart your terminal or run `source ~/.bashrc` to apply changes.

## Usage

Once tab completion is properly configured, you can use it by:

1. **Command Completion**: Type `fab` followed by a space and press Tab to see available commands
2. **Subcommand Completion**: Type a command (e.g., `fab acl`) and press Tab to see available subcommands
3. **Flag Completion**: Type a command with a dash (e.g., `fab acl -`) and press Tab to see available flags

Example usage:
```bash
fab <Tab>               # Shows main commands
fab acl <Tab>           # Shows acl subcommands
fab acl --<Tab>         # Shows available flags for acl command
```