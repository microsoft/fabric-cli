# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from enum import Enum, auto
from typing import List

import fabric_cli.core.fab_constant as fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages

####################################################################################################
# Fabric Element Types and Sub-Types                                                               #
####################################################################################################


# The FabricElement class is the base class for all elements in the fabric hierarchy.
class FabricElementType(Enum):
    TENANT = auto()
    WORKSPACE = auto()
    VIRTUAL_WORKSPACE = auto()
    VIRTUAL_ITEM_CONTAINER = auto()
    ITEM = auto()
    VIRTUAL_ITEM = auto()
    VIRTUAL_WORKSPACE_ITEM = auto()
    ONELAKE = auto()
    LOCAL_PATH = auto()
    FOLDER = auto()

    def __str__(self):
        """Return the camel case name of the enum, removing the underscores.
        Example:
            FabricElementType.VIRTUAL_WORKSPACE_ITEM -> "VirtualWorkspaceItem"
        """
        return self.name.title().replace("_", "")

    @classmethod
    def from_string(cls, elem_type_str):
        """Case-insensitive match for enum values."""
        for elem in cls:
            if str(elem).lower() == elem_type_str.lower():
                return elem
        match elem_type_str.lower():
            case "folder":
                return FabricElementType.FOLDER
            case "personal":
                return FabricElementType.WORKSPACE
            case x if x.startswith("."):
                try:
                    VirtualWorkspaceType.from_string(x)
                    return FabricElementType.VIRTUAL_WORKSPACE
                except Exception:
                    pass
                try:
                    VirtualItemContainerType.from_string(x)
                    return FabricElementType.VIRTUAL_ITEM_CONTAINER
                except Exception:
                    pass
                raise FabricCLIError(
                    ErrorMessages.Common.invalid_element_type(elem_type_str),
                    fab_constant.ERROR_INVALID_ELEMENT_TYPE,
                )
            case _:
                # Try to convert it to each item and return ItemType if successful
                try:
                    ItemType.from_string(elem_type_str)
                    return FabricElementType.ITEM
                except Exception:
                    pass
                try:
                    VirtualItemType.from_string(elem_type_str)
                    return FabricElementType.VIRTUAL_ITEM
                except Exception:
                    pass
                try:
                    VirtualWorkspaceItemType.from_string(elem_type_str)
                    return FabricElementType.VIRTUAL_WORKSPACE_ITEM
                except Exception:
                    pass
                raise FabricCLIError(
                    ErrorMessages.Common.invalid_element_type(elem_type_str),
                    fab_constant.ERROR_INVALID_ELEMENT_TYPE,
                )


########################
# Fabric Workspaces    #
########################


class WorkspaceType(Enum):
    WORKSPACE = "Workspace"
    PERSONAL = "Personal"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, ws_type_str):
        """Case-insensitive match for enum values."""
        for item in cls:
            if item.value.lower() == ws_type_str.lower():
                return item
        raise FabricCLIError(
            ErrorMessages.Common.invalid_workspace_type(ws_type_str),
            fab_constant.ERROR_INVALID_WORKSPACE_TYPE,
        )


#############################
# Fabric Virtual Workspaces #
#############################


class VirtualWorkspaceType(Enum):
    CAPACITY = ".capacities"
    CONNECTION = ".connections"
    GATEWAY = ".gateways"
    DOMAIN = ".domains"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, vws_type_str):
        """Case-insensitive match for enum values."""
        for item in cls:
            if item.value.lower() == vws_type_str.lower():
                return item
        raise FabricCLIError(
            ErrorMessages.Common.invalid_virtual_workspace_type(vws_type_str),
            fab_constant.ERROR_INVALID_WORKSPACE_TYPE,
        )


##################################
# Fabric Basic Item              #
##################################


class _BaseItemType(Enum):
    @classmethod
    def from_string(cls, item_type_str):
        raise NotImplementedError("This method must be implemented in the subclass")


##################################
# Fabric Virtual Workspace Items #
##################################


# The VirtualWorkspaceItem class is the base class for all elements in the fabric hierarchy.
class VirtualWorkspaceItemType(_BaseItemType):
    CAPACITY = auto()
    CONNECTION = auto()
    GATEWAY = auto()
    DOMAIN = auto()

    def __str__(self):
        return self.name.title().replace("_", "")

    @classmethod
    def from_string(cls, item_type_str):
        """Case-insensitive match for enum values."""
        for item in cls:
            if str(item).lower() == item_type_str.lower():
                return item
        raise FabricCLIError(
            ErrorMessages.Common.invalid_item_type(item_type_str),
            fab_constant.ERROR_INVALID_ITEM_TYPE,
        )


# VirutaWorkspace to VirtualWorkspaceItem mapping
VWIMap: dict[VirtualWorkspaceType, VirtualWorkspaceItemType] = {
    VirtualWorkspaceType.CAPACITY: VirtualWorkspaceItemType.CAPACITY,
    VirtualWorkspaceType.CONNECTION: VirtualWorkspaceItemType.CONNECTION,
    VirtualWorkspaceType.GATEWAY: VirtualWorkspaceItemType.GATEWAY,
    VirtualWorkspaceType.DOMAIN: VirtualWorkspaceItemType.DOMAIN,
}

##################################
# Fabric Virtual Item Containers #
##################################


class VirtualItemContainerType(Enum):
    SPARK_POOL = ".sparkpools"
    MANAGED_IDENTITY = ".managedidentities"
    MANAGED_PRIVATE_ENDPOINT = ".managedprivateendpoints"
    EXTERNAL_DATA_SHARE = ".externaldatashares"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, vws_type_str):
        """Case-insensitive match for enum values."""
        for item in cls:
            if item.value.lower() == vws_type_str.lower():
                return item
        raise FabricCLIError(
            ErrorMessages.Common.invalid_virtual_item_container_type(vws_type_str),
            fab_constant.ERROR_INVALID_ITEM_TYPE,
        )


########################
# Fabric Virtual Items #
########################


class VirtualItemType(_BaseItemType):
    SPARK_POOL = auto()
    MANAGED_IDENTITY = auto()
    MANAGED_PRIVATE_ENDPOINT = auto()
    EXTERNAL_DATA_SHARE = auto()

    def __str__(self):
        return self.name.title().replace("_", "")

    @classmethod
    def from_string(cls, item_type_str):
        """Case-insensitive match for enum values."""
        for item in cls:
            if str(item).lower() == item_type_str.lower():
                return item
        raise FabricCLIError(
            ErrorMessages.Common.invalid_item_type(item_type_str),
            fab_constant.ERROR_INVALID_ITEM_TYPE,
        )


# VirtualItemContainer to VirtualItem mapping
VICMap: dict[VirtualItemContainerType, VirtualItemType] = {
    VirtualItemContainerType.SPARK_POOL: VirtualItemType.SPARK_POOL,
    VirtualItemContainerType.MANAGED_IDENTITY: VirtualItemType.MANAGED_IDENTITY,
    VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT: VirtualItemType.MANAGED_PRIVATE_ENDPOINT,
    VirtualItemContainerType.EXTERNAL_DATA_SHARE: VirtualItemType.EXTERNAL_DATA_SHARE
}

################
# Fabric Items #
################


class ItemType(_BaseItemType):
    # Portal only, not documented in the API
    AISKILL = "AISkill"
    APACHE_AIRFLOW_JOB = "ApacheAirflowJob"
    EXPLORATION = "Exploration"
    RETAIL_DATA_MANAGER = "RetailDataManager"
    HEALTHCARE_DATA_SOLUTION = "Healthcaredatasolution"
    METRIC_SET = "MetricSet"
    ORG_APP = "OrgApp"
    SUSTAINABILITY_DATA_SOLUTION = "SustainabilityDataSolution"
    USER_DATA_FUNCTION = "UserDataFunction"
    VARIABLE_LIBRARY = "VariableLibrary"

    # API
    DASHBOARD = "Dashboard"
    DATAMART = "Datamart"
    DATA_PIPELINE = "DataPipeline"
    ENVIRONMENT = "Environment"
    EVENTHOUSE = "Eventhouse"
    EVENTSTREAM = "Eventstream"
    KQL_DASHBOARD = "KQLDashboard"
    KQL_DATABASE = "KQLDatabase"
    KQL_QUERYSET = "KQLQueryset"
    LAKEHOUSE = "Lakehouse"
    MIRRORED_WAREHOUSE = "MirroredWarehouse"
    MIRRORED_DATABASE = "MirroredDatabase"
    ML_EXPERIMENT = "MLExperiment"
    ML_MODEL = "MLModel"
    NOTEBOOK = "Notebook"
    PAGINATED_REPORT = "PaginatedReport"
    REFLEX = "Reflex"
    REPORT = "Report"
    SEMANTIC_MODEL = "SemanticModel"
    SPARK_JOB_DEFINITION = "SparkJobDefinition"
    SQL_ENDPOINT = "SQLEndpoint"
    WAREHOUSE = "Warehouse"
    COPYJOB = "CopyJob"
    GRAPHQLAPI = "GraphQLApi"
    MOUNTED_DATA_FACTORY = "MountedDataFactory"
    SQL_DATABASE = "SQLDatabase"
    DATAFLOW = "Dataflow"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, item_type_str):
        """Case-insensitive match for enum values."""
        for item in cls:
            if item.value.lower() == item_type_str.lower():
                return item
        raise FabricCLIError(
            ErrorMessages.Common.invalid_item_type(item_type_str),
            fab_constant.ERROR_INVALID_ITEM_TYPE,
        )


#################
# One Lake Item #
#################


class OneLakeItemType(Enum):
    FOLDER = auto()
    FILE = auto()
    TABLE = auto()
    SHORTCUT = auto()
    UNDEFINED = auto()


####################
# Fabric Job Types #
####################


class FabricJobType(Enum):
    SPARK_JOB = "sparkjob"
    RUN_NOTEBOOK = "RunNotebook"
    PIPELINE = "Pipeline"
    TABLE_MAINTENANCE = "TableMaintenance"


ITJobMap: dict[ItemType, FabricJobType] = {
    # {"commandLineArguments": "--param1 TEST --param2 1234"}
    ItemType.SPARK_JOB_DEFINITION: FabricJobType.SPARK_JOB,
    # { "parameters": {"param1": {"value": "FullPipeline", "type": "string"}, "param2": { "value": 2, "type": "int" } }}
    ItemType.NOTEBOOK: FabricJobType.RUN_NOTEBOOK,
    # {"parameters": { "param1": "FullPipeline", "param2": 2 }}
    ItemType.DATA_PIPELINE: FabricJobType.PIPELINE,
    # {"tableName": "orders", "optimizeSettings": {"vOrder": true, "zOrderBy": ["account_id"]}, "vacuumSettings": {"retentionPeriod": "7.01:00:00"}}
    ItemType.LAKEHOUSE: FabricJobType.TABLE_MAINTENANCE,
}

###################################
# Fabric Mutable Properties Types #
###################################
ITMutablePropMap: dict[ItemType, List[dict[str, str]]] = {
    ItemType.NOTEBOOK: [
        {
            "environment": "definition.parts[0].payload.metadata.dependencies.environment"
        },
        {"lakehouse": "definition.parts[0].payload.metadata.dependencies.lakehouse"},
        {"warehouse": "definition.parts[0].payload.metadata.dependencies.warehouse"},
    ],
    ItemType.REPORT: [
        {
            "semanticModelId": "definition.parts[0].payload.datasetReference.byConnection.pbiModelDatabaseName"
        },
    ],
    ItemType.SPARK_JOB_DEFINITION: [
        {
            "payload": "definition.parts[0].payload",
        },
        {
            "definition.parts[0].payload.defaultLakehouseArtifactId": "definition.parts[0].payload.defaultLakehouseArtifactId",
        },
        {
            "definition.parts[0].payload.executableFile": "definition.parts[0].payload.executableFile",
        },
    ],
}

#################
# Item Folders  #
#################


class LakehouseFolders(Enum):
    FILES = "Files"
    TABLES = "Tables"
    TABLE_MAINTENANCE = "TableMaintenance"


class WarehouseFolders(Enum):
    FILES = "Files"
    TABLES = "Tables"


class SemanticModelFolders(Enum):
    TABLES = "Tables"


class SparkJobDefinitionFolders(Enum):
    LIBS = "Libs"
    MAIN = "Main"
    SNAPSHOTS = "Snapshots"


class KQLDatabaseFolders(Enum):
    TABLES = "Tables"
    SHORTCUT = "Shortcut"


class SQLDatabaseFolders(Enum):
    TABLES = "Tables"
    FILES = "Files"
    CODE = "Code"


# TODO validate MirroredWarehouse OneLake folders
class MirroredDatabaseFolders(Enum):
    FILES = "Files"
    TABLES = "Tables"


ItemFoldersMap: dict[ItemType, List[str]] = {
    ItemType.LAKEHOUSE: [folder.value for folder in LakehouseFolders],
    ItemType.WAREHOUSE: [folder.value for folder in WarehouseFolders],
    ItemType.SEMANTIC_MODEL: [folder.value for folder in SemanticModelFolders],
    ItemType.SPARK_JOB_DEFINITION: [
        folder.value for folder in SparkJobDefinitionFolders
    ],
    ItemType.KQL_DATABASE: [folder.value for folder in KQLDatabaseFolders],
    ItemType.MIRRORED_DATABASE: [folder.value for folder in MirroredDatabaseFolders],
    ItemType.MIRRORED_WAREHOUSE: [folder.value for folder in MirroredDatabaseFolders],
    ItemType.SQL_DATABASE: [folder.value for folder in SQLDatabaseFolders],
}

OnelakeWritableFolders = ["Files", "Libs", "Main"]

ItemOnelakeWritableFoldersMap: dict[ItemType, List[str]] = {
    ItemType.LAKEHOUSE: [
        folder.value
        for folder in LakehouseFolders
        if folder.value in OnelakeWritableFolders
    ],
    ItemType.WAREHOUSE: [
        folder.value
        for folder in WarehouseFolders
        if folder.value in OnelakeWritableFolders
    ],
    ItemType.SEMANTIC_MODEL: [
        folder.value
        for folder in SemanticModelFolders
        if folder.value in OnelakeWritableFolders
    ],
    ItemType.SPARK_JOB_DEFINITION: [
        folder.value
        for folder in SparkJobDefinitionFolders
        if folder.value in OnelakeWritableFolders
    ],
    ItemType.KQL_DATABASE: [
        folder.value
        for folder in KQLDatabaseFolders
        if folder.value in OnelakeWritableFolders
    ],
    ItemType.SQL_DATABASE: [
        folder.value
        for folder in SQLDatabaseFolders
        if folder.value in OnelakeWritableFolders
    ],
    ItemType.MIRRORED_DATABASE: [
        folder.value
        for folder in MirroredDatabaseFolders
        if folder.value in OnelakeWritableFolders
    ],
    ItemType.MIRRORED_WAREHOUSE: [
        folder.value
        for folder in MirroredDatabaseFolders
        if folder.value in OnelakeWritableFolders
    ],
}

####################################################################################################
# Fabric Item Format Mapping                                                                           #
####################################################################################################

# Item URI in the Fabric API

format_mapping = {
    # Portal only
    ItemType.AISKILL: "aiskills",
    ItemType.APACHE_AIRFLOW_JOB: "apacheairflowprojects",
    ItemType.EXPLORATION: "explorations",
    ItemType.RETAIL_DATA_MANAGER: "retaildatamanagers",
    ItemType.HEALTHCARE_DATA_SOLUTION: "healthcaredatasolutions",
    ItemType.SUSTAINABILITY_DATA_SOLUTION: "sustainabilitydatasolutions",
    ItemType.METRIC_SET: "metricsets",
    ItemType.ORG_APP: "orgapps",
    ItemType.USER_DATA_FUNCTION: "userdatafunctions",
    ItemType.VARIABLE_LIBRARY: "variablelibraries",
    # API
    ItemType.DASHBOARD: "dashboards",
    ItemType.DATA_PIPELINE: "dataPipelines",
    ItemType.DATAMART: "datamarts",
    ItemType.ENVIRONMENT: "environments",
    ItemType.EVENTHOUSE: "eventhouses",
    ItemType.EVENTSTREAM: "eventstreams",
    ItemType.KQL_DASHBOARD: "kqlDashboards",
    ItemType.KQL_DATABASE: "kqlDatabases",
    ItemType.KQL_QUERYSET: "kqlQuerysets",
    ItemType.LAKEHOUSE: "lakehouses",
    ItemType.ML_EXPERIMENT: "mlExperiments",
    ItemType.ML_MODEL: "mlModels",
    ItemType.MIRRORED_WAREHOUSE: "mirroredWarehouses",
    ItemType.MIRRORED_DATABASE: "mirroredDatabases",
    ItemType.NOTEBOOK: "notebooks",
    ItemType.PAGINATED_REPORT: "paginatedReports",
    ItemType.REFLEX: "reflexes",
    ItemType.REPORT: "reports",
    ItemType.SQL_DATABASE: "sqlDatabases",
    ItemType.SQL_ENDPOINT: "sqlEndpoints",
    ItemType.SEMANTIC_MODEL: "semanticModels",
    ItemType.SPARK_JOB_DEFINITION: "sparkJobDefinitions",
    ItemType.WAREHOUSE: "warehouses",
    ItemType.COPYJOB: "copyJobs",
    ItemType.GRAPHQLAPI: "graphqlapis",
    ItemType.MOUNTED_DATA_FACTORY: "mounteddatafactories",
    ItemType.DATAFLOW: "dataflows",
}

# Item URI in the Fabric Portal

uri_mapping = {
    # Portal only
    ItemType.AISKILL: "aiskills",
    ItemType.APACHE_AIRFLOW_JOB: "apacheairflowprojects",
    ItemType.EXPLORATION: "explorations",
    ItemType.RETAIL_DATA_MANAGER: "retail-data-manager",
    ItemType.HEALTHCARE_DATA_SOLUTION: "health-data-manager",
    ItemType.SUSTAINABILITY_DATA_SOLUTION: "sustainability-data-manager",
    ItemType.METRIC_SET: "metricsets",
    ItemType.ORG_APP: "orgapps",
    ItemType.USER_DATA_FUNCTION: "userdatafunctions",
    ItemType.VARIABLE_LIBRARY: "variable-libraries",
    # API
    ItemType.DASHBOARD: "dashboards",
    ItemType.DATAMART: "datamarts",
    ItemType.DATA_PIPELINE: "pipelines",
    ItemType.ENVIRONMENT: "sparkenvironments",
    ItemType.EVENTHOUSE: "eventhouses",
    ItemType.EVENTSTREAM: "eventstreams",
    ItemType.KQL_DASHBOARD: "kustodashboards",
    ItemType.KQL_DATABASE: "databases",
    ItemType.KQL_QUERYSET: "queryworkbenches",
    ItemType.LAKEHOUSE: "lakehouses",
    ItemType.MIRRORED_DATABASE: "mirroreddatabases",
    ItemType.ML_EXPERIMENT: "mlexperiments",
    ItemType.ML_MODEL: "mlmodels",
    ItemType.NOTEBOOK: "synapsenotebooks",
    ItemType.PAGINATED_REPORT: "rdlreports",
    ItemType.REFLEX: "reflexes",
    ItemType.REPORT: "reports",
    ItemType.SEMANTIC_MODEL: "datasets",
    ItemType.SPARK_JOB_DEFINITION: "sparkjobdefinitions",
    ItemType.SQL_DATABASE: "sqldatabases",
    ItemType.SQL_ENDPOINT: "lakewarehouses",
    ItemType.WAREHOUSE: "datawarehouses",
    ItemType.COPYJOB: "copyjobs",
    ItemType.GRAPHQLAPI: "graphql",
    ItemType.MOUNTED_DATA_FACTORY: "mounteddatafactories",
    ItemType.DATAFLOW: "dataflows-gen2",
}

# Item Payload definition

definition_format_mapping = {
    ItemType.SPARK_JOB_DEFINITION: {"default": "?format=SparkJobDefinitionV1"},
    ItemType.NOTEBOOK: {
        "default": "?format=ipynb",
        ".py": "?format=fabricGitSource",
        ".ipynb": "?format=ipynb",
    },
}
