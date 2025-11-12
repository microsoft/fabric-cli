# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Optional


class CommonErrors:

    @staticmethod
    def invalid_jmespath_query() -> str:
        return f"Invalid jmespath query (https://jmespath.org)"

    @staticmethod
    def invalid_hostname(hostname: str) -> str:
        return f"Invalid hostname for '{hostname}'"

    @staticmethod
    def invalid_result_format() -> str:
        return f"Invalid result format provided - can't be None or empty"

    @staticmethod
    def invalid_element_type(element_type: str) -> str:
        return f"'{element_type}' is not a valid Fabric element type"

    @staticmethod
    def invalid_workspace_type(workspace_type: str) -> str:
        return f"'{workspace_type}' is not a valid Fabric workspace type"

    @staticmethod
    def invalid_item_type(item_type: str) -> str:
        return f"'{item_type}' is not a valid Fabric item type"

    @staticmethod
    def invalid_virtual_workspace_type(vws_type: str) -> str:
        return f"'{vws_type}' is not a valid Fabric virtual workspace type"

    @staticmethod
    def invalid_virtual_item_container_type(vic_type: str) -> str:
        return f"'{vic_type}' is not a valid Fabric virtual item container type"

    @staticmethod
    def file_or_directory_not_exists() -> str:
        return "The specified file or directory does not exist"

    @staticmethod
    def invalid_json_format() -> str:
        return "Invalid JSON format"

    @staticmethod
    def type_not_supported(type_name: str) -> str:
        return f"The type '{type_name}' is not supported"

    @staticmethod
    def invalid_path(path: Optional[str] = None) -> str:
        return (
            f"The path '{path}' is invalid" if path else "The specified path is invalid"
        )

    @staticmethod
    def invalid_guid(parameter_name: str) -> str:
        return f"The parameter '{parameter_name}' must be a valid GUID"

    @staticmethod
    def unauthorized() -> str:
        return "Access is unauthorized"

    @staticmethod
    def forbidden() -> str:
        return "Access is forbidden. You do not have permission to access this resource"

    @staticmethod
    def max_retries_exceeded(retries_count: int) -> str:
        return f"Maximum retries ({retries_count}) exceeded. The operation could not be completed"

    @staticmethod
    def unexpected_error(error: str) -> str:
        return f"An unexpected error occurred: {error}"

    @staticmethod
    def operation_failed(error: str) -> str:
        return f"The operation failed: {error}"

    @staticmethod
    def operation_cancelled(error: str) -> str:
        return f"The operation was cancelled: {error}"

    @staticmethod
    def invalid_headers_format() -> str:
        return "The headers format is invalid"

    @staticmethod
    def invalid_json_content(content: str, error: Optional[str]) -> str:
        base_msg = f"The JSON content is invalid: {content}"
        return f"{base_msg}. Error: {error}" if error else f"{base_msg}"

    @staticmethod
    def resource_not_found(resource: Optional[dict] = None) -> str:
        return (
            f"The {resource['type']} '{resource['name']}' could not be found"
            if resource
            else "The requested resource could not be found"
        )

    @staticmethod
    def json_decode_error(error: str) -> str:
        return f"Failed to decode JSON: {error}"

    @staticmethod
    def traversing_not_supported(path: str) -> str:
        return f"Traversing into '{path}' is not supported"

    @staticmethod
    def personal_workspace_not_found() -> str:
        return "The personal workspace could not be found"

    @staticmethod
    def personal_workspace_user_auth_only() -> str:
        return "The personal workspace is only available with user authentication"

    @staticmethod
    def folder_not_found_in_item(
        folder: str, item_name: str, valid_folders: str
    ) -> str:
        return f"The folder '{folder}' could not be found in item '{item_name}'. Valid folders are: {valid_folders}"

    @staticmethod
    def path_not_found(path: str) -> str:
        return f"The path '{path}' could not be found"

    @staticmethod
    def item_not_supported_in_context(item_type: str, context_type: str) -> str:
        return f"The item type '{item_type}' is not supported in the context '{context_type}'"

    @staticmethod
    def item_not_supported(item_type: str) -> str:
        return f"The item type '{item_type}' is not supported"

    @staticmethod
    def output_format_not_supported(output_type: str) -> str:
        return f"Output format {output_type} not supported"

    @staticmethod
    def folder_not_found(folder_name: str) -> str:
        return f"Folder '{folder_name}' not found"

    @staticmethod
    def universal_security_disabled(name: str) -> str:
        return f"Universal security is disabled for '{name}'"

    @staticmethod
    def job_instance_failed(job_id: str) -> str:
        return f"Job instance '{job_id}' Failed"

    @staticmethod
    def file_not_accessible(file_path: str) -> str:
        return f"Cannot access '{file_path}'. No such file or directory"

    @staticmethod
    def no_such_file_or_directory() -> str:
        return "No such file or directory"

    @staticmethod
    def only_supported_for_lakehouse_files() -> str:
        return "Only supported for Lakehouse/Files"

    @staticmethod
    def file_not_found(file_path: str) -> str:
        return f"The file at {file_path} was not found"

    @staticmethod
    def file_not_valid_json(file_path: str) -> str:
        return f"The file at {file_path} is not a valid JSON file"

    @staticmethod
    def invalid_destination_expected_file_or_folder() -> str:
        return "Invalid destination, expected file or writable folder"

    @staticmethod
    def cannot_write_in_folder(root_folder: str, item_type: str, supported_folders: str) -> str:
        return f"Cannot write in folder '{root_folder}' for {item_type}. Only {supported_folders} folders are supported"

    @staticmethod
    def invalid_creation_method_for_connection(
        con_type: str, supported_creation_methods: list
    ) -> str:
        return f"Invalid creation method. Supported creation methods for {con_type} are {supported_creation_methods}"

    @staticmethod
    def missing_connection_creation_method_or_parameters(
        supported_creation_methods: list,
    ) -> str:
        return f"Missing connection creation method and parameters. Please indicate either one of the following creation methods: {supported_creation_methods}, or provide parameters for automatic selection"
    
    @staticmethod
    def missing_onpremises_gateway_parameters(
        missing_params: list,
    ) -> str:
        return  f"Missing parameters for credential values in OnPremisesGateway connectivity type: {missing_params}"

    @staticmethod
    def invalid_onpremises_gateway_values() -> str:
        return "Values must be a list of JSON objects, each containing 'gatewayId' and 'encryptedCredentials' keys"
