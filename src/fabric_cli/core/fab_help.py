# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Structured help metadata derived from the registered argument parsers."""

import argparse
from typing import Any

from fabric_cli import __version__
from fabric_cli.parsers.fab_parser_validators import validate_positive_int


def _argument_metadata(action: argparse.Action) -> dict[str, Any]:
    name = next(
        (option for option in action.option_strings if option.startswith("--")),
        action.option_strings[0] if action.option_strings else action.dest,
    )
    value_type = "string"
    if action.nargs == 0:
        value_type = "boolean"
    elif action.type in (int, validate_positive_int):
        value_type = "integer"
    elif action.type is float:
        value_type = "number"
    elif action.type is bool:
        value_type = "boolean"

    description = action.help or f"Specify {action.dest.replace('_', ' ')}."
    if isinstance(action, argparse._HelpAction):
        description = "Show command help."
    elif name == "--output_format":
        description = "Output format. Uses saved configuration when omitted."
    elif name == "--version":
        description = "Show the installed CLI version."

    result: dict[str, Any] = {
        "name": name,
        "type": value_type,
        "required": bool(action.required),
        "description": description,
    }
    if action.option_strings:
        result["aliases"] = [
            option for option in action.option_strings if option != name
        ]
        if action.nargs != 0:
            result["value_optional"] = action.nargs in ("?", "*")
            result["repeat_behavior"] = (
                "append"
                if isinstance(action, (argparse._AppendAction, argparse._ExtendAction))
                else "replace"
            )
    if action.choices is not None:
        result["choices"] = list(action.choices)
    return result


def build_help_data(parser: argparse.ArgumentParser) -> dict[str, Any]:
    """Return version 1.0 help metadata without executing a command."""
    args: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    subcommands: list[dict[str, Any]] = []
    for action in parser._actions:
        if action.help == argparse.SUPPRESS:
            continue
        if isinstance(action, argparse._SubParsersAction):
            seen = set()
            for name, child in action.choices.items():
                if child in seen:
                    continue
                seen.add(child)
                subcommands.append(
                    {
                        "name": name,
                        "description": getattr(child, "fab_description", None)
                        or child.description
                        or f"Help for {name}.",
                        "aliases": [
                            alias
                            for alias, target in action.choices.items()
                            if target is child and alias != name
                        ],
                    }
                )
        elif isinstance(action, argparse._HelpAction):
            if not any(flag["name"] == "--help" for flag in flags):
                metadata = _argument_metadata(action)
                metadata["name"] = "--help"
                metadata["aliases"] = [
                    option
                    for help_action in parser._actions
                    if isinstance(help_action, argparse._HelpAction)
                    for option in help_action.option_strings
                    if option != "--help"
                ]
                flags.append(metadata)
        elif action.option_strings:
            flags.append(_argument_metadata(action))
        else:
            args.append(_argument_metadata(action))

    examples: list[dict[str, str]] = []
    description = ""
    for entry in getattr(parser, "fab_examples", []):
        entry = entry.strip()
        if entry.startswith("#"):
            description = entry.lstrip("#").strip()
        elif entry:
            command = entry.removeprefix("$").strip()
            if not command.startswith("fab "):
                command = f"fab {command}"
            examples.append(
                {"description": description or "Run this command.", "command": command}
            )

    notes = []
    learn_more = []
    for entry in getattr(parser, "fab_learnmore", []):
        if entry.startswith(("https://", "http://")):
            learn_more.append(entry)
        elif entry != "_" and entry.strip():
            notes.append(entry.strip())
    if "https://aka.ms/fabric-cli" not in learn_more:
        learn_more.append("https://aka.ms/fabric-cli")

    command = " ".join(parser.prog.split()[1:])
    usage = f"fab {command}".rstrip()
    for argument in args:
        placeholder = f"<{argument['name']}>"
        usage += f" {placeholder}" if argument["required"] else f" [{placeholder}]"
    if subcommands:
        usage += " <command>"
    usage += " [flags]"

    return {
        "schema_version": "1.0",
        "cli_version": __version__,
        "description": getattr(parser, "fab_description", None)
        or parser.description
        or f"Help for {command or 'Fabric CLI'}.",
        "usage": usage,
        "args": args,
        "flags": flags,
        "aliases": getattr(parser, "fab_aliases", []),
        "subcommands": subcommands,
        "examples": examples,
        "notes": notes,
        "learn_more": learn_more,
    }
