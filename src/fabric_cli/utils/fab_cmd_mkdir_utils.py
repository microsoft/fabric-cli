# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import base64
import json
import os
from argparse import Namespace

from fabric_cli.client import fab_api_azure as azure_api
from fabric_cli.client import fab_api_managedprivateendpoint as mpe_api
from fabric_cli.commands.fs.mkdir import fab_fs_mkdir_item as mkdir_item
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_hiearchy import Item
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_ui as utils_ui


def add_type_specific_payload(item: Item, args, payload):

    # Lowercase params
    params = args.params

    payload_dict = payload
    item_type = item.item_type
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))

    match item_type:

        case ItemType.LAKEHOUSE:
            if params.get("enableschemas", "False").lower() == "true":
                payload_dict["creationPayload"] = {"enableSchemas": True}

        case ItemType.WAREHOUSE:
            payload_dict["creationPayload"] = {
                "defaultCollation": "Latin1_General_100_BIN2_UTF8"
            }
            if params.get("enablecaseinsensitive", "False").lower() == "true":
                payload_dict["creationPayload"] = {
                    "defaultCollation": "Latin1_General_100_CI_AS_KS_WS_SC_UTF8"
                }

        case ItemType.KQL_DATABASE:
            _eventhouse_id = params.get("eventhouseid")
            _cluster_uri = params.get("clusteruri")
            _database_name = params.get("databasename")
            _type = params.get("dbtype", "readwrite")

            # ReadWrite DB
            if _eventhouse_id and _type.lower() == "readwrite":
                payload_dict["creationPayload"] = {
                    "databaseType": "ReadWrite",
                    "parentEventhouseItemId": _eventhouse_id,
                }
            # Shortcut DBS
            elif (
                _eventhouse_id
                and _type.lower() == "shortcut"
                and _cluster_uri
                and _database_name
            ):
                payload_dict["creationPayload"] = {
                    "databaseType": "Shortcut",
                    "parentEventhouseItemId": _eventhouse_id,
                    "sourceClusterUri": _cluster_uri,
                    "sourceDatabaseName": _database_name,
                }
            # Default
            else:
                fab_logger.log_warning(
                    "EventHouse not provided in params. Creating one first"
                )

                _initialize_batch_collection_for_dependency_creation(args)

                # Create a new Event House first
                _eventhouse = Item(
                    f"{item.short_name}_auto",
                    None,
                    item.parent,
                    "EventHouse",
                )
                _eventhouse_id = mkdir_item.exec(_eventhouse, args)

                payload_dict["creationPayload"] = {
                    "databaseType": "ReadWrite",
                    "parentEventhouseItemId": _eventhouse_id,
                }

        case ItemType.MIRRORED_DATABASE:
            _type = "genericmirror"
            payload_folder = "MirroredDatabase.GenericMirror"

            if params.get("mirrortype"):
                _type = params.get("mirrortype")
                match _type.lower():
                    case "azuresql":
                        fab_logger.log_warning(
                            "Requires system-assigned managed identity on"
                        )
                        payload_folder = "MirroredDatabase.AzureSQLDatabase"
                    case "azuresqlmi":
                        payload_folder = "MirroredDatabase.AzureSqlMI"
                    case "snowflake":
                        payload_folder = "MirroredDatabase.Snowflake"
                    case "cosmosdb":
                        payload_folder = "MirroredDatabase.CosmosDb"
                    case "genericmirror":
                        payload_folder = "MirroredDatabase.GenericMirror"

            payload_path = os.path.join(
                project_root,
                "commands",
                "fs",
                "payloads",
                payload_folder,
            )

            payload_dict["definition"] = _create_payload(payload_path, params, _type)

        case ItemType.REPORT:
            payload_folder = "Blank.Report"

            if params.get("semanticmodelid"):
                _semantic_model_id = params.get("semanticmodelid")
            else:
                fab_logger.log_warning(
                    "Semantic Model not provided in params. Creating one first"
                )

                _initialize_batch_collection_for_dependency_creation(args)

                # Create a new Semantic Model first
                _semantic_model = Item(
                    f"{item.short_name}_auto",
                    None,
                    item.parent,
                    "SemanticModel",
                )
                _semantic_model_id = mkdir_item.exec(_semantic_model, args)

            payload_path = os.path.join(
                project_root, "commands", "fs", "payloads", payload_folder
            )
            payload_dict["definition"] = _create_payload(
                payload_path, params, semantic_model_id=_semantic_model_id
            )

        case ItemType.SEMANTIC_MODEL:
            payload_folder = "Blank.SemanticModel"
            payload_path = os.path.join(
                project_root, "commands", "fs", "payloads", payload_folder
            )
            payload_dict["definition"] = _create_payload(payload_path, params)

        case ItemType.NOTEBOOK:
            # markdown metadata, same as web
            payload_dict["definition"] = {
                "parts": [
                    {
                        "path": "notebook-content.py",
                        "payload": "IyBGYWJyaWMgbm90ZWJvb2sgc291cmNlCgojIE1FVEFEQVRBICoqKioqKioqKioqKioqKioqKioqCgojIE1FVEEgewojIE1FVEEgICAia2VybmVsX2luZm8iOiB7CiMgTUVUQSAgICAgIm5hbWUiOiAic3luYXBzZV9weXNwYXJrIgojIE1FVEEgICB9LAojIE1FVEEgICAiZGVwZW5kZW5jaWVzIjoge30KIyBNRVRBIH0KCiMgQ0VMTCAqKioqKioqKioqKioqKioqKioqKgoKIyBXZWxjb21lIHRvIHlvdXIgbmV3IG5vdGVib29rCiMgVHlwZSBoZXJlIGluIHRoZSBjZWxsIGVkaXRvciB0byBhZGQgY29kZSEKCgojIE1FVEFEQVRBICoqKioqKioqKioqKioqKioqKioqCgojIE1FVEEgewojIE1FVEEgICAibGFuZ3VhZ2UiOiAicHl0aG9uIiwKIyBNRVRBICAgImxhbmd1YWdlX2dyb3VwIjogInN5bmFwc2VfcHlzcGFyayIKIyBNRVRBIH0K",
                        "payloadType": "InlineBase64",
                    }
                ]
            }

        case ItemType.MOUNTED_DATA_FACTORY:
            subscription_id = params.get("subscriptionid")
            resource_group = params.get("resourcegroup")
            factory_name = params.get("factoryname")

            data = {
                "dataFactoryResourceId": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DataFactory/factories/{factory_name}"
            }
            json_str = json.dumps(data)
            encoded_content = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

            payload_dict["definition"] = {
                "parts": [
                    {
                        "path": "mountedDataFactory-content.json",
                        "payload": encoded_content,
                        "payloadType": "InlineBase64",
                    }
                ]
            }

    return payload_dict


def _create_payload(directory, params, type=None, semantic_model_id=None, encode=True):
    parts = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get full path and relative path
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, directory)

            if semantic_model_id and "definition.pbir" in full_path:

                # Change byPath to byConnection
                with open(full_path, "rb") as file:
                    data = json.load(file)

                data["datasetReference"]["byPath"] = None

                data["datasetReference"]["byConnection"] = {
                    "connectionString": "Data Source=powerbi://api.powerbi.com/v1.0/myorg/mkdir;Initial Catalog=r3;Integrated Security=ClaimsToken",
                    "pbiServiceModelId": None,
                    "pbiModelVirtualServerName": "sobe_wowvirtualserver",
                    "pbiModelDatabaseName": semantic_model_id,
                    "name": "EntityDataSource",
                    "connectionType": "pbiServiceXmlaStyleLive",
                }

                # Encode the file content to base64
                json_str = json.dumps(data)
                encoded_content = base64.b64encode(json_str.encode("utf-8")).decode(
                    "utf-8"
                )

            # Mirrored database
            elif type and type.lower() != "genericmirror":

                # Change payload based on params
                with open(full_path, "rb") as file:
                    data = json.load(file)

                data["properties"]["source"]["typeProperties"]["connection"] = (
                    params.get("connectionid")
                )
                if params.get("database"):
                    data["properties"]["source"]["typeProperties"]["database"] = (
                        params.get("database")
                    )
                data["properties"]["target"]["typeProperties"]["defaultSchema"] = (
                    params.get("defaultschema", "dbo")
                )
                if params.get("mountedtables"):
                    _mounted_tables = []
                    for table in params.get("mountedtables").split(","):
                        schema_name, table_name = table.split(".")
                        _mounted_tables.append(
                            {
                                "source": {
                                    "typeProperties": {
                                        "schemaName": schema_name,
                                        "tableName": table_name,
                                    }
                                }
                            }
                        )
                    data["properties"]["mountedTables"] = _mounted_tables

                # Encode the file content to base64
                json_str = json.dumps(data)
                encoded_content = base64.b64encode(json_str.encode("utf-8")).decode(
                    "utf-8"
                )

            else:

                # Encode the file content to base64
                with open(full_path, "rb") as file:
                    content = file.read()
                    encoded_content = (
                        base64.b64encode(content).decode("utf-8") if encode else content
                    )

            # Add file data to parts
            parts.append(
                {
                    "path": relative_path.replace(
                        "\\", "/"
                    ),  # Ensure cross-platform path formatting
                    "payload": encoded_content,
                    "payloadType": "InlineBase64",
                }
            )

    # Create the final JSON structure
    payload_structure = {"parts": parts}
    return payload_structure


def get_params_per_item_type(item: Item):
    required_params = []
    optional_params = []

    match item.item_type:
        case ItemType.LAKEHOUSE:
            optional_params = ["enableSchemas"]
        case ItemType.WAREHOUSE:
            optional_params = ["enableCaseInsensitive"]
        case ItemType.KQL_DATABASE:
            optional_params = ["dbType", "eventhouseId", "clusterUri", "databaseName"]
        case ItemType.MIRRORED_DATABASE:
            optional_params = [
                "mirrorType",
                "connectionId",
                "database",
                "defaultSchema",
                "mountedTables",
            ]
        case ItemType.REPORT:
            optional_params = ["semanticModelId"]
        case ItemType.MOUNTED_DATA_FACTORY:
            required_params = ["subscriptionId", "resourceGroup", "factoryName"]

    return required_params, optional_params


def show_params_desc(params, type, required_params=None, optional_params=None):

    if not params:
        required_params_filtered = [p for p in (required_params or []) if p is not None]
        optional_params_filtered = [p for p in (optional_params or []) if p is not None]

        # Construct the parts of the message conditionally
        required_param_list = "\n  ".join(sorted(required_params_filtered))
        optional_param_list = "\n  ".join(sorted(optional_params_filtered))

        if required_params is None and optional_params is None:
            message_parts = [f"No parameters for '.{type}'"]
        else:
            message_parts = [
                f"Params for '.{type}'. Use key=value separated by commas."
            ]

            if required_param_list:
                message_parts.append(f"\n\nRequired params:\n  {required_param_list}")
            if optional_param_list:
                message_parts.append(f"\n\nOptional params:\n  {optional_param_list}")

        utils_ui.print("".join(message_parts) + "\n")

        return True
    elif params.get("run"):
        return False


def check_required_params(params, required_params):

    for mandatory_param in required_params:
        if "." in mandatory_param:
            a, b = mandatory_param.split(".")

            if (
                params.get(a.lower(), None) == None
                or params.get(a.lower()).get(b.lower()) == None
            ):
                raise FabricCLIError(
                    f"Missing mandatory params '{required_params}'. Please provide using -P/--params",
                    fab_constant.ERROR_INVALID_INPUT,
                )
        elif params.get(mandatory_param.lower(), None) == None:
            raise FabricCLIError(
                f"Missing mandatory params '{required_params}'. Please provide using -P/--params",
                fab_constant.ERROR_INVALID_INPUT,
            )


def _get_params_per_cred_type(cred_type, is_on_premises_gateway):
    match cred_type:
        case "Anonymous" | "WindowsWithoutImpersonation" | "WorkspaceIdentity":
            return []
        case "Basic" | "Windows":
            if is_on_premises_gateway:
                return ["values"]
            else:
                return ["username", "password"]
        case "Key":
            return ["key"]
        case "OAuth2":
            raise FabricCLIError(
                "OAuth2 credential type is not supported",
                fab_constant.ERROR_NOT_SUPPORTED,
            )
        case "ServicePrincipal":
            return [
                "servicePrincipalClientId",
                "servicePrincipalSecret",
                "tenantId",
            ]
        case "SharedAccessSignature":
            return ["token"]
        case _:
            utils_ui.print_warning(
                f"Unsupported credential type {cred_type}. Skipping validation"
            )
            return []
    

def _validate_credential_params(cred_type, provided_cred_params, is_on_premises_gateway):
    ignored_params = []
    params = {}
    param_keys = _get_params_per_cred_type(cred_type, is_on_premises_gateway)

    missing_params = [
        key for key in param_keys if key.lower() not in provided_cred_params
    ]
    if len(missing_params) > 0:
        raise FabricCLIError(
            f"Missing parameters for credential type {cred_type}: {missing_params}",
            fab_constant.ERROR_INVALID_INPUT,
        )

    ignored_params = [
        key
        for key in provided_cred_params
        if key not in [k.lower() for k in param_keys]
    ]
    if len(ignored_params) > 0:
        utils_ui.print_warning(
            f"Ignoring unsupported parameters for credential type {cred_type}: {ignored_params}"
        )
    if is_on_premises_gateway:
        provided_cred_params["values"] = _validate_and_get_on_premises_gateway_credential_values(provided_cred_params.get("values"))

    for key in param_keys:
        params[key] = provided_cred_params[key.lower()]

    return params

def _validate_and_get_on_premises_gateway_credential_values(cred_values):
    for item in cred_values:
        if not isinstance(item, dict):
            raise FabricCLIError(
                ErrorMessages.Common.invalid_onpremises_gateway_values(),
                fab_constant.ERROR_INVALID_INPUT,
            )
        
    param_values_keys = ["gatewayId", "encryptedCredentials"]
    missing_params = [
        key for key in param_values_keys 
        if not all(key.lower() in {k.lower() for k in item.keys()} for item in cred_values)
    ]
    if len(missing_params) > 0:
        raise FabricCLIError(
            ErrorMessages.Common.missing_onpremises_gateway_parameters(missing_params),
            fab_constant.ERROR_INVALID_INPUT,
    )

    ignored_params = [
        key
        for item in cred_values
        for key in item.keys()
        if key not in [k.lower() for k in param_values_keys]
    ]
    if len(ignored_params) > 0:
        utils_ui.print_warning(
            f"Ignoring unsupported parameters for on-premises gateway: {ignored_params}"
    )

    return [{key: item[key.lower()] for key in param_values_keys if key.lower() in item} for item in cred_values]


def get_connection_config_from_params(payload, con_type, con_type_def, params):
    connection_request = payload

    # Get and set Privacy Level
    supported_privacy_levels = ["None", "Organizational", "Private", "Public"]
    privacy_level = params.get("privacylevel", "None")
    if privacy_level not in supported_privacy_levels:
        raise FabricCLIError(
            f"Invalid privacy level. Supported privacy levels are {supported_privacy_levels}",
            fab_constant.ERROR_INVALID_INPUT,
        )
    connection_request["privacyLevel"] = privacy_level

    """
    Check and build the connection details:
     "connectionDetails": {
       "type": "SQL",
       "creationMethod": "SQL",
       "parameters": [
         {
           "dataType": "Text",
           "name": "server",
           "value": "contoso.database.windows.net"
         },
         {
           "dataType": "Text",
           "name": "database",
           "value": "sales"
         }
       ]
     }
    """
    if not params.get("connectiondetails"):
        raise FabricCLIError(
            "Connection details are required", fab_constant.ERROR_INVALID_INPUT
        )
    provided_params = params.get("connectiondetails").get("parameters")

    supported_creation_methods = [m["name"] for m in con_type_def["creationMethods"]]
    if not params.get("connectiondetails").get("creationmethod"):
        if provided_params:
            # We default to pick the first creation method that matches the provided parameters
            creation_method = next(
                (
                    item
                    for item in con_type_def["creationMethods"]
                    if all(
                        (k.get("name") or "").lower()
                        in [key.lower() for key in params.get("connectiondetails").get("parameters").keys()]
                        for k in item["parameters"]
                    )
                ),
                None,
            )
            if creation_method is not None:
                utils_ui.print_info(
                    f"Inferred creation method '{creation_method['name']}' from provided parameters"
                )
        else:
            raise FabricCLIError(
                ErrorMessages.Common.missing_connection_creation_method_or_parameters(
                    supported_creation_methods
                ),
                fab_constant.ERROR_INVALID_INPUT,
            )
    else:
        provided_method = params.get("connectiondetails").get("creationmethod")
        creation_method = next(
            (
                item
                for item in con_type_def["creationMethods"]
                if item["name"].lower() == provided_method.lower()
            ),
            None,
        )

    if creation_method is None:
        raise FabricCLIError(
            ErrorMessages.Common.invalid_creation_method_for_connection(
                con_type, supported_creation_methods
            ),
            fab_constant.ERROR_INVALID_INPUT,
        )

    parsed_params = []
    missing_params = []
    if not provided_params:
        # Get required and optional parameters from the creation method
        req_params_str = ", ".join(
            [p["name"] for p in creation_method["parameters"] if p["required"]]
        )
        opt_params_str = ", ".join(
            [p["name"] for p in creation_method["parameters"] if not p["required"]]
        )
        raise FabricCLIError(
            f"Parameters are required for the connection creation method. Required parameters are: {req_params_str}. Optional parameters are: {opt_params_str}",
            fab_constant.ERROR_INVALID_INPUT,
        )
    for param in creation_method["parameters"]:
        p_name = param["name"]
        if p_name.lower() not in provided_params and param["required"]:
            c_method = creation_method["name"]
            missing_params.append(p_name)
        if p_name.lower() in provided_params:
            parsed_params.append(
                {
                    "dataType": param["dataType"],
                    "name": p_name,
                    "value": provided_params[p_name.lower()],
                }
            )
    for param in provided_params:
        if param not in [p["name"].lower() for p in creation_method["parameters"]]:
            c_method = creation_method["name"]
            utils_ui.print_warning(
                f"Parameter {param} is not used by the creation method {c_method} and will be ignored"
            )

    if missing_params:
        missing_params_str = ", ".join(missing_params)
        raise FabricCLIError(
            f"Missing parameter(s) {missing_params_str} for creation method {c_method}",
            fab_constant.ERROR_INVALID_INPUT,
        )

    connection_request["connectionDetails"] = {
        "type": con_type,
        "creationMethod": creation_method["name"],
        "parameters": parsed_params,
    }

    """
    Check that the provided credential type is supported by the connection type:
     "credentialDetails": {
      "credentialType": "Basic",
       "singleSignOnType": "None",
       "connectionEncryption": "NotEncrypted",
       "skipTestConnection": false,
       "credentials": {
         "credentialType": "Basic",
         "username": "admin",
         "password": "********"
       }
    }
    or in case of OnPremisesGateway:
    "credentialDetails": {
        .....,
        "credentials": {
        "credentialType": "Basic",
        "values": [{gatewayId: "gatewayId", encryptedCredentials: "**********"}] 
        }
        }
    """
    sup_cred_types = ", ".join(con_type_def["supportedCredentialTypes"])
    if not params.get("credentialdetails"):
        raise FabricCLIError(
            f"Credential details are required. Supported credential types: {sup_cred_types}",
            fab_constant.ERROR_INVALID_INPUT,
        )
    provided_cred_type = params.get("credentialdetails").get("type")
    if not provided_cred_type:
        raise FabricCLIError(
            f"Credential type is required. Supported credential types: {sup_cred_types}",
            fab_constant.ERROR_INVALID_INPUT,
        )
    cred_type = next(
        (
            item
            for item in con_type_def["supportedCredentialTypes"]
            if item.lower() == provided_cred_type.lower()
        ),
        None,
    )
    if cred_type is None:
        raise FabricCLIError(
            f"Invalid credential type. Supported Credentials for {con_type}: {sup_cred_types}",
            fab_constant.ERROR_INVALID_INPUT,
        )
    provided_cred_params = params.get("credentialdetails", {})
    provided_cred_params.pop("type")
    # Get the single sign on type, use None as default
    singleSignOnType = provided_cred_params.get("singlesignontype", "None")
    # Remove if present
    if "singlesignontype" in provided_cred_params:
        provided_cred_params.pop("singlesignontype")
    encryption = provided_cred_params.get("connectionencryption", "Any")
    if "connectionencryption" in provided_cred_params:
        provided_cred_params.pop("connectionencryption")
    skipTestConnection = provided_cred_params.get("skiptestconnection", False)
    if "skiptestconnection" in provided_cred_params:
        provided_cred_params.pop("skiptestconnection")

    is_on_premises_gateway = connection_request.get("connectivityType").lower() == "onpremisesgateway"
    connection_params = _validate_credential_params(cred_type, provided_cred_params, is_on_premises_gateway)

    connection_request["credentialDetails"] = {
        "singleSignOnType": singleSignOnType,
        "connectionEncryption": encryption,
        "skipTestConnection": skipTestConnection,
        "credentials": connection_params,
    }
    connection_request["credentialDetails"]["credentials"]["credentialType"] = cred_type

    if is_on_premises_gateway:
        connection_request["credentialDetails"]["credentials"]["values"] = connection_params.get("values")

    return connection_request


def find_vnet_subnet(vnet_name, subnet_name) -> tuple:
    args = type("", (), {})()
    api_response = azure_api.list_subscriptions_azure(args)
    if api_response.status_code != 200:
        raise FabricCLIError(
            "Failed to list subscriptions", fab_constant.ERROR_NOT_FOUND
        )
    subscriptions = json.loads(api_response.text)["value"]
    for sub in subscriptions:
        sub_id = sub["id"].split("/")[-1]
        _args = type("", (), {})()
        _args.subscription_id = sub_id
        vnet_req = azure_api.list_vnets_azure(_args)
        vnets = json.loads(vnet_req.text)["value"]
        vnet = next(
            (item for item in vnets if item["name"].lower() == vnet_name.lower()),
            None,
        )
        if vnet:
            # Check if the subnet exists
            subnets = vnet["properties"]["subnets"]
            subnet = next(
                (
                    item
                    for item in subnets
                    if item["name"].lower() == subnet_name.lower()
                ),
                None,
            )
        if vnet and subnet:
            subnet_id = subnet["id"]
            rg_name = subnet_id.split("/")[4]
            return sub_id, rg_name

    return None, None


def lowercase_keys(data):
    if isinstance(data, dict):
        return {k.lower(): lowercase_keys(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [lowercase_keys(item) for item in data]
    else:
        return data


def validate_spark_pool_params(params):
    # Node size options
    allowed_node_sizes = {"small", "medium", "large", "xlarge", "xxlarge"}

    # Validate and set nodesize
    if params.get("nodesize"):
        nodesize = params.get("nodesize").lower()
        if nodesize not in allowed_node_sizes:
            raise FabricCLIError(
                f"Invalid nodesize '{nodesize}'. Allowed values are: {', '.join(allowed_node_sizes)}",
                fab_constant.ERROR_INVALID_INPUT,
            )

    # Validate autoscale
    if params.get("autoscale.maxnodecount") and params.get("autoscale.minnodecount"):
        if int(params.get("autoscale.maxnodecount")) < int(
            params.get("autoscale.minnodecount")
        ):
            raise FabricCLIError(
                "maxNodeCount must be >= minNodeCount",
                fab_constant.ERROR_INVALID_INPUT,
            )


def find_mpe_connection(managed_private_endpoint, targetprivatelinkresourceid):
    args = Namespace()
    args.resource_uri = targetprivatelinkresourceid
    response = mpe_api.list_private_endpoints_by_azure_resource(args)
    if response.status_code == 200:
        connections = json.loads(response.text)["value"]
        ws_id = managed_private_endpoint.workspace.id
        conn_name = f"{ws_id}.{managed_private_endpoint.short_name}"
        # Find the connection that matches the name
        conn = next(
            (
                item
                for item in connections
                if item["properties"]["privateEndpoint"]["id"].lower().split("/")[-1]
                == conn_name.lower()
            ),
            None,
        )
        return conn

    return None

def _initialize_batch_collection_for_dependency_creation(args):
    if not hasattr(args, 'output_batch'):
        args.output_batch = {
            'items': [],
            'names': []
        }