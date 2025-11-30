# CLI Input
The Fabric CLI accepts input values for command parameters.

## JSON Input Handling

When providing JSON input in command-line mode, different shells process quotes and escape characters before passing them to the CLI.

**Best Practice:** Use single quotes (`'`) around JSON input. Some shells (like PowerShell) may require escaping inner double quotes with backslashes (`\"`)

=== "PowerShell"
    ```
    fab set item.Resource -q query -i '{\"key\":\"value\"}'
    ```

=== "Bash"
    ```bash
    fab set item.Resource -q query -i '{"key":"value"}'
    ```

=== "Zsh"
    ```
    fab set item.Resource -q query -i '{"key":"value"}'
    ```