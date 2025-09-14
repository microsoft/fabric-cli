# CLI Modes

The Fabric CLI supports two primary modes to accommodate a variety of workflows: **command line** and **interactive**. The selected mode is preserved between sessions. If you exit and login to the CLI later, it will resume in the same mode you last used.

Use the following command to see the current stored mode setting:

```
fab config get mode
```

## Command Line Mode

Command line mode is best suited for scripted tasks, automation, or when you prefer running single commands without a prompt.

Typing commands directly in the terminal replicates typical UNIX-style usage.

Use the following command to switch the CLI into command line mode:

```
fab config set mode command_line
```

You will be required to log in again after switching modes.

## Interactive Mode

Interactive mode provides a shell-like environment in which you can run Fabric CLI commands directly without the `fab` prefix.

Upon entering interactive mode, you see a `fab:/$` prompt. Commands are executed one by one without needing to type `fab` before each command, giving you a more guided experience.

Use the following command to switch the CLI into interactive mode:

```
fab config set mode interactive
```

You will be required to log in again after switching modes.

## Switching Between Modes

To switch from one mode to the other, enter:

```
fab config set mode <desired_mode>
```

where `<desired_mode>` is either `command_line` or `interactive`. Because the Fabric CLI needs to establish new authentication for each mode, you must re-authenticate after switching. The mode choice then remains in effect until you change it again.