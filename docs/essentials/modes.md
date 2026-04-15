# CLI Modes

The Fabric CLI supports two modes: **command-line** and **REPL** (interactive). The active mode is determined automatically at runtime — no configuration is required.

## Command-Line Mode

Command-line mode is best suited for scripted tasks, automation, or when you prefer running single commands without a persistent prompt.

Invoke any command directly from your terminal with the `fab` prefix:

```
fab ls /
fab get /myworkspace.Workspace/mynotebook.Notebook
```

## REPL Mode

REPL mode provides a shell-like interactive environment. Run `fab` without any arguments to enter REPL mode:

```
fab
```

Upon entering REPL mode, you see a `fab:/$` prompt. Commands are executed one by one without needing to type `fab` before each command:

```
fab:/$ ls
fab:/$ cd myworkspace.Workspace
fab:/myworkspace.Workspace$ get mynotebook.Notebook
fab:/myworkspace.Workspace$ quit
```

Type `help` for a list of available commands, and `quit` or `exit` to leave REPL mode.

## Switching Between Modes

There is no explicit mode switch command. The mode is determined by how you invoke the CLI:

- **Command-line mode** — run `fab <command>` with one or more arguments.
- **REPL mode** — run `fab` with no arguments.
