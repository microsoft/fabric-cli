# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspaceItem
from fabric_cli.utils import fab_cmd_mkdir_utils as mkdir_utils
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui as utils_ui


def exec(domain: VirtualWorkspaceItem, args: Namespace) -> None:
    optional_params = ["description", "parentDomainName"]
    if mkdir_utils.show_params_desc(
        args.params, domain.item_type, optional_params=optional_params
    ):
        return

    fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMINISTRATOR)
    utils_ui.print_grey(f"Creating a new Domain...")

    payload = {"displayName": f"{domain.short_name}"}
    optional_payload = {}

    params = args.params

    for key in optional_params:
        lowercase_key = key.lower()
        if params.get(lowercase_key):
            # Convert name to id
            if lowercase_key == "parentdomainname":
                domain_name = params[lowercase_key]
                domain_name = domain_name.removesuffix(".domain").removesuffix(
                    ".Domain"
                )
                domain_name += ".Domain"

                value = utils_mem_store.get_domain_id(domain.tenant, domain_name)
                optional_payload["parentDomainId"] = value
            else:
                value = params[lowercase_key]
                optional_payload[lowercase_key] = value

    payload.update(optional_payload)
    json_payload = json.dumps(payload)

    response = domain_api.create_domain(args, payload=json_payload)
    if response.status_code in (200, 201):
        data = json.loads(response.text)
        utils_ui.print_output_format(
            args, message=f"'{domain.name}' created", data=data, show_headers=True
        )

        domain._id = data["id"]

        # Add to mem_store
        utils_mem_store.upsert_domain_to_cache(domain)
