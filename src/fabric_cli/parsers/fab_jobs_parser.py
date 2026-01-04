# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.jobs import fab_jobs as jobs
from fabric_cli.core import fab_constant
from fabric_cli.parsers.fab_parser_validators import validate_positive_int
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui

commands = {
    "Commands": {
        "start": "Start an item asynchronously.",
        "run": "Run an item synchronously.",
        "run-cancel": "Cancel a running or scheduled job.",
        "run-list": "List job runs for an item.",
        "run-update": "Update a scheduled job.",
        "run-rm": "Remove a scheduled job.",
        "run-sch": "Schedule a job for an item.",
        "run-status": "Get job run status.",
    },
}


def register_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("job", help=fab_constant.COMMAND_JOBS_DESCRIPTION)
    parser.set_defaults(func=show_help)
    jobs_subparsers = parser.add_subparsers(dest="jobs_command")

    # Subcommand for 'start'
    start_examples = [
        "# run a pipeline async",
        "$ job start pip1.DataPipeline\n",
        "# run a notebook async",
        "$ job start nb1.Notebook --input <json_path>",
    ]

    start_parser = jobs_subparsers.add_parser(
        "start",
        help="Start an item",
        fab_examples=start_examples,
        fab_learnmore=["_"],
    )
    start_parser.add_argument("path", nargs="+", help="Path to the item")
    start_parser.add_argument(
        "-P",
        "--params",
        required=False,
        metavar="",
        nargs="+",
        help="Parameters in name:type=value format, separated by commas. Optional.",
    )
    start_parser.add_argument(
        "-C",
        "--config",
        nargs="+",
        help="JSON payload for configuration of a Notebook, inline or path. Optional",
    )
    start_parser.add_argument(
        "-i", "--input", nargs="+", help="JSON payload, inline or path. Optional"
    )

    start_parser.usage = f"{utils_error_parser.get_usage_prog(start_parser)}"
    start_parser.set_defaults(func=jobs.run_command)

    # Subcommand for 'run'
    run_examples = [
        "# run a pipeline sync",
        "$ job run pip1.DataPipeline\n",
        "# run a pipeline sync with a 60 second timeout",
        "$ job run pip1.DataPipeline --timeout 60\n",
        "# run a notebook with custom 30-second polling interval",
        "$ job run nb1.Notebook --input <json_path> --polling_interval 30\n",
        "# run a notebook async",
        "$ job run nb1.Notebook --input <json_path>",
    ]

    run_parser = jobs_subparsers.add_parser(
        "run",
        help="Run an item",
        fab_examples=run_examples,
        fab_learnmore=["_"],
    )
    run_parser.add_argument("path", nargs="+", help="Path to the item")
    run_parser.add_argument(
        "-P",
        "--params",
        required=False,
        metavar="",
        nargs="+",
        help="Parameters in name:type=value format, separated by commas. Optional.",
    )
    run_parser.add_argument(
        "-C",
        "--config",
        nargs="+",
        help="JSON payload for configuration of a Notebook, inline or path. Optional",
    )
    run_parser.add_argument(
        "-i", "--input", nargs="+", help="JSON payload, inline or path. Optional"
    )
    run_parser.add_argument(
        "--timeout", metavar="", help="Timeout in seconds. Optional", type=int
    )
    run_parser.add_argument(
        "--polling_interval",
        metavar="",
        dest="polling_interval",
        help="Custom job status polling interval in seconds. Optional",
        type=validate_positive_int,
    )

    run_parser.usage = f"{utils_error_parser.get_usage_prog(run_parser)}"
    run_parser.set_defaults(func=jobs.run_command)

    # Subcommand for 'run_list'
    list_examples = [
        "# list pipeline runs",
        "$ job run-list pip1.DataPipeline\n",
        "# list pipeline schedule runs",
        "$ job run-list pip1.DataPipeline --schedule",
    ]

    run_list_parser = jobs_subparsers.add_parser(
        "run-list",
        help="List job runs",
        fab_examples=list_examples,
        fab_learnmore=["_"],
    )
    run_list_parser.add_argument(
        "path",
        nargs="+",
        help="Path to the item",
    )
    run_list_parser.add_argument(
        "--schedule", help="Schedule runs. Optional", action="store_true"
    )

    run_list_parser.usage = f"{utils_error_parser.get_usage_prog(run_list_parser)}"
    run_list_parser.set_defaults(func=jobs.run_list_command)

    # Subcommand for 'run_cancel'
    cancel_examples = [
        "# cancel pipeline run",
        "$ job run-cancel pip1.DataPipeline --id <instance_id>\n",
        "# cancel pipeline run and wait",
        "$ job run-cancel pip1.DataPipeline --id <instance_id> --wait\n",
    ]

    run_cancel_parser = jobs_subparsers.add_parser(
        "run-cancel",
        help="Cancel an item or scheduled run",
        fab_examples=cancel_examples,
        fab_learnmore=["_"],
    )
    run_cancel_parser.add_argument("path", nargs="+", help="Path to the item")
    run_cancel_parser.add_argument(
        "--id",
        required=True,
        metavar="",
        dest="id",
        help="Job Schedule or Execution ID",
    )
    run_cancel_parser.add_argument(
        "-w", "--wait", action="store_true", help="Wait for the job to cancel. Optional"
    )

    run_cancel_parser.usage = f"{utils_error_parser.get_usage_prog(run_cancel_parser)}"
    run_cancel_parser.set_defaults(func=jobs.run_cancel_command)

    # Subcommand for 'run_sch'
    sch_examples = [
        "# set up pipeline schedule to run every 10 minutes and enable it",
        "$ job run-sch pip1.DataPipeline --type cron --interval 10 --start 2024-11-15T09:00:00 --end 2024-12-15T10:00:00 --enable \n",
        "# set up pipeline schedule to run every day at 10:00 and 16:00 (disabled by default)",
        "$ job run-update pip1.DataPipeline --id <schedule_id> --type daily --interval 10:00,16:00 --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00 \n",
        "# set up pipeline schedule to run every Monday and Friday at 10:00 and 16:00, disabled by default",
        "$ job run-sch pip1.DataPipeline --type weekly --interval 10:00,16:00 --days Monday,Friday --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00 \n",
        "# set up pipeline schedule with custom input",
        "$ job run-sch pip1.DataPipeline --input {'enabled': true, 'configuration': {'startDateTime': '2024-04-28T00:00:00', 'endDateTime': '2024-04-30T23:59:00', 'localTimeZoneId': 'Central Standard Time', 'type': 'Cron', 'interval': 10}} ",
    ]

    run_sch_parser = jobs_subparsers.add_parser(
        "run-sch",
        help="Schedule a job for an item.",
        fab_examples=sch_examples,
        fab_learnmore=["_"],
    )
    run_sch_parser.add_argument("path", nargs="+", help="Path to the item")
    run_sch_parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=False,
        help="JSON payload, inline or path",
    )
    run_sch_parser.add_argument(
        "--enable", action="store_true", help="Enable schedule. Optional"
    )
    run_sch_parser.add_argument(
        "--type",
        choices=["cron", "daily", "weekly"],
        help="Type of schedule (cron, daily, weekly). Optional",
    )
    run_sch_parser.add_argument(
        "--interval", metavar="", help="Interval in minutes or time list. Optional"
    )
    run_sch_parser.add_argument(
        "--start", metavar="", help="Start date and time in UTC. Optional"
    )
    run_sch_parser.add_argument(
        "--end", metavar="", help="End date and time in UTC. Optional"
    )
    run_sch_parser.add_argument("--days", metavar="", help="Days of the week. Optional")
    run_sch_parser.usage = f"{utils_error_parser.get_usage_prog(run_sch_parser)}"
    run_sch_parser.set_defaults(func=jobs.run_sch_command)

    # Subcommand for 'run_update'
    update_examples = [
        "# disable pipeline schedule",
        "$ job run-update pip1.DataPipeline --id <schedule_id> --disabled \n",
        "# update pipeline schedule to run every 10 minutes and enable it",
        "$ job run-update pip1.DataPipeline --id <schedule_id> --type cron --interval 10 --start 2024-11-15T09:00:00 --end 2024-12-15T10:00:00 --enable \n",
        "# update pipeline schedule to run every day at 10:00 and 16:00 (maintain the existing enabled state)",
        "$ job run-update pip1.DataPipeline --id <schedule_id> --type daily --interval 10:00,16:00 --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00 \n",
        "# update pipeline schedule to run every Monday and Friday at 10:00 and 16:00 and enable it",
        "$ job run-update pip1.DataPipeline --id <schedule_id> --type weekly --interval 10:00,16:00 --days Monday,Friday --start 2024-11-15T09:00:00 --end 2024-12-16T10:00:00 --enable \n",
        "# update pipeline schedule with custom input",
        "$ job run-update pip1.DataPipeline --id <schedule_id> --input {'enabled': true, 'configuration': {'startDateTime': '2024-04-28T00:00:00', 'endDateTime': '2024-04-30T23:59:00', 'localTimeZoneId': 'Central Standard Time', 'type': 'Cron', 'interval': 10}} ",
    ]

    run_update_parser = jobs_subparsers.add_parser(
        "run-update",
        help="Updated the schedule of an item job",
        fab_examples=update_examples,
        fab_learnmore=["_"],
    )
    run_update_parser.add_argument("path", nargs="+", help="Path to the item")
    run_update_parser.add_argument(
        "--id",
        required=True,
        metavar="",
        dest="schedule_id",
        help="Job Schedule ID",
    )
    run_update_parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=False,
        help="JSON payload, inline or path. Optional",
    )
    run_update_parser.add_argument(
        "--enable", action="store_true", help="Enable schedule. Optional"
    )
    run_update_parser.add_argument(
        "--disable", action="store_false", help="Disable schedule. Optional"
    )
    run_update_parser.add_argument(
        "--type",
        choices=["cron", "daily", "weekly"],
        help="Type of schedule (cron, daily, weekly). Optional",
    )
    run_update_parser.add_argument(
        "--interval", metavar="", help="Interval in minutes or time list. Optional"
    )
    run_update_parser.add_argument(
        "--start", metavar="", help="Start date and time in UTC. Optional"
    )
    run_update_parser.add_argument(
        "--end", metavar="", help="End date and time in UTC. Optional"
    )
    run_update_parser.add_argument(
        "--days", metavar="", help="Days of the week. Optional"
    )
    run_update_parser.set_defaults(func=jobs.run_update_command)

    # Subcommand for 'run_rm'
    rm_examples = [
        "# remove pipeline schedule",
        "$ job run-rm pip1.DataPipeline --id <schedule_id>\n",
        "# remove notebook schedule",
        "$ job run-rm nb1.Notebook --id <schedule_id>\n",
        "# remove Spark job definition schedule",
        "$ job run-rm sjd1.SparkJobDefinition --id <schedule_id>\n",
        "# remove lakehouse schedule",
        "$ job run-rm lh1.Lakehouse --id <schedule_id>\n",
        "# Force remove a scheduled job without confirmation prompt",
        "$ job run-rm pip1.DataPipeline --id <schedule_id> -f\n",
    ]

    run_rm_parser = jobs_subparsers.add_parser(
        "run-rm",
        help="Remove a scheduled job",
        fab_examples=rm_examples,
        fab_learnmore=["_"],
    )
    run_rm_parser.add_argument("path", nargs="+", help="Path to the item")
    run_rm_parser.add_argument(
        "--id",
        required=True,
        metavar="",
        dest="schedule_id",
        help="Job Schedule ID",
    )
    run_rm_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force delete the schedule without confirmation. Optional",
    )
    run_rm_parser.usage = f"{utils_error_parser.get_usage_prog(run_rm_parser)}"
    run_rm_parser.set_defaults(func=jobs.run_rm_command)

    # Subcommand for 'run_status'
    status_examples = [
        "# Check the status of a pipeline instance job",
        "$ job run-status pip1.DataPipeline --id <instance_id>\n",
        "# Check the status of a notebook scheduled job",
        "$ job run-status nb1.Notebook --id <schedule_id> --schedule",
    ]

    run_status_parser = jobs_subparsers.add_parser(
        "run-status",
        help="List job runs",
        fab_examples=status_examples,
        fab_learnmore=["_"],
    )
    run_status_parser.add_argument("path", nargs="+", help="Path to the item")
    run_status_parser.add_argument(
        "--id",
        required=True,
        metavar="",
        dest="id",
        help="Job Schedule or Execution ID",
    )
    run_status_parser.add_argument(
        "--schedule", action="store_true", help="Schedule runs. Optional"
    )
    run_status_parser.usage = f"{utils_error_parser.get_usage_prog(run_status_parser)}"
    run_status_parser.set_defaults(func=jobs.run_status_command)


def show_help(args: Namespace) -> None:
    utils_ui.display_help(commands, custom_header=fab_constant.COMMAND_JOBS_DESCRIPTION)
