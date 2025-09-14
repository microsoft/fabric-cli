# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from fabric_cli.client import fab_api_domain as domain_api
from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.hiearchy.fab_hiearchy import VirtualWorkspace
from fabric_cli.utils import fab_cmd_ls_utils as utils_ls
from fabric_cli.utils import fab_mem_store as utils_mem_store


def exec(vws: VirtualWorkspace, args, show_details):
    fab_logger.log_warning(fab_constant.WARNING_FABRIC_ADMIN_ROLE)
    domains = utils_mem_store.get_domains(vws.tenant)
    sorted_domains = utils_ls.sort_elements(
        [{"name": d.name, "id": d.id} for d in domains]
    )

    base_cols = ["name"]

    if show_details:
        domains_detail_cols = [
            "id",
            "contributorsScope",
            "description",
            "parentDomainId",
        ]
        fab_response = domain_api.list_domains(args)
        if fab_response.status_code in {200, 201}:
            _domains: list = json.loads(fab_response.text)["domains"]
            for domain in sorted_domains:
                domain_details: dict[str, str] = next(
                    (d for d in _domains if d["id"] == domain["id"]), {}
                )
                for col in domains_detail_cols:
                    domain[col] = domain_details.get(col, "Unknown")

                # enrich with parentDomainName
                domain["parentDomainName"] = utils_ls.get_domain_name_by_id(
                    domains, domain.get("parentDomainId")
                )
        domains_detail_cols.insert(3, "parentDomainName")

    columns = base_cols + domains_detail_cols if show_details else base_cols

    utils_ls.format_and_print_output(
        data=sorted_domains,
        columns=columns,
        args=args,
        show_details=show_details
    )
