# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Resolve help controls and describe registered parsers without executing commands."""

import argparse
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from fabric_cli import __version__


@dataclass
class HelpRequest:
    """A help target and its explicit selectors, before output-format resolution."""

    parser: argparse.ArgumentParser
    selectors: list[str] = field(default_factory=list)
    error: Optional[str] = None


def child_parsers(
    parser: argparse.ArgumentParser,
) -> Iterator[tuple[str, argparse.ArgumentParser, list[str], str]]:
    """Yield immediate canonical children once, with aliases and descriptions."""
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        seen: set[int] = set()
        descriptions = {entry.dest: entry.help for entry in action._get_subactions()}
        for name, child in action.choices.items():
            if id(child) in seen:
                continue
            seen.add(id(child))
            aliases = [
                alias
                for alias, candidate in action.choices.items()
                if candidate is child and alias != name
            ]
            yield name, child, aliases, descriptions.get(
                name
            ) or child.description or name


def canonical_command(parser: argparse.ArgumentParser) -> str:
    """Return the canonical command name used in help response envelopes."""
    parts = parser.prog.split()[1:]
    return " ".join(parts) or "fab"


def _is_option(token: str) -> bool:
    if not token.startswith("-") or token == "-":
        return False
    try:
        float(token)
    except ValueError:
        return True
    return False


def resolve_help(
    parser: argparse.ArgumentParser, tokens: list[str]
) -> Optional[HelpRequest]:
    """Find help while respecting registered option arity and literal value boundaries.

    Operation requiredness, choices and value validators deliberately do not run here.
    Structural errors are retained only if the request actually asks for help.
    """
    request = HelpRequest(parser)
    current = parser
    found = False
    index = 0
    positional_index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            break
        options = current._option_string_actions
        spelling, separator, attached = token.partition("=")
        action = options.get(spelling)
        if action is None and token.startswith("-") and not token.startswith("--"):
            # argparse permits attached short-option values, e.g. -c"mkdir --help".
            short = options.get(token[:2])
            if short is not None and short.nargs != 0:
                action = short
                spelling, separator, attached = token[:2], "=", token[2:]
        if action is not None:
            if isinstance(action, argparse._HelpAction):
                found = True
                if separator:
                    request.error = "A help flag does not accept a value."
                index += 1
                continue
            if action.nargs == 0:
                if separator:
                    request.error = "A boolean flag does not accept a value."
                index += 1
                continue
            values = [attached] if separator else []
            index += 1
            nargs = action.nargs
            limit = (
                1 if nargs in (None, "?") else nargs if isinstance(nargs, int) else None
            )
            while not separator and index < len(tokens):
                value = tokens[index]
                if limit is not None and len(values) >= limit:
                    break
                if value == "--" or (
                    _is_option(value) and spelling not in ("-c", "--command")
                ):
                    break
                values.append(value)
                index += 1
            minimum = (
                0 if nargs in ("?", "*") else nargs if isinstance(nargs, int) else 1
            )
            if len(values) < minimum:
                request.error = "A supplied option is missing its value."
            if action.dest == "output_format":
                request.selectors.extend(values)
            continue
        if _is_option(token):
            request.error = "An unknown option was supplied."
            index += 1
            continue
        children = [
            (name, child, aliases) for name, child, aliases, _ in child_parsers(current)
        ]
        child = next(
            (child for name, child, aliases in children if token in [name, *aliases]),
            None,
        )
        if children:
            if child is None or found:
                request.error = (
                    "An unknown help target or unexpected argument was supplied."
                )
            else:
                current = child
                request.parser = child
                positional_index = 0
        else:
            positionals = [
                action for action in current._actions if not action.option_strings
            ]
            if positional_index >= len(positionals):
                request.error = "An unexpected argument was supplied."
            elif positionals[positional_index].nargs not in ("+", "*"):
                positional_index += 1
        index += 1
    return request if found else None


def _describe_action(action: argparse.Action) -> dict[str, Any]:
    boolean = isinstance(
        action,
        (argparse._HelpAction, argparse._StoreTrueAction, argparse._StoreFalseAction),
    )
    value_type = (
        "boolean"
        if boolean
        else (
            "integer"
            if action.type is int
            else "number" if action.type is float else "string"
        )
    )
    metadata = getattr(action, "fab_help", {})
    entry: dict[str, Any] = {
        "name": action.dest,
        "type": value_type,
        "required": bool(action.required),
        "description": action.help or f"Value for {action.dest.replace('_', ' ')}.",
    }
    if action.option_strings:
        name = next(
            (option for option in action.option_strings if option.startswith("--")),
            action.option_strings[0],
        )
        entry["name"] = name
        entry["aliases"] = [
            option for option in action.option_strings if option != name
        ]
        if not boolean:
            entry["repeat_behavior"] = (
                "append" if isinstance(action, argparse._AppendAction) else "replace"
            )
            if action.nargs in ("?", "*"):
                entry["value_optional"] = True
    if action.choices is not None:
        entry["choices"] = list(action.choices)
    if (
        isinstance(action.default, (str, int, float, bool))
        and action.default != argparse.SUPPRESS
    ):
        entry["default"] = action.default
    entry.update(metadata)
    return entry


def build_help_data(parser: argparse.ArgumentParser) -> dict[str, Any]:
    """Generate the versioned public help payload from a registered parser."""
    command = canonical_command(parser)
    args: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    help_spellings: list[str] = []
    for action in parser._actions:
        if (
            isinstance(action, argparse._SubParsersAction)
            or action.help == argparse.SUPPRESS
        ):
            continue
        if isinstance(action, argparse._HelpAction):
            help_spellings.extend(action.option_strings)
            continue
        entry = _describe_action(action)
        (flags if action.option_strings else args).append(entry)
    if help_spellings:
        flags.insert(
            0,
            {
                "name": "--help",
                "aliases": [
                    spelling for spelling in help_spellings if spelling != "--help"
                ],
                "type": "boolean",
                "required": False,
                "description": "Show command help.",
            },
        )
    examples: list[dict[str, str]] = []
    description = "Example invocation."
    for raw in getattr(parser, "fab_examples", []):
        example = raw.strip()
        if example.startswith("#"):
            description = example.lstrip("#").strip()
        elif example:
            invocation = example.removeprefix("$").strip()
            if not invocation.startswith("fab "):
                invocation = f"fab {invocation}"
            examples.append({"description": description, "command": invocation})
            if len(examples) == 2:
                break
    notes = list(getattr(parser, "fab_notes", []))
    links = ["https://aka.ms/fabric-cli"]
    for item in getattr(parser, "fab_learnmore", []):
        if item.startswith(("https://", "http://")):
            if item not in links:
                links.append(item)
        elif item != "_":
            notes.append(item)
    path = "" if command == "fab" else f" {command}"
    usage_args = " ".join(
        f"<{entry['name']}>" if entry["required"] else f"[<{entry['name']}>]"
        for entry in args
    )
    children = list(child_parsers(parser))
    suffix = " <command>" if children else ""
    if usage_args:
        suffix += f" {usage_args}"
    return {
        "schema_version": "1.0",
        "cli_version": __version__,
        "description": parser.description
        or getattr(parser, "fab_description", None)
        or command,
        "usage": f"fab{path}{suffix} [flags]",
        "args": args,
        "flags": flags,
        "aliases": list(getattr(parser, "fab_aliases", [])),
        "subcommands": [
            {"name": name, "aliases": aliases, "description": description}
            for name, _, aliases, description in children
        ],
        "examples": examples,
        "notes": notes,
        "learn_more": links,
    }
