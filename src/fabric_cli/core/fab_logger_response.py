# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

_ITEM_DEFINITION_PART_KEYS = {"path", "payload", "payloadType"}


def process_response(parsed_json, ctxt_cmd: str):
    """Process an HTTP response for logging based on the command context."""
    if not parsed_json or not isinstance(parsed_json, dict):
        return parsed_json

    match ctxt_cmd:
        case "bulk-export":
            return _process_bulk_export(parsed_json)
        case "export":
            return _process_export(parsed_json)
        case _:
            return parsed_json


def _process_bulk_export(parsed_json: dict):
    if (
        "itemDefinitionsIndex" in parsed_json
        and "definitionParts" in parsed_json
        and isinstance(parsed_json["definitionParts"], list)
        and all(
            isinstance(part, dict) and _ITEM_DEFINITION_PART_KEYS <= part.keys()
            for part in parsed_json["definitionParts"]
        )
    ):
        return {
            k: ("redacted_from_log" if k == "definitionParts" else v)
            for k, v in parsed_json.items()
        }

    return parsed_json


def _process_export(parsed_json: dict):
    if (
        "definition" in parsed_json
        and "parts" in parsed_json["definition"]
        and isinstance(parsed_json["definition"]["parts"], list)
        and all(
            isinstance(part, dict) and _ITEM_DEFINITION_PART_KEYS <= part.keys()
            for part in parsed_json["definition"]["parts"]
        )
    ):
        definition = {
            k: v for k, v in parsed_json["definition"].items() if k != "parts"
        }
        definition["parts"] = [
            {k: ("redacted_from_log" if k == "payload" else v) for k, v in part.items()}
            for part in parsed_json["definition"]["parts"]
        ]
        return {"definition": definition}

    return parsed_json
