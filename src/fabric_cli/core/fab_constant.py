# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli import __version__
from fabric_cli.utils.fab_hostname_validator import validate_and_get_env_variable

# Initialize API endpoints with validation
API_ENDPOINT_FABRIC = validate_and_get_env_variable(
    "FAB_API_ENDPOINT_FABRIC", "api.fabric.microsoft.com"
)
API_VERSION_FABRIC = "v1"

API_ENDPOINT_ONELAKE = validate_and_get_env_variable(
    "FAB_API_ENDPOINT_ONELAKE", "onelake.dfs.fabric.microsoft.com"
)

API_ENDPOINT_AZURE = validate_and_get_env_variable(
    "FAB_API_ENDPOINT_AZURE", "management.azure.com"
)

API_ENDPOINT_POWER_BI = (
    validate_and_get_env_variable(
        "FAB_API_ENDPOINT_POWER_BI", "api.powerbi.com")
    + "/v1.0/myorg"
)

API_USER_AGENT = "ms-fabric-cli"
API_USER_AGENT_TEST = "ms-fabric-cli-test"
WEB_URI = "https://app.powerbi.com/groups"

# Versioning
FAB_VERSION = __version__

# Scopes
SCOPE_FABRIC_DEFAULT = ["https://analysis.windows.net/powerbi/api/.default"]
SCOPE_ONELAKE_DEFAULT = ["https://storage.azure.com/.default"]
SCOPE_AZURE_DEFAULT = ["https://management.azure.com/.default"]

FABRIC_TOKEN_AUDIENCE = ["https://analysis.windows.net/powerbi/api"]
ONELAKE_TOKEN_AUDIENCE = ["https://storage.azure.com"]
AZURE_TOKEN_AUDIENCE = ["https://management.azure.com"]

# Auth
AUTH_DEFAULT_AUTHORITY = "https://login.microsoftonline.com/common"
AUTH_DEFAULT_CLIENT_ID = "5814bfb4-2705-4994-b8d6-39aabeb5eaeb"
AUTH_TENANT_AUTHORITY = "https://login.microsoftonline.com/"

# Env variables
FAB_TOKEN = "fab_token"
FAB_TOKEN_ONELAKE = "fab_token_onelake"
FAB_TOKEN_AZURE = "fab_token_azure"
FAB_SPN_CLIENT_ID = "fab_spn_client_id"
FAB_SPN_CLIENT_SECRET = "fab_spn_client_secret"
FAB_SPN_CERT_PATH = "fab_spn_cert_path"
FAB_SPN_CERT_PASSWORD = "fab_spn_cert_password"
FAB_SPN_FEDERATED_TOKEN = "fab_spn_federated_token"
FAB_TENANT_ID = "fab_tenant_id"

FAB_REFRESH_TOKEN = "fab_refresh_token"
IDENTITY_TYPE = "identity_type"
FAB_AUTH_MODE = "fab_auth_mode"  # Kept for backward compatibility
FAB_AUTHORITY = "fab_authority"

AUTH_KEYS = {
    FAB_TENANT_ID: [],
    IDENTITY_TYPE: ["user", "service_principal", "managed_identity"],
}

# Other constants
FAB_CAPACITY_NAME_NONE = "none"
FAB_DEFAULT_OPEN_EXPERIENCE_FABRIC = "fabric-developer"
FAB_DEFAULT_OPEN_EXPERIENCE_POWERBI = "power-bi"
FAB_DEFAULT_CAPACITY_ID = "fab_default_capacity_id"
FAB_MODE_INTERACTIVE = "interactive"
FAB_MODE_COMMANDLINE = "command_line"

# CLI settings
FAB_MODE = "mode"
FAB_CACHE_ENABLED = "cache_enabled"
FAB_CONTEXT_PERSISTENCE_ENABLED = "context_persistence_enabled"
FAB_DEBUG_ENABLED = "debug_enabled"
FAB_ENCRYPTION_FALLBACK_ENABLED = "encryption_fallback_enabled"
FAB_SHOW_HIDDEN = "show_hidden"
FAB_LOCAL_DEFINITION_LABELS = "local_definition_labels"
FAB_DEFAULT_OPEN_EXPERIENCE = "default_open_experience"
FAB_DEFAULT_CAPACITY = "default_capacity"
FAB_DEFAULT_AZ_SUBSCRIPTION_ID = "default_az_subscription_id"
FAB_DEFAULT_AZ_RESOURCE_GROUP = "default_az_resource_group"
FAB_DEFAULT_AZ_LOCATION = "default_az_location"
FAB_DEFAULT_AZ_ADMIN = "default_az_admin"
FAB_JOB_CANCEL_ONTIMEOUT = "job_cancel_ontimeout"
FAB_OUTPUT_ITEM_SORT_CRITERIA = "output_item_sort_criteria"
FAB_OUTPUT_FORMAT = "output_format"
FAB_FOLDER_LISTING_ENABLED = "folder_listing_enabled"
FAB_WS_PRIVATE_LINKS_ENABLED = "workspace_private_links_enabled"
FAB_CHECK_UPDATES = "check_cli_version_updates"

# Version check settings
VERSION_CHECK_PYPI_URL = "https://pypi.org/pypi/ms-fabric-cli/json"
VERSION_CHECK_TIMEOUT_SECONDS = 3

FAB_CONFIG_KEYS_TO_VALID_VALUES = {
    FAB_CACHE_ENABLED: ["false", "true"],
    FAB_CONTEXT_PERSISTENCE_ENABLED: ["false", "true"],
    FAB_DEBUG_ENABLED: ["false", "true"],
    FAB_ENCRYPTION_FALLBACK_ENABLED: ["false", "true"],
    FAB_JOB_CANCEL_ONTIMEOUT: ["false", "true"],
    FAB_LOCAL_DEFINITION_LABELS: [],
    FAB_MODE: [FAB_MODE_INTERACTIVE, FAB_MODE_COMMANDLINE],
    FAB_OUTPUT_ITEM_SORT_CRITERIA: ["byname", "bytype"],
    FAB_SHOW_HIDDEN: ["false", "true"],
    FAB_DEFAULT_AZ_SUBSCRIPTION_ID: [],
    FAB_DEFAULT_AZ_RESOURCE_GROUP: [],
    FAB_DEFAULT_AZ_LOCATION: [],
    FAB_DEFAULT_AZ_ADMIN: [],
    FAB_DEFAULT_CAPACITY: [],
    FAB_DEFAULT_OPEN_EXPERIENCE: ["fabric", "powerbi"],
    FAB_OUTPUT_FORMAT: ["text", "json"],
    FAB_FOLDER_LISTING_ENABLED: ["false", "true"],
    FAB_WS_PRIVATE_LINKS_ENABLED: ["false", "true"],
    FAB_CHECK_UPDATES: ["false", "true"],
    # Add more keys and their respective allowed values as needed
}

CONFIG_DEFAULT_VALUES = {
    FAB_MODE: FAB_MODE_COMMANDLINE,
    FAB_CACHE_ENABLED: "true",
    FAB_CONTEXT_PERSISTENCE_ENABLED: "false",
    FAB_JOB_CANCEL_ONTIMEOUT: "true",
    FAB_DEBUG_ENABLED: "false",
    FAB_SHOW_HIDDEN: "false",
    FAB_ENCRYPTION_FALLBACK_ENABLED: "false",
    FAB_DEFAULT_OPEN_EXPERIENCE: "fabric",
    FAB_OUTPUT_ITEM_SORT_CRITERIA: "byname",
    FAB_OUTPUT_FORMAT: "text",
    FAB_FOLDER_LISTING_ENABLED: "false",
    FAB_WS_PRIVATE_LINKS_ENABLED: "false",
    FAB_CHECK_UPDATES: "true",
}

# Command descriptions
COMMAND_AUTH_DESCRIPTION = "Authenticate with Fabric."
COMMAND_AUTH_STATUS_DESCRIPTION = "Display active account and authentication state."
COMMAND_FS_DESCRIPTION = "Workspace, item and file system operations."
COMMAND_JOBS_DESCRIPTION = "Manage and schedule jobs."
COMMAND_TABLES_DESCRIPTION = "Manage Delta tables."
COMMAND_SHORTCUTS_DESCRIPTION = "Manage shorcuts."
COMMAND_ACLS_DESCRIPTION = "Manage access control lists [admin]."
COMMAND_ACLS_LS_DESCRIPTION = (
    "List ACLs for a workspace, item, gateway, connection, or OneLake resource."
)
COMMAND_ACLS_RM_DESCRIPTION = "Remove an ACL from a workspace, gateway, or connection."
COMMAND_ACLS_GET_DESCRIPTION = (
    "Get ACL details for a workspace, item, gateway, connection, or OneLake resource."
)
COMMAND_ACLS_SET_DESCRIPTION = "Set ACLs on a workspace, gateway, or connection."
COMMAND_CONFIG_DESCRIPTION = "Manage CLI configuration."
COMMAND_API_DESCRIPTION = "Make authenticated API requests."
COMMAND_EXTENSIONS_DESCRIPTION = "Manage extensions."
COMMAND_LABELS_DESCRIPTION = "Manage sensitivity labels [admin]."
COMMAND_CAPACITIES_DESCRIPTION = "(tenant) Manage capacities [admin]."
COMMAND_CONNECTIONS_DESCRIPTION = "(tenant) Manage connections."
COMMAND_DOMAINS_DESCRIPTION = "(tenant) Manage domains [admin]."
COMMAND_EXTERNAL_DATA_SHARES_DESCRIPTION = (
    "(tenant) Manage external data shares [admin]."
)
COMMAND_GATEWAYS_DESCRIPTION = "(tenant) Manage gateways."
COMMAND_FOLDERS_DESCRIPTION = "(workspace) Manage folders."
COMMAND_MANAGED_IDENTITIES_DESCRIPTION = "(workspace) Manage managed identities."
COMMAND_MANAGED_PRIVATE_ENDPOINTS_DESCRIPTION = (
    "(workspace) Manage managed private endpoints."
)
COMMAND_SPARK_POOLS_DESCRIPTION = "(workspace) Manage Apache Spark pools."
COMMAND_VARIABLES_DESCRIPTION = "(workspace) Manage variables."
COMMAND_DESCRIBE_DESCRIPTION = "Show commands supported by each Fabric element or path."

# File system command descriptions
COMMAND_FS_MV_DESCRIPTION = "Move an item or file."
COMMAND_FS_CP_DESCRIPTION = "Copy an item or file."
COMMAND_FS_EXISTS_DESCRIPTION = "Check if a workspace, item, or file exists."
COMMAND_FS_PWD_DESCRIPTION = "Print the current working directory."
COMMAND_FS_OPEN_DESCRIPTION = "Open a workspace or item in browser."
COMMAND_FS_EXPORT_DESCRIPTION = "Export an item."
COMMAND_FS_GET_DESCRIPTION = "Get workspace or item properties."
COMMAND_FS_IMPORT_DESCRIPTION = "Import an item to create or update it."
COMMAND_FS_SET_DESCRIPTION = "Set workspace or item properties."
COMMAND_FS_CLEAR_DESCRIPTION = "Clear the terminal screen."
COMMAND_FS_LN_DESCRIPTION = "Create a shortcut."
COMMAND_FS_START_DESCRIPTION = "Start a resource."
COMMAND_FS_STOP_DESCRIPTION = "Stop a resource."
COMMAND_FS_ASSIGN_DESCRIPTION = "Assign a capacity or resource to a workspace."
COMMAND_FS_UNASSIGN_DESCRIPTION = "Unassign a resource from a workspace."
COMMAND_FS_LS_DESCRIPTION = "List workspaces, items, and files."
COMMAND_FS_MKDIR_DESCRIPTION = "Create a workspace, item, or directory."
COMMAND_FS_RM_DESCRIPTION = "Delete a workspace, item, or file."

# Label command descriptions
COMMAND_LABELS_LIST_LOCAL_DESCRIPTION = "List configured sensitivity labels."
COMMAND_LABELS_SET_DESCRIPTION = "Set a sensitivity label on an item."
COMMAND_LABELS_RM_DESCRIPTION = "Remove a sensitivity label from an item."

# Other command descriptions
COMMAND_VERSION_DESCRIPTION = "Show version information."

# Info
INFO_EXISTS_TRUE = "true"
INFO_EXISTS_FALSE = "false"
INFO_FEATURE_NOT_SUPPORTED = "Feature is not supported"

# Warnings
WARNING_INVALID_WORKSPACE_NAME = "Invalid workspace name"
WARNING_INVALID_ITEM_NAME = "Invalid item name"
WARNING_NOT_SUPPORTED_ITEM = "Not supported in this item type"
WARNING_DIFFERENT_ITEM_TYPES = "Different item types, review"
WARNING_INVALID_PATHS = (
    "Source and destination must be of the same type. Check your paths"
)
WARNING_NOT_SUPPORTED_PATHS = "mv is not supported for the specified source and destination items types. Check your paths"
WARNING_INVALID_SPECIAL_CHARACTERS = (
    "Special caracters not supported for this item type"
)
WARNING_INVALID_LS_ONELAKE = "No more subdirectories supported for this item"
WARNING_INVALID_JSON_FORMAT = "Invalid JSON format"
WARNING_MKDIR_INVALID_ONELAKE = "Invalid paths. Only supported within /Files"
WARNING_OPERATION_NO_RESULT = "Long Running Operation returned no result"
WARNING_FABRIC_ADMINISTRATOR = "Requires Fabric administrator"
WARNING_ONELAKE_RBAC_ENABLED = "Requires data access roles enabled"
WARNING_NON_FABRIC_CAPACITY = "Not a Fabric capacity"
WARNING_ONLY_SUPPORTED_WITHIN_LAKEHOUSE = "Only supported within Lakehouse"
WARNING_ONLY_SUPPORTED_WITHIN_FILES_AND_TABLES = (
    "Only supported within Files/ and Tables/"
)
WARNING_MOVING_ITEMS_INSIDE_WORKSPACE_NOT_SUPPORTED = (
    "Moving items between folders in the same workspace is not yet supported"
)
WARNING_WORKSPACE_EMPTY = "Workspace is empty"
WARNING_ITEM_EXISTS_IN_PATH = "An item with the same name exists in {0}"

# Error codes

ERROR_ALREADY_EXISTS = "AlreadyExists"
ERROR_ALREADY_RUNNING = "AlreadyRunning"
ERROR_AUTHENTICATION_FAILED = "AuthenticationFailed"
ERROR_BAD_REQUEST = "BadRequest"
ERROR_CONFLICT = "Conflict"
ERROR_CONTEXT_LOAD_FAILED = "ContextLoadFailed"
ERROR_DUPLICATE_GATEWAY_NAME = "DuplicateGatewayName"
ERROR_ENCRYPTION_FAILED = "EncryptionFailed"
ERROR_FORBIDDEN = "Forbidden"
ERROR_INVALID_ACCESS_MODE = "InvalidAccessMode"
ERROR_INVALID_CERTIFICATE = "InvalidCertificate"
ERROR_INVALID_CERTIFICATE_PATH = "InvalidCertificatePath"
ERROR_INVALID_DEFINITION_PAYLOAD = "InvalidDefinitionPayload"
ERROR_INVALID_HOSTNAME = "InvalidHostname"
ERROR_INVALID_ELEMENT_TYPE = "InvalidElementType"
ERROR_INVALID_ENTRIES_FORMAT = "InvalidEntriesFormat"
ERROR_INVALID_FORMAT = "InvalidFormat"
ERROR_INVALID_GUID = "InvalidGuid"
ERROR_INVALID_INPUT = "InvalidInput"
ERROR_INVALID_ITEM_TYPE = "InvalidItemType"
ERROR_INVALID_JSON = "InvalidJson"
ERROR_INVALID_OPERATION = "InvalidOperation"
ERROR_INVALID_PATH = "InvalidPath"
ERROR_INVALID_PROPERTY = "InvalidProperty"
ERROR_INVALID_DETLA_TABLE = "InvalidDeltaTable"
ERROR_INVALID_QUERY_FIELDS = "InvalidQueryFields"
ERROR_INVALID_WORKSPACE_TYPE = "InvalidWorkspaceType"
ERROR_INVALID_QUERY = "InvalidQuery"
ERROR_INTERNAL_SERVER_ERROR = "InternalServerError"
ERROR_UNSUPPORTED_ITEM_TYPE = "UnsupportedItemType"
ERROR_UNSUPPORTED_COMMAND = "UnsupportedCommand"
ERROR_UNEXPECTED_ERROR = "UnexpectedError"
ERROR_ITEM_DISPLAY_NAME_ALREADY_IN_USE = "ItemDisplayNameAlreadyInUse"
ERROR_MAX_RETRIES_EXCEEDED = "MaxRetriesExceeded"
ERROR_NOT_FOUND = "NotFound"
ERROR_NOT_RUNNABLE = "NotRunnable"
ERROR_NOT_RUNNING = "NotRunning"
ERROR_NOT_SUPPORTED = "NotSupported"
ERROR_OPERATION_CANCELLED = "LongRunningOperationCancelled"
ERROR_OPERATION_FAILED = "LongRunningOperationFailed"
ERROR_UNAUTHORIZED = "Unauthorized"
ERROR_UNIVERSAL_SECURITY_DISABLED = "UniversalSecurityDisabled"
ERROR_SPN_AUTH_MISSING = "ServicePrincipalAuthMissing"
ERROR_JOB_FAILED = "JobFailed"

# Exit codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_CANCELLED_OR_MISUSE_BUILTINS = 2
EXIT_CODE_AUTHORIZATION_REQUIRED = 4

# Contextual commands
OS_COMMANDS = {
    "rm": {"windows": "del", "unix": "rm"},
    "ls": {"windows": "dir", "unix": "ls"},
    "mv": {"windows": "move", "unix": "mv"},
    "cp": {"windows": "copy", "unix": "cp"},
    "ln": {
        "windows": "mklink",
        "unix": "ln",
    },
    "clear": {
        "windows": "cls",
        "unix": "clear",
    },
}

# DEBUG
DEBUG = False

# Interactive CLI messages
INTERACTIVE_EXIT_MESSAGE = "Exiting interactive mode. Goodbye!"

# Interactive command constants
INTERACTIVE_QUIT_COMMANDS = ["quit", "q", "exit"]
INTERACTIVE_HELP_COMMANDS = ["help", "h", "-h", "--help"]
INTERACTIVE_VERSION_COMMANDS = ["version", "v", "-v", "--version"]

# Platform metadata
ITEM_METADATA_PROPERTIES = {
    "id",
    "type",
    "displayName",
    "description",
    "workspaceId",
    "folderId",
    "properties",
}

# Item set constants
ITEM_QUERY_DEFINITION = "definition"
ITEM_QUERY_PROPERTIES = "properties"
ITEM_QUERY_DISPLAY_NAME = "displayName"
ITEM_QUERY_DESCRIPTION = "description"

# Allowed metadata keys for item set operations
ITEM_SET_ALLOWED_METADATA_KEYS = [
    ITEM_QUERY_DISPLAY_NAME,
    ITEM_QUERY_DESCRIPTION,
    ITEM_QUERY_PROPERTIES,
]

# Invalid query parameters for set command across all fabric resources
SET_COMMAND_INVALID_QUERIES = ["id", "type", "workspaceId", "folderId"]
