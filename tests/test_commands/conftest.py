# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import os
import re
from unittest.mock import patch

import pytest
import requests
import vcr  # type: ignore

import fabric_cli.commands.fs.fab_fs_import as fab_fs_import
import fabric_cli.commands.fs.fab_fs_mkdir as fab_fs_mkdir
import fabric_cli.commands.fs.fab_fs_rm as fab_fs_rm
import fabric_cli.core.fab_state_config as state_config
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    ItemType,
    VICMap,
    VirtualItemContainerType,
    VirtualWorkspaceType,
    VWIMap,
)
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.data.models import EntityMetadata
from tests.test_commands.data.static_test_data import (
    StaticTestData,
    get_mock_data,
    get_static_data,
)
from tests.test_commands.processors import (
    generate_random_string,
    process_request,
    process_response,
    update_generated_name_with_special_character,
)
from tests.test_commands.utils import cli_path_join, set_vcr_mode_env

custom_parametrize = pytest.mark.parametrize("item_type", [
    ItemType.DATA_PIPELINE,
    ItemType.ENVIRONMENT, ItemType.EVENTHOUSE, ItemType.EVENTSTREAM,
    ItemType.KQL_DASHBOARD, ItemType.KQL_QUERYSET,
    ItemType.LAKEHOUSE, ItemType.ML_EXPERIMENT, ItemType.ML_MODEL,
    ItemType.MIRRORED_DATABASE, ItemType.NOTEBOOK,
    ItemType.REFLEX, ItemType.REPORT,
    ItemType.SQL_DATABASE, ItemType.SEMANTIC_MODEL,
    ItemType.SPARK_JOB_DEFINITION, ItemType.WAREHOUSE, ItemType.COPYJOB,
    ItemType.GRAPHQLAPI, ItemType.DATAFLOW,
])

basic_item_parametrize = pytest.mark.parametrize("item_type", [
    ItemType.DATA_PIPELINE, ItemType.ENVIRONMENT, ItemType.EVENTSTREAM,
    ItemType.KQL_DASHBOARD, ItemType.KQL_QUERYSET, ItemType.ML_EXPERIMENT,
    ItemType.ML_MODEL, ItemType.MIRRORED_DATABASE, ItemType.NOTEBOOK,
    ItemType.REFLEX, ItemType.SPARK_JOB_DEFINITION,
])

FILTER_HEADERS = [
    "authorization",
    "client-request-id",
    "retry-after",
    "x-ms-client-request-id",
    "x-ms-correlation-request-id",
    "x-ms-ratelimit-remaining-subscription-reads",
    "x-ms-request-id",
    "x-ms-routing-request-id",
    "x-ms-gateway-service-instanceid",
    "x-ms-ratelimit-remaining-tenant-reads",
    "x-ms-served-by",
    "x-ms-authorization-auxiliary",
]


def pytest_addoption(parser):
    parser.addoption(
        "--record",
        action="store_true",
        default=False,
        help="Run tests in live mode (recording of cassettes).",
    )


@pytest.fixture(scope="session")
def cli_executor() -> CLIExecutor:
    return CLIExecutor()


@pytest.fixture(scope="session")
def vcr_mode(request):
    return "all" if request.config.getoption("--record") else "none"


@pytest.fixture(scope="class")
def vcr_instance(vcr_mode, request):
    """
    A pytest fixture to create a VCR instance.
    Automatically places cassettes in a directory named after the parent folder of the test file.
    """
    # Determine the test file's parent folder name
    test_file = request.fspath
    parent_folder = os.path.basename(os.path.dirname(test_file))

    # Construct the cassette library directory path
    test_file_name = os.path.splitext(os.path.basename(test_file))[0]
    cassette_library_dir = os.path.join(
        os.path.dirname(__file__), "recordings", parent_folder, test_file_name
    )

    # Ensure the directory exists
    os.makedirs(cassette_library_dir, exist_ok=True)

    # Create and return the VCR instance
    vcr_instance = vcr.VCR(
        cassette_library_dir=cassette_library_dir,
        record_mode=vcr_mode,
        filter_headers=FILTER_HEADERS,
        before_record_request=process_request,
        before_record_response=process_response,
        path_transformer=vcr.VCR.ensure_suffix(".yaml"),
        match_on=["method", "uri", "json_body"],
        ignore_hosts=["login.microsoftonline.com", "pypi.org"],
    )

    set_vcr_mode_env(vcr_mode)

    vcr_instance.register_matcher("json_body", _json_body_matcher)

    return vcr_instance


@pytest.fixture(autouse=True)
def vcr_cassette(vcr_instance, cassette_name):
    cassette_name = f"{cassette_name}.yaml"
    delete_cassette_if_record_mode_all(vcr_instance, cassette_name)

    with vcr_instance.use_cassette(cassette_name):
        yield


@pytest.fixture()
def cassette_name(request):
    """Fixture to provide the current test's cassette name."""
    cassette_name = request.node.name
    return cassette_name


def _json_body_matcher(r1, r2):
    assert r1.method == r2.method and r1.uri == r2.uri

    body1 = r1.body or b""
    body2 = r2.body or b""

    content_type = r1.headers.get("Content-Type")

    if "multipart/form-data" in content_type:
        # Compare if the filenames are the same
        filename1 = body1.split(b"filename=")[1].split(b"\r\n")[0]
        filename2 = body2.split(b"filename=")[1].split(b"\r\n")[0]
        assert filename1 == filename2
        return

    if "application/octet-stream" in content_type:
        # For octet-stream, we compare the raw bytes directly
        assert body1 == body2, "Raw body mismatch!\nGot: {body1}\nExpected: {body2}"
        return

    try:
        b1 = json.loads(body1.decode("utf-8")) if body1 else {}
        b2 = json.loads(body2.decode("utf-8")) if body2 else {}
    except json.JSONDecodeError:
        assert body1 == body2, "Raw body mismatch!\nGot: {b1}\nExpected: {b2}"
        return

    # Sorting the “parts” list ensures both requests have their parts
    # in the same order before comparing. JSON treats list order as
    # significant, so normalizing the parts prevents false mismatches
    # when the items are the same but appear in different orders.
    b1_definition = b1.get("definition", {})
    b2_definition = b2.get("definition", {})
    if isinstance(b1_definition, dict) and isinstance(b2_definition, dict):
        for definition_obj in (b1_definition, b2_definition):
            if definition_obj.get("parts") and isinstance(
                definition_obj["parts"], list
            ):
                definition_obj["parts"].sort(key=lambda x: x.get("path", ""))

    assert b1 == b2, f"JSON body mismatch!\nGot: {b1}\nExpected: {b2}"


@pytest.fixture(autouse=True)
def set_test_user_agent(monkeypatch):
    original_request = requests.Session.request

    def patched_request(self, method, url, *args, **kwargs):
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = (
            f"{fab_constant.API_USER_AGENT_TEST}/{fab_constant.FAB_VERSION}"
        )
        kwargs["headers"] = headers

        # Call the original request method with updated headers
        return original_request(self, method, url, *args, **kwargs)

    # Monkeypatch the Session.request method
    monkeypatch.setattr(requests.Session, "request", patched_request)


@pytest.fixture(scope="session")
def test_data(vcr_mode) -> StaticTestData:
    """
    Fixture to get the StaticTestsData according to current test running mode.
    Running in playback mode will return StaticTestData with predefined mock data,
    while running in recording mode will return StaticTestData with preconfigured values for live mode.
    """
    return get_mock_data() if vcr_mode == "none" else get_static_data()


@pytest.fixture()
def assert_fabric_cli_error(mock_fab_ui_print_error):
    """
    Fixture to assert that a FabricCLIError is raised with the expected error code and message.
    Automatically includes mock_fab_ui_print_error.
    """

    def _assert_fabric_cli_error(expected_error_code: str, expected_message=None):
        """
        Assert that a FabricCLIError was raised with the expected error code and message.

        Args:
            expected_error_code (str): The expected error code
            expected_message (str, optional): The expected error message. Can be exact match or regex pattern.
        """
        mock_fab_ui_print_error.assert_called()
        error_call = mock_fab_ui_print_error.mock_calls[0]
        assert isinstance(error_call.args[0], FabricCLIError)
        assert error_call.args[0].status_code == expected_error_code
        assert (
            error_call.args[0].message != None
        ), "expected error message to not be None"
        if expected_message is not None:
            assert expected_message in error_call.args[0].message

    return _assert_fabric_cli_error


#################### Setup and Teardown Fixtures ####################


@pytest.fixture(scope="class")
def workspace(vcr_instance, test_data):
    state_config.set_config(fab_constant.FAB_CACHE_ENABLED, "false")
    cassette_name = "class_setup.yaml"
    delete_cassette_if_record_mode_all(vcr_instance, cassette_name)

    with vcr_instance.use_cassette(cassette_name):
        display_name = generate_random_string(
            vcr_instance,
            cassette_name,
            prefix="fabriccli_WorkspacePerTestclass_",
            type="workspace",
        )
        workspace_name = f"{display_name}.Workspace"
        workspace_path = f"/{workspace_name}"

        mkdir(workspace_path, params=[
              f"capacityName={test_data.capacity.name}"])
        yield EntityMetadata(display_name, workspace_name, workspace_path)
        rm(workspace_path)


@pytest.fixture
def item_factory(vcr_instance, cassette_name, workspace):
    # Keep track of all items created during this test
    created_items = []

    def _create_item(
        type: ItemType,
        path=workspace.full_path,
        content_path=None,
        should_clean=True,
        custom_name=None,
    ):
        """
        Actually creates the item resource and returns an EntityMetadata object.
        """
        # Use custom name if provided, otherwise generate random name
        if custom_name:
            generated_name = custom_name
        else:
            # Use the test's specific recording file
            generated_name = generate_random_string(
                vcr_instance, cassette_name)

        item_name = f"{generated_name}.{type}"
        item_path = cli_path_join(path, item_name)

        if content_path:
            import_cmd(item_path, content_path)
        else:
            mkdir(item_path)

        # Build the metadata for the created resource
        metadata = EntityMetadata(generated_name, item_name, item_path)
        if should_clean:
            created_items.append(metadata)
        return metadata

    yield _create_item

    # Remove all items in inverse order of creation to avoid dependencies
    for metadata in reversed(created_items):
        rm(metadata.full_path)


@pytest.fixture
def folder_factory(vcr_instance, cassette_name, workspace):
    # Keep track of all folders created during this test
    current_config = state_config.get_config(
        fab_constant.FAB_FOLDER_LISTING_ENABLED)
    state_config.set_config(fab_constant.FAB_FOLDER_LISTING_ENABLED, "true")
    created_folders = []

    def _create_folder(
        path=workspace.full_path,
        should_clean=True,
    ) -> EntityMetadata:
        """
        Actually creates the folder resource and returns an EntityMetadata object.
        """
        # Use the test's specific recording file
        generated_name = generate_random_string(vcr_instance, cassette_name)
        folder_name = f"{generated_name}.Folder"
        folder_path = cli_path_join(path, folder_name)

        mkdir(folder_path)

        # Build the metadata for the created resource
        metadata = EntityMetadata(generated_name, folder_name, folder_path)
        if should_clean:
            created_folders.append(metadata)
        return metadata

    yield _create_folder

    # Remove all folders in inverse order of creation to avoid dependencies
    for metadata in reversed(created_folders):
        rm(metadata.full_path)

    state_config.set_config(
        fab_constant.FAB_FOLDER_LISTING_ENABLED, current_config)


@pytest.fixture
def virtual_item_factory(
    vcr_instance,
    cassette_name,
    workspace,
    item_factory,
    mock_print_done,
    test_data: StaticTestData,
):
    # Keep track of all virtual items created during this test
    created_virtual_items = []

    def _create_virtual_item(
        type: VirtualItemContainerType,
        workspace_path=workspace.full_path,
        params=None,
        should_clean=True,
    ):
        """
        Actually creates the virtual item resource and returns an EntityMetadata object.
        """
        generated_name = generate_random_string(vcr_instance, cassette_name)
        virtual_item_name = f"{generated_name}.{str(VICMap[type])}"
        virtual_item_path = cli_path_join(
            workspace_path, str(type), virtual_item_name)

        match type:

            case VirtualItemContainerType.EXTERNAL_DATA_SHARE:
                lakehouse = item_factory(ItemType.LAKEHOUSE)

                if params is None:
                    params = f"paths=[Files/images/taxi_zone_map_bronx.jpg],recipient.userPrincipalName=lisa@fabrikam.com,recipient.tenantId=c51dc03f-268a-4da0-a879-25f24947ab8b,item={lakehouse.full_path}"
                mkdir(virtual_item_path, params)

                # Get eds_name from print:
                created_print = mock_print_done.call_args[0][0]
                match = re.search(r"'(.*?)'", created_print)
                if match:
                    eds_long_name = match.group(1)
                else:
                    raise Exception(
                        "Unexpected error: could not find external data share name in print output"
                    )
                parts = eds_long_name.split(".")

                # Override name and path to contain actual name
                generated_name = ".".join(parts[:2])
                virtual_item_name = f"{generated_name}.{str(VICMap[type])}"
                virtual_item_path = cli_path_join(
                    workspace.full_path,
                    str(type),
                    virtual_item_name,
                )

            case VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT:
                if params is None:
                    subscription_id = test_data.azure_subscription_id
                    resource_group = test_data.azure_resource_group
                    sql_server = test_data.sql_server.server
                    params = f"targetPrivateLinkResourceId=/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{sql_server},targetSubresourceType=sqlServer"
                mkdir(virtual_item_path, params)

            case VirtualItemContainerType.MANAGED_IDENTITY:
                generated_name = workspace.display_name
                virtual_item_name = f"{generated_name}.{str(VICMap[type])}"
                virtual_item_path = cli_path_join(
                    workspace.full_path,
                    str(type),
                    virtual_item_name,
                )
                mkdir(virtual_item_path, params)

            case _:
                mkdir(virtual_item_path, params)

        # Build the metadata for the created resource
        metadata = EntityMetadata(
            generated_name, virtual_item_name, virtual_item_path)
        if should_clean:
            created_virtual_items.append(metadata)
        return metadata

    yield _create_virtual_item

    # Teardown: remove everything we created during the test
    for metadata in created_virtual_items:
        rm(metadata.full_path)


@pytest.fixture
def workspace_factory(vcr_instance, cassette_name, test_data: StaticTestData):
    # Keep track of all workspaces created during this test
    created_workspaces = []

    def _create_workspace(special_character=None):
        """
        Actually creates the workspace resource and returns an EntityMetadata object.
        """
        # Use the test's specific recording file
        generated_name = generate_random_string(vcr_instance, cassette_name)
        if special_character:
            generated_name = update_generated_name_with_special_character(
                vcr_instance, generated_name, special_character
            )
        workspace_name = f"{generated_name}.Workspace"
        workspace_path = f"/{workspace_name}"

        mkdir(workspace_path, params=[
              f"capacityName={test_data.capacity.name}"])

        # Build the metadata for the created resource
        metadata = EntityMetadata(
            generated_name, workspace_name, workspace_path)
        created_workspaces.append(metadata)
        return metadata

    yield _create_workspace

    # Teardown: remove everything we created during the test
    for metadata in created_workspaces:
        rm(metadata.full_path)


@pytest.fixture
def virtual_workspace_item_factory(
    vcr_instance,
    cassette_name,
    test_data: StaticTestData,
    setup_config_values_for_capacity,
):
    # Keep track of all workspaces created during this test
    created_virtual_workspace_items = []

    def _create_virtual_workspace_item(type: VirtualWorkspaceType):
        """
        Actually creates the workspace virtual item resource and returns an EntityMetadata object.
        """
        # Use the test's specific recording file
        generated_name = generate_random_string(vcr_instance, cassette_name)
        virtual_workspace_name = f"{generated_name}.{str(VWIMap[type])}"
        virtual_workspace_item_path = cli_path_join(
            f"/{str(type)}", virtual_workspace_name
        )
        params = None

        match type:
            case VirtualWorkspaceType.CONNECTION:
                params = [
                    f"connectionDetails.type=SQL,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.username={test_data.credential_details.username},credentialDetails.password={test_data.credential_details.password}"
                ]
            case VirtualWorkspaceType.GATEWAY:
                params = [
                    f"capacity={test_data.capacity.name},virtualNetworkName={test_data.vnet.name},subnetName={test_data.vnet.subnet}"
                ]

        mkdir(virtual_workspace_item_path, params=params)

        # Build the metadata for the created resource
        metadata = EntityMetadata(
            generated_name, virtual_workspace_name, virtual_workspace_item_path
        )
        created_virtual_workspace_items.append(metadata)
        return metadata

    yield _create_virtual_workspace_item

    # Teardown: remove everything we created during the test
    for metadata in created_virtual_workspace_items:
        rm(metadata.full_path)


def mkdir(element_full_path, params=None):
    state_config.set_config(fab_constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="mkdir",
        command_path="mkdir",
        path=element_full_path,
        params=params if params else ["run=true"],
    )

    context = handle_context.get_command_context(args.path, False)
    fab_fs_mkdir.exec_command(args, context)


def rm(element_full_path):
    state_config.set_config(fab_constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="rm",
        command_path="rm",
        path=element_full_path,
        force=True,
    )

    context = handle_context.get_command_context(args.path)
    fab_fs_rm.exec_command(args, context)


def import_cmd(element_full_path, content_path, format=None):
    state_config.set_config(fab_constant.FAB_CACHE_ENABLED, "false")
    args = argparse.Namespace(
        command="import",
        command_path="import",
        path=element_full_path,
        input=content_path,
        force=True,
        format=format,
    )

    context = handle_context.get_command_context(args.path, raise_error=False)
    fab_fs_import.exec_command(args, context)


def delete_cassette_if_record_mode_all(vcr_instance, cassette_name):
    """
    Deletes the cassette file if `record_mode` is set to 'all'.

    :param vcr_instance: The VCR instance being used.
    :param cassette_name: The name of the cassette file.
    """
    if vcr_instance.record_mode == "all":
        cassette_path = os.path.join(
            vcr_instance.cassette_library_dir, cassette_name)
        if os.path.exists(cassette_path):
            os.remove(cassette_path)


# region mock fixtures
@pytest.fixture(autouse=True)
def setup_default_format(mock_fab_set_state_config):
    mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "text")


@pytest.fixture(autouse=True)
def disable_cache():
    state_config.set_config(fab_constant.FAB_CACHE_ENABLED, "false")


@pytest.fixture(autouse=True, scope="class")
def disable_debug():
    state_config.set_config(fab_constant.FAB_DEBUG_ENABLED, "false")


@pytest.fixture
def mock_questionary_confirm():
    with patch("questionary.confirm") as mock:
        yield mock


@pytest.fixture
def mock_print_done():
    with patch("fabric_cli.utils.fab_ui.print_done") as mock:
        yield mock


@pytest.fixture()
def mock_print_grey():
    with patch("fabric_cli.utils.fab_ui.print_grey") as mock:
        yield mock


@pytest.fixture
def mock_fab_ui_print_error():
    with patch("fabric_cli.utils.fab_ui.print_output_error") as mock:
        yield mock


@pytest.fixture
def mock_fab_logger_log_warning():
    with patch("fabric_cli.core.fab_logger.log_warning") as mock:
        yield mock


@pytest.fixture(scope="class", autouse=True)
def mock_get_access_token(vcr_mode):
    if vcr_mode == "none":
        fab_auth_instance = FabAuth()  # Singleton
        with patch.object(
            fab_auth_instance, "get_access_token", return_value="mocked_access_token"
        ) as mock:
            yield mock
    else:
        yield


@pytest.fixture(autouse=True)
def mock_get_token_claims(request, vcr_mode):
    # Use a marker "custom_upn" from the test node to override the default.
    marker = request.node.get_closest_marker("token_claims")
    token_claims = marker.args[0] if marker else "some claim"

    def fake_get_token_claims(scope, claim_names):
        return token_claims

    fab_auth_instance = FabAuth()  # Singleton
    with patch.object(
        fab_auth_instance, "get_token_claims", side_effect=fake_get_token_claims
    ) as mock:
        yield mock


@pytest.fixture(scope="class", autouse=True)
def mock_time_sleep(vcr_mode):
    """
    This fixture intercepts time.sleep calls to skip real delays when running in playback mode (vcr_mode="none"),
    thereby avoiding redundant exponential waits for long-running operations and improving test execution speed.
    """
    if vcr_mode == "none":
        with patch("time.sleep", return_value="None"):
            yield
    else:
        yield


# endregion


# region test util fixtures
@pytest.fixture
def setup_config_values_for_capacity(test_data: StaticTestData):
    # Store existing values
    fab_default_az_subscription_id = state_config.get_config(
        fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID
    )
    fab_default_az_resource_group = state_config.get_config(
        fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP
    )
    fab_default_az_location = state_config.get_config(
        fab_constant.FAB_DEFAULT_AZ_LOCATION
    )
    fab_default_az_admin = state_config.get_config(
        fab_constant.FAB_DEFAULT_AZ_ADMIN)

    # Setup new values
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID,
        test_data.azure_subscription_id,
    )
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP,
        test_data.azure_resource_group,
    )
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_LOCATION, test_data.azure_location
    )
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_ADMIN, test_data.admin.upn)

    yield

    # Reset values
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, fab_default_az_subscription_id
    )
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, fab_default_az_resource_group
    )
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_LOCATION, fab_default_az_location
    )
    state_config.set_config(
        fab_constant.FAB_DEFAULT_AZ_ADMIN, fab_default_az_admin)


# endregion
