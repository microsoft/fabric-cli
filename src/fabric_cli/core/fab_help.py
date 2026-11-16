# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Build text and JSON help from registered command parsers."""

import argparse
import re
from copy import copy
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from fabric_cli import __version__


class CustomHelpFormatter(argparse.HelpFormatter):
    """Format registered command help as text or JSON-ready metadata."""

    def __init__(
        self,
        prog: str,
        fab_examples: Optional[list[str]] = None,
        fab_aliases: Optional[list[str]] = None,
        fab_learnmore: Optional[list[str]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(prog, *args, **kwargs)
        self.fab_examples = fab_examples or []
        self.fab_aliases = fab_aliases or []
        self.fab_learnmore = fab_learnmore or []

    def _format_args(self, action: argparse.Action, default_metavar: str) -> str:
        if action.nargs in ("*", "+"):
            return "" if action.option_strings else f"<{action.dest}>"
        return super()._format_args(action, default_metavar)

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.metavar and action.nargs in (None, "?"):
            return ", ".join(action.option_strings)
        if action.nargs in ("*", "+"):
            metavar = self._format_args(action, action.dest)
            return ", ".join(action.option_strings) + metavar
        return super()._format_action_invocation(action)

    def format_help(self) -> str:
        """Implement argparse's text-help hook."""
        return self.fab_help_text()

    def fab_help_text(self) -> str:
        """Return formatted text help without producing JSON or printing output."""
        help_message = super().format_help()
        help_message = help_message.replace("usage:", "Usage:")
        help_message = help_message.replace("positional arguments:", "Arg(s):")
        help_message = help_message.replace("options:", "Flags:")
        help_message = re.sub(
            r"\s*-h, --help\s*(Show help for command|show this help message and exit)?",
            "",
            help_message,
        )
        help_message = help_message.replace("  -help\n", "")
        help_message = help_message.replace("[-h] ", "")
        help_message = help_message.replace("[-help] ", "")
        help_message = help_message.replace("[-help]", "")

        if "Flags:" in help_message:
            flags_section = help_message.split("Flags:")[1].strip()
            if not flags_section:
                help_message = help_message.replace("\nFlags:\n", "")

        if self.fab_aliases:
            help_message += "\nAliases:\n"
            for alias in self.fab_aliases:
                help_message += f"  {alias}\n"

        if self.fab_examples:
            help_message += "\nExamples:\n"
            for example in self.fab_examples:
                if "#" in example:
                    help_message += f"  \033[38;5;243m{example}\033[0m\n"
                else:
                    help_message += f"  {example}\n"

        if self.fab_learnmore:
            help_message += "\nLearn more:\n"
            if self.fab_learnmore != ["_"]:
                for learn_more in self.fab_learnmore:
                    help_message += f"  {learn_more}\n"
            help_message += "  For more usage examples, see https://aka.ms/fabric-cli\n"

        return help_message + "\n"

    @staticmethod
    def fab_help_json_format(parser: argparse.ArgumentParser) -> dict[str, Any]:
        """Generate the versioned JSON help payload directly from a registered parser."""
        command = " ".join(parser.prog.split())
        command = command.removeprefix("fab ") or "fab"
        args: list[dict[str, Any]] = []
        flags: list[dict[str, Any]] = []
        required_flags: list[str] = []
        formatter = argparse.HelpFormatter(parser.prog)
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
            if action.option_strings and action.required:
                required_flag = entry["name"]
                if action.nargs != 0:
                    usage_action = copy(action)
                    usage_action.metavar = action.metavar or f"<{action.dest}>"
                    required_flag += (
                        f" {formatter._format_args(usage_action, action.dest)}"
                    )
                required_flags.append(required_flag)
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
                if "interactive mode" in description.lower():
                    invocation = invocation.removeprefix("fab ")
                elif not invocation.startswith("fab "):
                    invocation = f"fab {invocation}"
                examples.append({"description": description, "command": invocation})
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
        if required_flags:
            suffix += f" {' '.join(required_flags)}"
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


@dataclass
class HelpRequest:
    """A selected command parser and its requested output formats."""

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


def _describe_action(action: argparse.Action) -> dict[str, Any]:
    boolean = isinstance(
        action,
        (argparse._HelpAction, argparse._StoreConstAction),
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
