---
hide:
  - navigation
---

# Fabric CLI

The Fabric CLI (`fab`) is a fast, file‑system‑inspired command‑line interface for Microsoft Fabric.  Explore, automate, and script your Fabric environment—right from your terminal.

---


## ✨ Key features

- File‑system navigation – `ls`, `cd`, `mkdir`, `cp`, `rm`, `run`. Work seemlesly in both Unix-style and Windows-style command names for file system operations. You can use whichever style you're most familiar with. For more details see [File System Commands](./commands/index.md#file-system-operations-fs).
- Scripting & interactive modes – switch fluidly between live shell and one‑off commands.
- Automation ready – ideal for GitHub Actions, Azure Pipelines, or any Bash/PowerShell/Python workflow.
- Cross‑platform – Windows Terminal, macOS Terminal, Linux shells.
- Built on public APIs – Fabric REST, OneLake, and Microsoft.Fabric ARM endpoints.


## 🚀 Install

Prerequisites:

  - Python version 3.10, 3.11, 3.12, 3.13, or 3.14 is installed on your machine.
  - Ensure `python` (defined in the `PATH` environment variable) is accessible from your terminal, by opening a terminal and run `python`.

Open a terminal and run:

```
pip install ms-fabric-cli
```

This installs the latest version of `fab` on Windows, MacOS, and Linux.
If you’re upgrading from an earlier version, simply run the same command with `‑‑upgrade`.

*Need a different method?* See the [release notes](./release-notes.md) for standalone binaries and package managers as they become available.


## 🔐 Authenticate

`fab` supports **user**, **service principal**, and **managed identity** identity types for sign‑in.  

| **Identity Type**        | **Scenario**                       | **Command Usage**                                                                                    |
|----------------------|------------------------------------|------------------------------------------------------------------------------------------------|
| **User**             | Interactive browser login          | `fab auth login` and select *Interactive with a web browser*                                                                               |
| **Service Principal**| Secret                             | `fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>`                        |
|                      | Certificate              | `fab auth login -u <client_id> --certificate </path/to/certificate.[pem\|p12\|pfx]> --tenant <tenant_id>` |
|                      | Certificate + password   | `fab auth login -u <client_id> --certificate </path/to/certificate.[pem\|p12\|pfx]> -p <certificate_secret> --tenant <tenant_id>` |
|                      | Federated token          | `fab auth login -u <client_id> --federated-token <token> --tenant <tenant_id>` |
| **Managed Identity** | System‑assigned                    | `fab auth login --identity`                                                                    |
|                      | User‑assigned                      | `fab auth login --identity -u <client_id>`                                                     |

For more details and scripts, see the [auth examples](./examples/auth_examples.md).

## 🏁 Run Your First Command

Once you’re signed in, you’re one command away from exploring Fabric. Try and run `ls` command to list all workspaces:

```
fab ls
```

For a detailed list of available commands, see [Commands](./commands/index.md), or explore advanced scenarios in our [Usage examples](./examples/index.md).

## 💬 Feedback & Support

**Have thoughts on the Fabric CLI?** We review every submission and your input directly shapes the Fabric CLI roadmap.

- **Submit feedback**  
  Use our short [Microsoft Form](https://forms.office.com/r/uhL6b6tNsi) to report issues, request enhancements, or ask questions.

- **Stay in the loop**  
  Join the conversation in [r/MicrosoftFabric on Reddit](https://www.reddit.com/r/MicrosoftFabric/) — follow updates, share tips, and connect with other CLI users.

- **Share feature ideas**  
  Post and vote on suggestions in the [Fabric Ideas Portal](https://ideas.fabric.microsoft.com/).

- **Get community help**  
  Ask technical questions in the [Developer Community Forum](https://community.fabric.microsoft.com/t5/Developer/bd-p/Developer) — the Fabric team and community experts are ready to help.

- **Need enterprise assistance?**  
  Reach out to your Microsoft account manager or open a ticket with the [Fabric Support Team](https://support.fabric.microsoft.com/).

*Thank you for helping us build the best CLI experience possible!*



