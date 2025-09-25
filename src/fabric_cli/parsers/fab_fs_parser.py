# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.fs import fab_fs as fs
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser


def register_ls_parser(subparsers: _SubParsersAction) -> None:
    ls_aliases = ["dir"]
    ls_examples = [
        "# list all workspaces with details",
        "$ ls -l\n",
        "# list lakehouse tables",
        "$ ls ws1.Workspace/lh1.Lakehouse/Tables",
    ]

    ls_parser = subparsers.add_parser(
        "ls",
        aliases=ls_aliases,
        help=fab_constant.COMMAND_FS_LS_DESCRIPTION,
        fab_examples=ls_examples,
        fab_aliases=ls_aliases,
        fab_learnmore=["_"],
    )
    ls_parser.add_argument(
        "path", nargs="*", type=str, default=None, help="Directory path"
    )
    ls_parser.add_argument(
        "-l",
        "--long",
        required=False,
        action="store_true",
        help="Show detailed output. Optional",
    )
    ls_parser.add_argument(
        "-a",
        "--all",
        required=False,
        action="store_true",
        help="Show all. Optional",
    )

    ls_parser.usage = f"{utils_error_parser.get_usage_prog(ls_parser)}"
    ls_parser.set_defaults(func=fs.ls_command)


# Command for 'mkdir'
def register_mkdir_parser(subparsers: _SubParsersAction) -> None:
    mkdir_aliases = ["create"]
    mkdir_examples = [
        "# create an empty notebook",
        "$ mkdir ws1.Workspace/nb1.Notebook\n",
        "# create a directory (Lakehouse only)",
        "$ mkdir ws1.Workspace/lh1.Lakehouse/Files/fabdir",
    ]
    mkdir_learnmore = [
        "Tip: Use `-P` to view custom parameters per item type (e.g., `mkdir nb1.Notebook -P`)"
    ]

    mkdir_parser = subparsers.add_parser(
        "mkdir",
        aliases=mkdir_aliases,
        help=fab_constant.COMMAND_FS_MKDIR_DESCRIPTION,
        fab_examples=mkdir_examples,
        fab_aliases=mkdir_aliases,
        fab_learnmore=mkdir_learnmore,
    )
    mkdir_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    mkdir_parser.add_argument(
        "-P",
        "--params",
        required=False,
        default=["run=true"],
        metavar="",
        nargs="*",  # Allow zero or more arguments
        help="Parameters in key=value format, separated by commas. Optional.",
    )

    mkdir_parser.usage = f"{utils_error_parser.get_usage_prog(mkdir_parser)}"
    mkdir_parser.set_defaults(func=fs.mkdir_command)


# Command for 'cd'
def register_cd_parser(subparsers: _SubParsersAction) -> None:
    cd_examples = [
        "# using absolute path",
        "$ cd /ws1.Workspace/nb1.Notebook\n",
        "# using relative path",
        "$ cd ../../ws2.Workspace",
    ]

    cd_parser = subparsers.add_parser(
        "cd",
        help="Change directory",
        fab_examples=cd_examples,
        fab_learnmore=["_"],
    )
    cd_parser.add_argument("path", nargs="+", type=str, help="Directory path")

    cd_parser.usage = f"{utils_error_parser.get_usage_prog(cd_parser)}"
    cd_parser.set_defaults(func=fs.cd_command)


def register_rm_parser(subparsers: _SubParsersAction) -> None:
    rm_aliases = ["del"]
    rm_examples = [
        "# remove selected items from a workspace (selective)",
        "$ rm ws1.Workspace\n",
        "# remove a table",
        "$ rm lh1.Lakehouse/Tables/fabtbl",
    ]

    rm_parser = subparsers.add_parser(
        "rm",
        aliases=rm_aliases,
        help=fab_constant.COMMAND_FS_RM_DESCRIPTION,
        fab_examples=rm_examples,
        fab_aliases=rm_aliases,
        fab_learnmore=["_"],
    )
    rm_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    rm_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    rm_parser.usage = f"{utils_error_parser.get_usage_prog(rm_parser)}"
    rm_parser.set_defaults(func=fs.rm_command)


def register_mv_parser(subparsers: _SubParsersAction) -> None:
    mv_aliases = ["move"]
    mv_examples = [
        "# move items from one workspace to another one",
        "$ mv ws1.Workspace ws2.Workspace\n",
        "# move a notebook",
        "$ mv nb1.Notebook mv_nb1.Notebook -f\n",
        "# move file from one folder to another",
        "$ mv Files/csv/fab.csv Files/dest/fab.csv",
    ]

    mv_parser = subparsers.add_parser(
        "mv",
        aliases=mv_aliases,
        help=fab_constant.COMMAND_FS_MV_DESCRIPTION,
        fab_examples=mv_examples,
        fab_aliases=mv_aliases,
        fab_learnmore=["_"],
    )
    mv_parser.add_argument("from_path", nargs="+", type=str, help="Source path")
    mv_parser.add_argument("to_path", nargs="+", type=str, help="Target path")
    mv_parser.add_argument(
        "-f",
        "--force",
        required=False,
        action="store_true",
        help="Force. Optional, Overrides confirmation prompts. Moves the item definition without the sensitivity label and overwrites an item if already exists in the destination",
    )
    mv_parser.add_argument(
        "-r",
        "--recursive",
        required=False,
        action="store_true",
        help="Recursive. Optional, moves all items in the source path recursively, including subfolders and their contents. This option is only applicable for workspaces and folders.",
    )

    mv_parser.usage = f"{utils_error_parser.get_usage_prog(mv_parser)}"
    mv_parser.set_defaults(func=fs.mv_command)


def register_cp_parser(subparsers: _SubParsersAction) -> None:
    cp_aliases = ["copy"]
    cp_examples = [
        "# copy items from one workspace to another one",
        "$ cp ws1.Workspace ws2.Workspace\n",
        "# copy a notebook",
        "$ cp nb1.Notebook nb2.Notebook\n",
        "# copy file from one folder to another",
        "$ cp Files/csv/fab.csv Files/dest/copy_fab.csv",
    ]

    cp_parser = subparsers.add_parser(
        "cp",
        aliases=cp_aliases,
        help=fab_constant.COMMAND_FS_CP_DESCRIPTION,
        fab_examples=cp_examples,
        fab_aliases=cp_aliases,
        fab_learnmore=["_"],
    )

    cp_parser.add_argument("from_path", nargs="+", type=str, help="Source path")
    cp_parser.add_argument("to_path", nargs="+", type=str, help="Target path")
    cp_parser.add_argument(
        "-f",
        "--force",
        required=False,
        action="store_true",
        help="Force. Optional, Overrides confirmation prompts. Copies the item definition without the sensitivity label and overwrites an item if already exists in the destination.",
    )
    cp_parser.add_argument(
        "-r",
        "--recursive",
        required=False,
        action="store_true",
        help="Recursive. Optional, copies all items in the source path recursively, including subfolders and their contents. This option is only applicable for workspaces and folders.",
    )
    cp_parser.add_argument(
        "-ftp",
        "--force-target-path",
        required=False,
        action="store_true",
        help="Force target path. Optional, prevents copying when an item with the same name exists in a different folder within the target workspace.",
    )

    cp_parser.usage = f"{utils_error_parser.get_usage_prog(cp_parser)}"
    cp_parser.set_defaults(func=fs.cp_command)


# Command for 'exists'
def register_exists_parser(subparsers: _SubParsersAction) -> None:
    exists_examples = [
        "# check if a workspace exists",
        "$ exists /ws1.Workspace\n",
        "# check if an item exists",
        "$ exists /ws1.Workspace/lh1.Lakehouse",
    ]

    exists_parser = subparsers.add_parser(
        "exists",
        help=fab_constant.COMMAND_FS_EXISTS_DESCRIPTION,
        fab_examples=exists_examples,
        fab_learnmore=["_"],
    )
    exists_parser.add_argument("path", nargs="+", type=str, help="Directory path")

    exists_parser.usage = f"{utils_error_parser.get_usage_prog(exists_parser)}"
    exists_parser.set_defaults(func=fs.exists_command)


# Command for 'pwd'
def register_pwd_parser(subparsers: _SubParsersAction) -> None:
    pwd_examples = ["# print working directory", "$ pwd"]
    pwd_parser = subparsers.add_parser(
        "pwd",
        help=fab_constant.COMMAND_FS_PWD_DESCRIPTION,
        fab_examples=pwd_examples,
        fab_learnmore=["_"],
    )

    pwd_parser.usage = f"{utils_error_parser.get_usage_prog(pwd_parser)}"
    pwd_parser.set_defaults(func=fs.pwd_command)


# Command for 'open'
def register_open_parser(subparsers: _SubParsersAction) -> None:
    open_examples = [
        "# open a workspace in the browser",
        "$ open ws1.Workspace\n",
        "# open a Power BI report in the browser",
        "$ open ws1.Workspace/rep1.Report",
    ]

    open_parser = subparsers.add_parser(
        "open",
        help=fab_constant.COMMAND_FS_OPEN_DESCRIPTION,
        fab_examples=open_examples,
        fab_learnmore=["_"],
    )
    open_parser.add_argument("path", nargs="+", type=str, help="Directory path")

    open_parser.usage = f"{utils_error_parser.get_usage_prog(open_parser)}"
    open_parser.set_defaults(func=fs.open_command)


# Command for 'export'
def register_export_parser(subparsers: _SubParsersAction) -> None:
    export_examples = [
        "# export multiple items from a workspace to local",
        "$ export ws1.Workspace -o /tmp\n",
        "# export a single item to a lakehouse",
        "$ export ws1.Workspace/rep1.Report -o /ws1.Workspace/lh1.Lakehouse/Files/export -f",
    ]

    export_parser = subparsers.add_parser(
        "export",
        help=fab_constant.COMMAND_FS_EXPORT_DESCRIPTION,
        fab_examples=export_examples,
        fab_learnmore=["_"],
    )
    export_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    export_parser.add_argument(
        "-o",
        "--output",
        nargs="+",
        metavar="",
        required=True,
        help="Output path for export",
    )
    export_parser.add_argument(
        "-a",
        "--all",
        required=False,
        action="store_true",
        help="Export all. Optional",
    )
    export_parser.add_argument(
        "-f",
        "--force",
        required=False,
        action="store_true",
        help="Force. Optional, Overrides confirmation prompts. Exports the item definition without the sensitivity label",
    )

    export_parser.usage = f"{utils_error_parser.get_usage_prog(export_parser)}"
    export_parser.set_defaults(func=fs.export_command)


# Command for 'get'
def register_get_parser(subparsers: _SubParsersAction) -> None:
    get_examples = [
        "# get workspace properties",
        "$ get ws1.Workspace -q .\n",
        "# get report properties and output",
        "$ get ws1.Workspace/rep1.Report -q <jmespath> -o <export_path>",
    ]
    get_learnmore = [
        "Tip: Run `get <path>` to view queryable JSON properties (e.g. get ws1.Workspace)"
    ]

    get_parser = subparsers.add_parser(
        "get",
        help=fab_constant.COMMAND_FS_GET_DESCRIPTION,
        fab_examples=get_examples,
        fab_learnmore=get_learnmore,
    )
    get_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    get_parser.add_argument(
        "-q",
        "--query",
        metavar="",
        nargs="+",
        required=False,
        help="JMESPath query to filter. Optional",
    )
    get_parser.add_argument(
        "-o",
        "--output",
        metavar="",
        nargs="+",
        required=False,
        help="Output path for export. Optional",
    )
    get_parser.add_argument(
        "-v",
        "--verbose",
        required=False,
        action="store_true",
        help="Verbose, show all JSON properties. Optional",
    )
    get_parser.add_argument(
        "-f",
        "--force",
        required=False,
        action="store_true",
        help="Force. Optional, Overrides confirmation prompts. Gets the item definition without the sensitivity label",
    )

    get_parser.usage = f"{utils_error_parser.get_usage_prog(get_parser)}"
    get_parser.set_defaults(func=fs.get_command)


# Command for 'import'
def register_import_parser(subparsers: _SubParsersAction) -> None:
    import_examples = [
        "# import a notebook from a local directory",
        "$ import imp.Notebook -i /tmp/nb1.Notebook\n",
        "# import a pipeline from a local directory",
        "$ import pip.Notebook -i /tmp/pip1.DataPipeline -f",
    ]

    import_parser = subparsers.add_parser(
        "import",
        help=fab_constant.COMMAND_FS_IMPORT_DESCRIPTION,
        fab_examples=import_examples,
        fab_learnmore=["_"],
    )
    import_parser.add_argument(
        "path", nargs="+", type=str, help="Directory path (item name to import)"
    )
    import_parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=True,
        help="Input path for import",
    )
    import_parser.add_argument(
        "--format",
        metavar="",
        help="Input format. Optional, supported for notebooks (.ipynb, .py)",
    )
    import_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    import_parser.usage = f"{utils_error_parser.get_usage_prog(import_parser)}"
    import_parser.set_defaults(func=fs.import_command)


# Command for 'set'
def register_set_parser(subparsers: _SubParsersAction) -> None:
    set_examples = [
        "# rename a workspace",
        "$ set ws2.Workspace -q displayName -i ws2r\n",
        "# assign a custom pool",
        "$ set ws2r.workspace -q sparkSettings.pool.defaultPool -i <inline_json_w_id_name_type> -f",
    ]
    set_learnmore = [
        "Tip: Run `set <path> -q check -i empty` to see updatable  properties (e.g. set ws1.Workspace -q check -i empty)"
    ]

    set_parser = subparsers.add_parser(
        "set",
        help=fab_constant.COMMAND_FS_SET_DESCRIPTION,
        fab_examples=set_examples,
        fab_learnmore=set_learnmore,
    )
    set_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    set_parser.add_argument(
        "-q",
        "--query",
        nargs="+",
        metavar="",
        required=True,
        help="JSON path to filter",
    )
    set_parser.add_argument(
        "-i", "--input", nargs="+", required=True, help="Input path for replace"
    )
    set_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    set_parser.usage = f"{utils_error_parser.get_usage_prog(set_parser)}"
    set_parser.set_defaults(func=fs.set_command)


# Command for 'clear'
def register_clear_parser(subparsers: _SubParsersAction) -> None:
    clear_parser = subparsers.add_parser(
        "clear", aliases=["cls"], help=fab_constant.COMMAND_FS_CLEAR_DESCRIPTION
    )
    clear_parser.usage = f"{utils_error_parser.get_usage_prog(clear_parser)}"
    clear_parser.set_defaults(func=do_clear)


def register_ln_parser(subparsers: _SubParsersAction) -> None:
    ln_aliases = ["mklink"]
    ln_examples = [
        "# create a shortcut in the /Files section",
        "$ ln Files/scut.Shortcut --type oneLake --target ../../_wsfabcli.Workspace/lakehouse.lakehouse/Files\n",
        "# create an external shortcut in the /Tables section",
        "$ ln Tables/ext_table.Shortcut --type adlsGen2 -i <inline_json_w_location_subpath_connectionid>",
    ]

    ln_parser = subparsers.add_parser(
        "ln",
        aliases=ln_aliases,
        help=fab_constant.COMMAND_FS_LN_DESCRIPTION,
        fab_examples=ln_examples,
        fab_aliases=ln_aliases,
        fab_learnmore=["_"],
    )
    ln_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    ln_parser.add_argument(
        "--type",
        required=True,
        metavar="",
        choices=[
            "adlsGen2",
            "amazonS3",
            "dataverse",
            "googleCloudStorage",
            "oneLake",
            "s3Compatible",
        ],
        help="Shortcut type (adlsGen2, amazonS3, dataverse, googleCloudStorage, oneLake, s3Compatible)",
    )
    ln_parser.add_argument(
        "--target",
        nargs="+",
        required=False,
        metavar="",
        type=str,
        help="OneLake target. Optional for internal (OneLake) shortcut",
    )
    ln_parser.add_argument(
        "-i", "--input", nargs="+", required=False, help="JSON path. Optional"
    )
    ln_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    ln_parser.usage = f"{utils_error_parser.get_usage_prog(ln_parser)}"
    ln_parser.set_defaults(func=fs.ln_command)


# Command for 'start'
def register_start_parser(subparsers: _SubParsersAction) -> None:
    start_examples = [
        "# start a capacity",
        "$ start .capacities/capac1.Capacity .\n",
        "# start mirroring",
        "$ start ws1.Workspace/mir1.MirroredDatabase -f",
    ]

    start_parser = subparsers.add_parser(
        "start",
        help=fab_constant.COMMAND_FS_START_DESCRIPTION,
        fab_examples=start_examples,
        fab_learnmore=["_"],
    )
    start_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    start_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    start_parser.usage = f"{utils_error_parser.get_usage_prog(start_parser)}"
    start_parser.set_defaults(func=fs.start_command)


# Command for 'stop'
def register_stop_parser(subparsers: _SubParsersAction) -> None:
    stop_examples = [
        "# stop a capacity",
        "$ stop .capacities/capac1.Capacity .\n",
        "# stop mirroring",
        "$ stop ws1.Workspace/mir1.MirroredDatabase -f",
    ]

    stop_parser = subparsers.add_parser(
        "stop",
        help=fab_constant.COMMAND_FS_STOP_DESCRIPTION,
        fab_examples=stop_examples,
        fab_learnmore=["_"],
    )
    stop_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    stop_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    stop_parser.usage = f"{utils_error_parser.get_usage_prog(stop_parser)}"
    stop_parser.set_defaults(func=fs.stop_command)


# Command for 'assign'
def register_assign_parser(subparsers: _SubParsersAction) -> None:
    assign_examples = [
        "# assign a capacity to a workspace",
        "$ assign .capacities/capac1.Capacity -W ws1.Workspace\n",
        "# assign a domain to a workspace",
        "$ assign .domains/domain1.Domain -W ws1.Workspace -f",
    ]

    assign_parser = subparsers.add_parser(
        "assign",
        help=fab_constant.COMMAND_FS_ASSIGN_DESCRIPTION,
        fab_examples=assign_examples,
        fab_learnmore=["_"],
    )
    assign_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    assign_parser.add_argument(
        "-W",
        "--workspace",
        nargs="+",
        required=True,
        help="Assign to target Workspace",
    )
    assign_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    assign_parser.usage = f"{utils_error_parser.get_usage_prog(assign_parser)}"
    assign_parser.set_defaults(func=fs.assign_command)


# Command for 'unassign'
def register_unassign_parser(subparsers: _SubParsersAction) -> None:
    unassign_examples = [
        "# unassign a capacity from a workspace",
        "$ unassign .capacities/capac1.Capacity -W ws1.Workspace\n",
        "# unassign a domain from a workspace",
        "$ unassign .domains/domain1.Domain -W ws1.Workspace -f",
    ]

    unassign_parser = subparsers.add_parser(
        "unassign",
        help=fab_constant.COMMAND_FS_UNASSIGN_DESCRIPTION,
        fab_examples=unassign_examples,
        fab_learnmore=["_"],
    )
    unassign_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    unassign_parser.add_argument(
        "-W",
        "--workspace",
        nargs="+",
        required=True,
        help="Unassign from target Workspace",
    )
    unassign_parser.add_argument(
        "-f", "--force", required=False, action="store_true", help="Force. Optional"
    )

    unassign_parser.usage = f"{utils_error_parser.get_usage_prog(unassign_parser)}"
    unassign_parser.set_defaults(func=fs.unassign_command)


# Command for 'clear'
def do_clear(args: Namespace) -> None:
    os.system("cls" if os.name == "nt" else "clear")
