---
hide:
  - navigation
---

# Release Notes

!!! abstract "Legend"
    📦 New Items **·** ✨ New Features **·** 🔧 Bug Fix **·** ⚡ Optimization **·** 📝 Docs **·** ⚠️ Breaking Change
    
## [v1.1.0](https://pypi.org/project/ms-fabric-cli/1.1.0/)

*Release date: 2025-09-10*

* ✨ Added support for folders in `fs` commands, including `cp` and `mv`
* ✨ Added option to output command results in JSON format
* ✨ Implemented context persistence between `command_line` mode operations
* ✨ Added autocomplete support for commands and arguments in `command_line` mode
* ✨ Enabled support for Workspace Level Private Links in `api` command
* ✨ Added support for `set` and `rm` commands in Gateway and Connection
* 🆕 Added support for GraphQLApi items definitions
* 📝 Switched to MIT license
* 🔧 Fixed download of binary files with the `cp` command
* 🔧 Disabled the `mv` command for certain real-time intelligence (RTI) items
* 🔧 Fixed case sensitivity issues in connection matching
* ⚡ Adjusted polling intervals for jobs and long-running operations
* ⚡ Standardized configuration key naming conventions

## [v1.0.1](https://pypi.org/project/ms-fabric-cli/1.0.1/)

*Release date: 2025-07-15*

* 🔧 Fixed `get` command results for items whose definitions include binary files
* 🔧 Fixed `--timeout` parameter being parsed as string so it’s now correctly parsed as an integer
* 🔧 Fixed `table load` command when the table doesn't exist
* 🔧 Fixed printed output when exiting login with Ctrl+C during managed identity authentication
* 🔧 Fixed incorrect sorting of results in the `ls` command
* 🔧 Fixed resolution of the log file’s real path in Windows sandbox environments
* 🔧 Fixed handling of `CopyJob` and `VariableLibrary` items in the `import` command
* ⚡ Improved error messages
* ⚡ Added support for custom files in `api` commands

## [v1.0.0](https://pypi.org/project/ms-fabric-cli/1.0.0/)

*Release date: 2025-05-14*

* ⚠️ Added a confirmation prompt in `get` to acknowledge that exported items do not include sensitivity labels; use `-f` to skip
* 🔧 Fixed issue in connection creation when `mkdir` was invoked with `skipTestConnection` parameter
* 🔧 Fixed `cp` and `mv` when workspace names contained spaces
* 🔧 Fixed `cd` when workspace display names included special characters
* 🔧 Fixed a crash in `auth status` when no identity is logged in
* ⚡ Added support for [Web Account Manager (WAM)](https://learn.microsoft.com/en-us/windows/uwp/security/web-account-manager) authentication on Windows
* ⚡ Added the application (client) ID of the signed-in identity to `auth status`
* ⚡ Renamed `fab_auth_mode` to `identity_type` in `auth.json`
* ⚡ Removed the `fab_authority` property from `auth.json`
* ⚡ Updated confirmation prompt in `cp`,`mv`, and `export` to include sensitivity label limitation.
* 📝 Clarified in the documentation for `cp`, `get`, `mv`, and `export` that sensitivity labels are not included in item definitions

## [v0.2.0](https://pypi.org/project/ms-fabric-cli/0.2.0/)

*Release date: 2025-04-24*

* ⚠️ Python v3.13+ is not yet supported.
* 🆕 Added support for [VariableLibrary](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview) and [CopyJob](https://learn.microsoft.com/en-us/fabric/data-factory/what-is-copy-job) items  
* ✨ Added support for Service Principal authentication with federated credentials
* ✨ Added support for `~/` as a valid path in `import` and `export` input/output parameters
* 🔧 Fixed connection-creation issues in On-Premises Gateways (Standard & Personal)
* 🔧 Fixed whitespace handling in `cp` and `mv` with local paths
* 🔧 Fixed OneLake-to-OneLake copy with encoded data

## [v0.1.10](https://pypi.org/project/ms-fabric-cli/0.1.10/)

*Release date: 2025-03-27*

* ✨ Added item overwrite support in `cp` and `mv`
* 🔧 Fixed binary output in `export` (e.g., report images)
* 🔧 Fixed shortcut creation when one already existed for `ln`
* 📝 Updated settings descriptions

## [v0.1.9](https://pypi.org/project/ms-fabric-cli/0.1.9/)

*Release date: 2025-03-25*

* ✨ Initial public release
* ✨ Released to PyPI
* ✨ Onboarded to GitHub Pages
