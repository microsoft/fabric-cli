---
hide:
  - navigation
---

# Release Notes


## [v1.4.0](https://pypi.org/project/ms-fabric-cli/v1.4.0) - February 09, 2026

### 🆕 New Items Support

* Add support of CosmosDBDatabase item type in mkdir, get, set, rm, ls, cp, mv, import and export commands by [v-alexmoraru](https://github.com/v-alexmoraru)
* Add support of UserDataFunction item type in mkdir, get, set, rm, cp, mv, import and export commands by [v-alexmoraru](https://github.com/v-alexmoraru)
* Add support of GraphQuerySet item type in mkdir, get, rm and export commands by [v-alexmoraru](https://github.com/v-alexmoraru)
* Add support of DigitalTwinBuilder item type in create, rm, get and set (metadata only) by [may-hartov](https://github.com/may-hartov)

### ✨ New Functionality

* Add --format option to export command to pick .ipynb or .py when exporting notebooks by [jkafrouni](https://github.com/jkafrouni)
* Include API response data in the output by [aviatco](https://github.com/aviatco)
* Display a notification to users on login when a new fab cli version is available by [Guust-Franssens](https://github.com/Guust-Franssens)
* Support fab command to start interactive (repl) mode by [aviatco](https://github.com/aviatco)
* Refactored `set` command validation to use blocklist approach instead of allowlist, allowing any query parameter except explicitly blocked ones by [may-hartov](https://github.com/may-hartov)

### 🔧 Bug Fix

* Avoid reauthentication when switching from command_line to interactive mode by [aviatco](https://github.com/aviatco)
* Fixed set shortcut so it correctly handles target query by [may-hartov](https://github.com/may-hartov)
* Fix a typo in connection roles by [Guust-Franssens](https://github.com/Guust-Franssens)
* Add ‘properties’ field to the item metadata list to eliminate unnecessary calls to the getItemDefinition API by [aviatco](https://github.com/aviatco)
* Update the argument-parameter regex to allow optional whitespace after commas by [aviatco](https://github.com/aviatco)
* Fix the job run command so that it exits with status code 1 on failure. by [aviatco](https://github.com/aviatco)
* Set the creation‑method parameters to be optional by [aviatco](https://github.com/aviatco)

### ⚡ Additional Optimizations

* Add python 3.13 support by [ayeshurun](https://github.com/ayeshurun)
* Improve the error message to clearly indicate when the MPE creator does not have sufficient Azure permissions on the resource. by [aviatco](https://github.com/aviatco)
* Reduced unnecessary Fabric administrator warnings for ACL commands by [ayeshurun](https://github.com/ayeshurun)
* optimize the update flow in `set` command to construct PATCH request bodies by extracting only the updated properties from the GET payload by [may-hartov](https://github.com/may-hartov)

### 📝 Documentation Update

* Improve homepage documentation clarity and structure with better headings, simplified examples, and enhanced getting started instructions by [jeremydhoover-blip](https://github.com/jeremydhoover-blip)
* Improve help text clarity and consistency across all commands with concise descriptions, consistent terminology, and user-focused language by [jeremydhoover-blip](https://github.com/jeremydhoover-blip)


## [v1.3.1](https://pypi.org/project/ms-fabric-cli/v1.3.1) - December 15, 2025

### ✨ New Functionality

* Add support of mv, cp, export and import for SQLDatabase item type by [ayeshurun](https://github.com/ayeshurun)
* Add new 'job run-rm' command for remove a scheduled job by [CSharplie](https://github.com/CSharplie)
* Enhance `set` command for items to support any settable property path within the item's definition and metadata structure by [may-hartov](https://github.com/may-hartov)
* Add support in `ls` commmand using `-q` flag for filtering based on JMESPath expressions by [aviatco](https://github.com/aviatco)

### 🔧 Bug Fix

* Fix `--output_format` argument for command `fab auth status` by [Guust-Franssens](https://github.com/Guust-Franssens)
* Fix context persistence in virtual environment by [ayeshurun](https://github.com/ayeshurun)
* Fix create connection with onPremGateway and encryptedCredentials by [aviatco](https://github.com/aviatco)

### ⚡ Additional Optimizations

* Add support for print in key-value list style by [aviatco](https://github.com/aviatco)
* Optimize LRO polling by calling GetOperationResult API only when a Location header is present by [may-hartov](https://github.com/may-hartov)
* Enforce CLI parameter values must be wrapped in single (') or double (") quotes in interactive mode by [aviatco](https://github.com/aviatco)

### 📝 Documentation Update

* Documentation updates by [ayeshurun](https://github.com/ayeshurun)


## [v1.2.0](https://pypi.org/project/ms-fabric-cli/v1.2.0) - October 21, 2025

### 🆕 New Items Support

* Added support for [Dataflow](https://learn.microsoft.com/en-us/fabric/data-factory/dataflows-gen2-overview) item by [aviatco](https://github.com/aviatco)

### ✨ New Functionality

* Enable GraphQLApi item support in `mv` and `cp` commands by [ayeshurun](https://github.com/ayeshurun)
* Add `--block-path-collision` (`-bpc`) flag to `cp` command to prevent implicit overwriting when copying items to another workspace by [may-hartov](https://github.com/may-hartov)
 
### 🔧 Bug Fix

* Align output font color in JSON output format by [aviatco](https://github.com/aviatco)
* Return newly created item in `ls` command in Folder path by [aviatco](https://github.com/aviatco)

### ⚡ Additional Optimizations

* Enhance auto-completion with supported config keys by [may-hartov](https://github.com/may-hartov)


## [v1.1.0](https://pypi.org/project/ms-fabric-cli/1.1.0/) - September 10, 2025

### 🆕 New Items Support

* Added support for GraphQLApi items definitions by [ayeshurun](https://github.com/ayeshurun)

### ✨ New Functionality

* Added support for folders in `fs` commands, including `cp` and `mv` by [jdocampo](https://github.com/jdocampo)
* Added option to output command results in JSON format by [aviatco](https://github.com/aviatco)
* Implemented context persistence between `command_line` mode operations by [MahirDiab](https://github.com/MahirDiab)
* Added autocomplete support for commands and arguments in `command_line` mode by [may-hartov](https://github.com/may-hartov)
* Enabled support for Workspace Level Private Links in `api` command by [ayeshurun](https://github.com/ayeshurun)
* Added support for `set` and `rm` commands in Gateway and Connection by [ayeshurun](https://github.com/ayeshurun)

### 🔧 Bug Fix

* Fixed download of binary files with the `cp` command by [MahirDiab](https://github.com/MahirDiab)
* Disabled the `mv` command for certain real-time intelligence (RTI) items by [murggu](https://github.com/murggu)
* Fixed case sensitivity issues in connection matching by [aviatco](https://github.com/aviatco)

### ⚡ Additional Optimizations

* Adjusted polling intervals for jobs and long-running operations by [may-hartov](https://github.com/may-hartov)
* Standardized configuration key naming conventions by [ayeshurun](https://github.com/ayeshurun)

### 📝 Documentation Update

* Switched to MIT license

## [v1.0.1](https://pypi.org/project/ms-fabric-cli/1.0.1/) - July 15, 2025

### 🔧 Bug Fix

* Fixed `get` command results for items whose definitions include binary files by [MahirDiab](https://github.com/MahirDiab)
* Fixed `--timeout` parameter being parsed as string so it’s now correctly parsed as an integer by [jdocampo](https://github.com/jdocampo)
* Fixed `table load` command when the table doesn't exist by [MahirDiab](https://github.com/MahirDiab)
* Fixed printed output when exiting login with Ctrl+C during managed identity authentication by [ayeshurun](https://github.com/ayeshurun)
* Fixed incorrect sorting of results in the `ls` command by [orshemesh16](https://github.com/orshemesh16)
* Fixed resolution of the log file’s real path in Windows sandbox environments by [aviatco](https://github.com/aviatco)
* Fixed handling of `CopyJob` and `VariableLibrary` items in the `import` command by [ayeshurun](https://github.com/ayeshurun)

### ⚡ Additional Optimizations

* Improved error messages by [ayeshurun](https://github.com/ayeshurun)
* Added support for custom files in `api` commands by [jdocampo](https://github.com/jdocampo)

## [v1.0.0](https://pypi.org/project/ms-fabric-cli/1.0.0/) - May 14, 2025

### ⚠️ Breaking Change

* Added a confirmation prompt in `get` to acknowledge that exported items do not include sensitivity labels; use `-f` to skip

### 🔧 Bug Fix

* Fixed issue in connection creation when `mkdir` was invoked with `skipTestConnection` parameter by [jdocampo](https://github.com/jdocampo)
* Fixed `cp` and `mv` when workspace names contained spaces by [ohadedry](https://github.com/ohadedry)
* Fixed `cd` when workspace display names included special characters by [aviatco](https://github.com/aviatco)
* Fixed a crash in `auth status` when no identity is logged in by [ayeshurun](https://github.com/ayeshurun)

### ⚡ Additional Optimizations

* Added support for [Web Account Manager (WAM)](https://learn.microsoft.com/en-us/windows/uwp/security/web-account-manager) authentication on Windows by [may-hartov](https://github.com/may-hartov)
* Added the application (client) ID of the signed-in identity to `auth status` by [aviatco](https://github.com/aviatco)
* Renamed `fab_auth_mode` to `identity_type` in `auth.json` by [may-hartov](https://github.com/may-hartov)
* Removed the `fab_authority` property from `auth.json` by [may-hartov](https://github.com/may-hartov)
* Updated confirmation prompt in `cp`,`mv`, and `export` to include sensitivity label limitation by [ohadedry](https://github.com/ohadedry)

### 📝 Documentation Update

* Clarified in the documentation for `cp`, `get`, `mv`, and `export` that sensitivity labels are not included in item definitions by [aliabufoul](https://github.com/aliabufoul)

## [v0.2.0](https://pypi.org/project/ms-fabric-cli/0.2.0/) - April 24, 2025

### ⚠️ Breaking Change

* Python v3.13+ is not yet supported.

### 🆕 New Items Support

* Added support for [VariableLibrary](https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview) and [CopyJob](https://learn.microsoft.com/en-us/fabric/data-factory/what-is-copy-job) items by [murggu](https://github.com/murggu)

### ✨ New Functionality

* Added support for Service Principal authentication with federated credentials by [jdocampo](https://github.com/jdocampo)
* Added support for `~/` as a valid path in `import` and `export` input/output parameters by [ayeshurun](https://github.com/ayeshurun)

### 🔧 Bug Fix

* Fixed connection-creation issues in On-Premises Gateways (Standard & Personal) by [jdocampo](https://github.com/jdocampo)
* Fixed whitespace handling in `cp` and `mv` with local paths by [jdocampo](https://github.com/jdocampo)
* Fixed OneLake-to-OneLake copy with encoded data by [jdocampo](https://github.com/jdocampo)


## [v0.1.10](https://pypi.org/project/ms-fabric-cli/0.1.10/) - March 27, 2025

### ✨ New Functionality

* Added item overwrite support in `cp` and `mv` by [murggu](https://github.com/murggu)

### 🔧 Bug Fix

* Fixed binary output in `export` (e.g., report images) by [murggu](https://github.com/murggu)
* Fixed shortcut creation when one already existed for `ln` by [murggu](https://github.com/murggu)

### 📝 Documentation Update

* Updated settings descriptions by [ayeshurun](https://github.com/ayeshurun)


## [v0.1.9](https://pypi.org/project/ms-fabric-cli/0.1.9/) - March 25, 2025

### ✨ New Functionality

* Initial public release
* Released to PyPI
* Onboarded to GitHub Pages