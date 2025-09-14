# This script is provided as a sample to demonstrate how to enable fab tab completion. Users are solely responsible for reviewing, testing, and executing this script in their environment.
# To enable tab completion for `fab` command, add the following script to your PowerShell $PROFILE. Then restart Powershell or run `source $PROFILE` to apply changes.
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