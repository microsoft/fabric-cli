# Tab Completion

The Fabric CLI (`fab`) supports comprehensive tab completion in `command_line` mode for commands, subcommands, and flags to enhance productivity. This feature provides auto-completion suggestions as you type, reducing the need to memorize command syntax.

## Current Limitations and Support

The tab completion feature currently supports the following functionality:

-   **Command Completion** - Auto-complete group commands (e.g., `fab <Tab>`)
-   **Subcommand Completion** - Auto-complete subcommands for each command (e.g., `fab acl <Tab>`)
-   **Flag Completion** - Auto-complete available flags and options (e.g., `fab acl --<Tab>`)
-   **Config Key Completion** - Auto-complete keys for `config get` and `config set` commands (e.g., `fab config get <Tab>`)

## Shell Support

Tab completion is supported in the following shell environments:

-   **PowerShell** (Windows PowerShell and PowerShell Core)
-   **Bash** (Linux/macOS and Windows Subsystem for Linux)
-   **Zsh** (Z shell - popular on macOS and Linux)

## How to Enable Autocompletion

To enable `fab` tab completion, follow the instructions for your shell.

The completion scripts are also available in the [scripts/completion](https://github.com/microsoft/fabric-cli/blob/main/scripts/completion) directory of the repository.

---

### PowerShell

1.  Create or edit your PowerShell profile. You can open it by running `notepad $PROFILE`.
2.  Refer to the script [`fab_completion.ps1`](https://github.com/microsoft/fabric-cli/blob/main/scripts/completion/fab_completion.ps1) and add it to your profile.
3.  Restart your terminal or run `. $PROFILE` to apply the changes.


### Zsh

1.  Open your Zsh profile (`~/.zshrc`) in a text editor.
2.  Add the following line:

    ```bash
    # This script is provided as a sample to demonstrate how to enable fab tab completion. Users are solely responsible for reviewing, testing, and executing this script in their environment.
    eval "$(register-python-argcomplete fab)"
    ```

3.  Restart your terminal or run `source ~/.zshrc` to apply the changes.


### Bash

1.  Open your Bash profile (`~/.bashrc`) in a text editor.
2.  Add the following line:

    ```bash
    # This script is provided as a sample to demonstrate how to enable fab tab completion. Users are solely responsible for reviewing, testing, and executing this script in their environment.
    eval "$(register-python-argcomplete fab)"
    ```

3.  Restart your terminal or run `source ~/.bashrc` to apply the changes.