# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import tempfile
from argparse import Namespace

from fabric_cli.commands.jobs import fab_jobs as jobs


def exec_command(args: Namespace) -> None:
    args.jobType = "TableMaintenance"
    args.path = args.lakehouse_path
    args.jobs_command = "run"

    _config = json.loads(args.configuration)
    _config["tableName"] = args.table_name
    if args.schema:
        _config["schemaName"] = args.schema

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        with open(temp_file.name, "w") as fp:
            json.dump(_config, fp)

        args.configuration = None
        args.input = temp_file.name
        args.params = None
        jobs.run_command(args)
