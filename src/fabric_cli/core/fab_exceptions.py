# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import html
import json
import re

# Constants for common error messages and codes
DEFAULT_ERROR_MESSAGE = "An error occurred while processing the operation"
DEFAULT_ERROR_CODE = "UnknownError"


class FabricCLIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message.rstrip(".") if message else None
        self.status_code = status_code

    def __str__(self):
        return (
            f"[{self.status_code}] {self.args[0]}"
            if self.status_code
            else f"{self.args[0]}"
        )

    def formatted_message(self, verbose=False):
        escaped_text = html.escape(self.message) if self.message else ""

        return (
            f"[{self.status_code}] {escaped_text}"
            if self.status_code
            else f"{escaped_text}"
        )


class FabricAPIError(FabricCLIError):
    def __init__(self, response_text):
        """
        Represents an error response from the Fabric REST API.
        https://learn.microsoft.com/en-us/rest/api/fabric/core/items/get-item?tabs=HTTP#:~:text=Other%20Status%20Codes-,ErrorResponse,-Common%20error%20codes

        The error response follows this structure:
        {
            "errorCode": "string",                   # A specific identifier for the error condition.
            "message": "string",                     # A human-readable representation of the error.
            "moreDetails": [                         # A list of additional error details (optional).
                {
                    "errorCode": "string",           # The detail error code.
                    "message": "string",            # The detail error message.
                    "relatedResource": {            # Details about the related resource involved in the error (optional).
                        "resourceId": "string",     # The resource ID involved in the error.
                        "resourceType": "string"    # The type of the resource involved in the error.
                    }
                }
            ],
            "relatedResource": {                     # Details about the main related resource (optional).
                "resourceId": "string",             # The resource ID involved in the error.
                "resourceType": "string"            # The type of the resource involved in the error.
            },
            "requestId": "string"                   # The ID of the request associated with the error.
        }

        Attributes:
            error_code (str): The main error code.
            message (str): A descriptive message about the error.
            more_details (list): A list of additional error details, if available.
            related_resource (dict): Details about the main related resource, if available.
            request_id (str): The ID of the request associated with the error.
        """
        try:
            response = json.loads(response_text) if response_text else {}
            message = response.get("message")
            error_code = response.get("errorCode")
            self.more_details: list[dict] = response.get("moreDetails", [])
            self.request_id = response.get("requestId")
        except (json.JSONDecodeError, TypeError):
            message = DEFAULT_ERROR_MESSAGE
            error_code = DEFAULT_ERROR_CODE
            self.more_details = []
            self.request_id = None

        super().__init__(message, error_code)

    def formatted_message(self, verbose=False):
        base_message = super().formatted_message(verbose)

        detailed_message = html.escape(
            "\n".join(
                [
                    f"∟ [{detail.get('errorCode')}] {detail.get('message')}"
                    for detail in self.more_details
                ]
            )
        )

        final_message = (
            base_message
            if detailed_message == "" or not verbose
            else f"{base_message}\n<grey>{detailed_message}</grey>"
        )

        return f"{final_message}\n<grey>∟ Request Id: {self.request_id}</grey>"


class OnelakeAPIError(FabricCLIError):
    def __init__(self, response_text):
        """
        Represents an error response from the Data Lake Storage API.
        https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/read?view=rest-storageservices-datalakestoragegen2-2019-12-12#:~:text=Other%20Status%20Codes-,DataLakeStorageError,-An%20error%20occurred

        The error response follows this structure:
        {
            "error": {
                "code": "string",      # The service error code.
                "message": "string"    # The service error message.
            }
        }

        Attributes:
            code (str): The error code returned by the API.
            message (str): A descriptive message about the error.
        """
        # Initialize properties before parsing
        self.request_id = None
        self.timestamp = None
        
        try:
            response_data = json.loads(response_text) if response_text else {}
            error_data = response_data.get("error", {})
            code = error_data.get("code")
            message = error_data.get("message")

            if message:
                message = re.sub(r"\n(?=RequestId:)", "", message)
                match = re.search(r"RequestId:(\S+)", message)
                if match:
                    self.request_id = match.group(1)
                    message = message.replace(match.group(0), "")

                message = re.sub(r"\n(?=Time:)", "", message)
                match = re.search(r"Time:(\S+)", message)
                if match:
                    self.timestamp = match.group(1)
                    message = message.replace(match.group(0), "")
        except (json.JSONDecodeError, TypeError):
            message = DEFAULT_ERROR_MESSAGE
            code = DEFAULT_ERROR_CODE

        super().__init__(message, code)

    def formatted_message(self, verbose=False):
        message = super().formatted_message(verbose)

        if self.timestamp:
            message += f"\n<grey>∟ Timestamp: {self.timestamp}</grey>"

        if self.request_id:
            message += f"\n<grey>∟ Request Id: {self.request_id}</grey>"

        return message


class AzureAPIError(FabricCLIError):
    def __init__(self, response_text):
        """
        Represents an error response from the Azure REST API.
        https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/get?view=rest-microsoftfabric-2023-11-01&tabs=HTTP#errordetail:~:text=Other%20Status%20Codes-,ErrorResponse,-An%20unexpected%20error

        The error response follows this structure:
        {
            "error": {
                "code": "string",                   # The error code.
                "message": "string",                # The error message.
                "target": "string",                 # The error target (optional).
                "details": [                        # A list of additional error details (optional).
                    {
                        "code": "string",           # The detail error code.
                        "message": "string",        # The detail error message.
                        "target": "string",         # The detail error target (optional).
                        "additionalInfo": [         # Additional information (optional).
                            {
                                "type": "string",   # The type of additional info.
                                "info": {}          # The additional info object.
                            }
                        ]
                    }
                ],
                "additionalInfo": [                 # Additional information at the main error level (optional).
                    {
                        "type": "string",           # The type of additional info.
                        "info": {}                  # The additional info object.
                    }
                ]
            }
        }

        Attributes:
            code (str): The main error code.
            message (str): A descriptive message about the error.
            target (str, optional): The target of the error.
            details (list): A list of additional error details, if available.
            additional_info (list): Additional info at the main error level, if available.
        """
        # Initialize properties before parsing
        self.request_id = None
        
        try:
            response_data = json.loads(response_text) if response_text else {}
            error_data = response_data.get("error", {})
            code = error_data.get("code")
            message = error_data.get("message")

            details: list[dict] = error_data.get("details", [])

            for detail in details:
                if detail.get("code") == "RootActivityId":
                    self.request_id = detail.get("message")
                    break
        except (json.JSONDecodeError, TypeError):
            message = DEFAULT_ERROR_MESSAGE
            code = DEFAULT_ERROR_CODE

        super().__init__(message, code)

    def formatted_message(self, verbose=False):
        final_message = super().formatted_message(verbose)

        if self.request_id:
            final_message += f"\n<grey>∟ Request Id: {self.request_id}</grey>"

        return final_message
