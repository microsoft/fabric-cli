# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace
import os
from typing import Any, Optional

from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.errors import ErrorMessages
from fabric_cli.utils import fab_mem_store as utils_mem_store
from fabric_cli.utils import fab_ui, fab_version_check

AUTH_ENV_VARS = [
    "FAB_TOKEN",
    "FAB_TOKEN_ONELAKE",
    "FAB_TOKEN_AZURE",
    "FAB_SPN_CLIENT_ID",
    "FAB_SPN_CLIENT_SECRET",
    "FAB_SPN_CERT_PATH",
    "FAB_SPN_FEDERATED_TOKEN",
    "FAB_MANAGED_IDENTITY",
]


def init(args: Namespace) -> Any:
    auth_options = [
        "Interactive with a web browser",
        "Service principal authentication with secret",
        "Service principal authentication with certificate",
        "Service principal authentication with federated credential",
        "Managed identity authentication",
    ]

    utils_mem_store.clear_caches()

    # Clean up stale context files when logging in
    Context().cleanup_context_files(cleanup_all_stale=True, cleanup_current=False)

    if args.identity:
        FabAuth().set_access_mode("managed_identity")
        FabAuth().set_managed_identity(args.username)
        FabAuth().get_access_token(scope=fab_constant.SCOPE_FABRIC_DEFAULT)
        FabAuth().get_access_token(scope=fab_constant.SCOPE_ONELAKE_DEFAULT)
        FabAuth().get_access_token(scope=fab_constant.SCOPE_AZURE_DEFAULT)
        Context().context = FabAuth().get_tenant()

    elif any([args.username, args.password]):
        if not (
            all([args.username, args.tenant])
            and any([args.password, args.certificate, args.federated_token])
        ):
            raise FabricCLIError(
                "-u/--username and -t/--tenant all must be provided. -p/--password or --certificate must be provided.",
                fab_constant.ERROR_INVALID_INPUT,
            )
        else:
            FabAuth().set_access_mode("service_principal", args.tenant)
            if args.certificate:
                FabAuth().set_spn(
                    args.username, cert_path=args.certificate, password=args.password
                )
            elif args.password:
                FabAuth().set_spn(args.username, password=args.password)
            elif args.federated_token:
                FabAuth().set_spn(args.username, client_assertion=args.federated_token)
            FabAuth().get_access_token(scope=fab_constant.SCOPE_FABRIC_DEFAULT)
            FabAuth().get_access_token(scope=fab_constant.SCOPE_ONELAKE_DEFAULT)
            FabAuth().get_access_token(scope=fab_constant.SCOPE_AZURE_DEFAULT)
            Context().context = FabAuth().get_tenant()
    else:
        selected_auth = fab_ui.prompt_select_item(
            "How would you like to authenticate Fabric CLI?", auth_options
        )
        # When user cancels the prompt, selected_auth will be None
        if selected_auth is None:
            return False

        try:
            if selected_auth == "Interactive with a web browser":
                FabAuth().prepare_user_login(args.tenant)
                FabAuth().get_access_token(
                    scope=fab_constant.SCOPE_FABRIC_DEFAULT,
                    force_interactive=True,
                )
                FabAuth().get_access_token(scope=fab_constant.SCOPE_ONELAKE_DEFAULT)
                FabAuth().get_access_token(scope=fab_constant.SCOPE_AZURE_DEFAULT)
                Context().context = FabAuth().get_tenant()
            elif selected_auth.startswith("Service principal authentication"):
                fab_logger.log_warning(
                    "Ensure tenant setting is enabled for Service Principal auth"
                )

                tenant_id = fab_ui.prompt_ask("Enter tenant ID:")
                if tenant_id is None:  # User pressed CTRL+C
                    return

                if tenant_id.strip() == "":
                    fab_ui.print_output_error(
                        FabricCLIError(
                            ErrorMessages.Auth.spn_auth_missing_tenant_id(),
                            fab_constant.ERROR_SPN_AUTH_MISSING,
                        ),
                        command=args.command,
                        output_format_type=args.output_format,
                    )
                    return

                client_id = fab_ui.prompt_ask("Enter client ID:")
                if client_id is None:  # User pressed CTRL+C
                    return

                if client_id.strip() == "":
                    fab_ui.print_output_error(
                        FabricCLIError(
                            ErrorMessages.Auth.spn_auth_missing_client_id(),
                            fab_constant.ERROR_SPN_AUTH_MISSING,
                        ),
                        command=args.command,
                        output_format_type=args.output_format,
                    )
                    return

                if selected_auth == "Service principal authentication with certificate":
                    cert_path = fab_ui.prompt_ask(
                        "Enter certificate path (PEM, PKCS12 formats):"
                    )
                    if cert_path is None:  # User pressed CTRL+C
                        return

                    if cert_path.strip() == "":
                        fab_ui.print_output_error(
                            FabricCLIError(
                                ErrorMessages.Auth.spn_auth_missing_cert_path(),
                                fab_constant.ERROR_SPN_AUTH_MISSING,
                            ),
                            command=args.command,
                            output_format_type=args.output_format,
                        )
                        return
                    cert_password = fab_ui.prompt_password(
                        "Enter certificate password (optional):"
                    )
                elif selected_auth == "Service principal authentication with secret":
                    cert_path = None
                    client_secret = fab_ui.prompt_password("Enter client secret:")
                    if client_secret is None:  # User pressed CTRL+C
                        return

                    if client_secret.strip() == "":
                        fab_ui.print_output_error(
                            FabricCLIError(
                                ErrorMessages.Auth.spn_auth_missing_client_secret(),
                                fab_constant.ERROR_SPN_AUTH_MISSING,
                            ),
                            command=args.command,
                            output_format_type=args.output_format,
                        )
                        return
                elif (
                    selected_auth
                    == "Service principal authentication with federated credential"
                ):
                    cert_path = None
                    client_secret = None
                    federated_token = fab_ui.prompt_password("Enter federated token:")
                    if federated_token is None:  # User pressed CTRL+C
                        return

                    if federated_token.strip() == "":
                        fab_ui.print_output_error(
                            FabricCLIError(
                                ErrorMessages.Auth.spn_auth_missing_federated_token(),
                                fab_constant.ERROR_SPN_AUTH_MISSING,
                            ),
                            command=args.command,
                            output_format_type=args.output_format,
                        )
                        return

                FabAuth().set_access_mode("service_principal", tenant_id)
                if cert_path:
                    FabAuth().set_spn(
                        client_id, cert_path=cert_path, password=cert_password
                    )
                elif client_secret:
                    FabAuth().set_spn(client_id, password=client_secret)
                elif federated_token:
                    FabAuth().set_spn(client_id, client_assertion=federated_token)
                FabAuth().get_access_token(scope=fab_constant.SCOPE_FABRIC_DEFAULT)
                FabAuth().get_access_token(scope=fab_constant.SCOPE_ONELAKE_DEFAULT)
                FabAuth().get_access_token(scope=fab_constant.SCOPE_AZURE_DEFAULT)
                Context().context = FabAuth().get_tenant()
            elif selected_auth == "Managed identity authentication":
                fab_logger.log_warning(
                    "Ensure tenant setting is enabled for Service Principal auth"
                )
                client_id = fab_ui.prompt_ask(
                    "Enter client ID (only for User Assigned):"
                )

                if client_id is None:  # User pressed CTRL+C
                    return

                FabAuth().set_access_mode("managed_identity")
                FabAuth().set_managed_identity(client_id)
                FabAuth().get_access_token(scope=fab_constant.SCOPE_FABRIC_DEFAULT)
                FabAuth().get_access_token(scope=fab_constant.SCOPE_ONELAKE_DEFAULT)
                FabAuth().get_access_token(scope=fab_constant.SCOPE_AZURE_DEFAULT)
                Context().context = FabAuth().get_tenant()

        except KeyboardInterrupt:
            # User cancelled the authentication process
            return False

    fab_version_check.check_and_notify_update()

    return True


def logout(args: Namespace) -> None:
    auth = FabAuth()

    if getattr(args, "all", False):
        auth.logout()

        # Clear cache and context including current and stale context files
        utils_mem_store.clear_caches()
        Context().reset_context()

        fab_ui.print_output_format(args, message="Logged out of Fabric account")
        return

    if auth.get_identity_type() == "user":
        sessions = auth.get_user_sessions()
        if sessions:
            session = _resolve_user_session(
                auth,
                username=getattr(args, "username", None),
                tenant_id=getattr(args, "tenant", None),
                action="log out",
            )
            next_session = auth.remove_user_session(session["session_id"])

            utils_mem_store.clear_caches()
            if next_session is None:
                Context().reset_context()
                fab_ui.print_output_format(
                    args,
                    message=f"Logged out of {session['account_name']}",
                )
            else:
                Context().context = auth.get_tenant()
                fab_ui.print_output_format(
                    args,
                    message=(
                        f"Logged out of {session['account_name']} and switched to "
                        f"{next_session['account_name']}"
                    ),
                )
            return

    FabAuth().logout()

    # Clear cache and context including current and stale context files
    utils_mem_store.clear_caches()
    Context().reset_context()

    fab_ui.print_output_format(args, message="Logged out of Fabric account")


def status(args: Namespace) -> None:
    auth = FabAuth()
    tenant_id = auth.get_tenant_id()

    def __get_token_info(scope):
        try:
            token = auth.get_access_token(scope, interactive_renew=False)
        except FabricCLIError as e:
            if e.status_code in [
                fab_constant.ERROR_UNAUTHORIZED,
                fab_constant.ERROR_AUTHENTICATION_FAILED,
            ]:
                return {}
            else:
                raise e
        if isinstance(token, str):
            token = token.encode()  # Ensure bytes type
        return _get_token_info_from_bearer_token(token) if token else {}

    token_info = __get_token_info(fab_constant.SCOPE_FABRIC_DEFAULT)

    upn = token_info.get("upn") or "N/A"
    oid = token_info.get("oid") or "N/A"
    tid = token_info.get("tid", tenant_id) or "N/A"
    appid = token_info.get("appid") or "N/A"

    def __mask_token(scope):
        try:
            token = auth.get_access_token(scope, interactive_renew=False)
        except FabricCLIError as e:
            if e.status_code in [
                fab_constant.ERROR_UNAUTHORIZED,
                fab_constant.ERROR_AUTHENTICATION_FAILED,
            ]:
                return "N/A"
            else:
                raise e
        if isinstance(token, str):
            token = token.encode()  # Ensure bytes type
        return (
            token[:4].decode() + "************************************"
            if token
            else "N/A"
        )

    fabric_secret = __mask_token(fab_constant.SCOPE_FABRIC_DEFAULT)
    storage_secret = __mask_token(fab_constant.SCOPE_ONELAKE_DEFAULT)
    azure_secret = __mask_token(fab_constant.SCOPE_AZURE_DEFAULT)

    # Check login status
    is_logged_in = fabric_secret != "N/A"
    login_status = (
        "✓ Logged in to app.fabric.microsoft.com"
        if is_logged_in
        else "✗ Not logged in to app.fabric.microsoft.com"
    )
    fab_ui.print_grey(login_status)

    auth_data = {
        "logged_in": is_logged_in,
        "account": upn,
        "principal_id": oid,
        "tenant_id": tid,
        "app_id": appid,
        "token_fabric_powerbi": fabric_secret,
        "token_storage": storage_secret,
        "token_azure": azure_secret,
    }
    fab_ui.print_output_format(args, data=auth_data, show_key_value_list=True)


def list_accounts(args: Namespace) -> None:
    auth = FabAuth()
    sessions = auth.get_user_sessions()

    if not sessions:
        fab_ui.print_output_format(
            args,
            message=ErrorMessages.Auth.no_user_sessions_found(),
        )
        return

    active_session = auth.get_active_user_session()
    active_session_id = active_session.get("session_id") if active_session else None

    rows = []
    for session in sessions:
        rows.append(
            {
                "active": str(session.get("session_id") == active_session_id).lower(),
                "account": session.get("account_name", "Unknown"),
                "tenant_id": session.get("tenant_id", "Unknown"),
                "valid": str(auth.is_user_session_valid(session)).lower(),
                "last_used_at": session.get("last_used_at", ""),
            }
        )

    fab_ui.print_output_format(args, data=rows, show_headers=True)


def switch(args: Namespace) -> None:
    if _is_environment_auth_active():
        raise FabricCLIError(
            ErrorMessages.Auth.environment_auth_switch_not_supported(),
            fab_constant.ERROR_INVALID_OPERATION,
        )

    auth = FabAuth()
    session = _resolve_user_session(
        auth,
        username=getattr(args, "username", None),
        tenant_id=getattr(args, "tenant", None),
        action="switch to",
        require_valid=True,
    )
    current_session = auth.get_active_user_session()

    auth.activate_user_session(session["session_id"])
    utils_mem_store.clear_caches()
    Context().context = auth.get_tenant()

    if current_session and current_session.get("session_id") == session.get(
        "session_id"
    ):
        message = (
            f"Already using {session['account_name']} in tenant {session['tenant_id']}"
        )
    else:
        message = (
            f"Switched to {session['account_name']} in tenant {session['tenant_id']}"
        )

    fab_ui.print_output_format(args, message=message)


def _is_environment_auth_active() -> bool:
    return any(os.environ.get(var) for var in AUTH_ENV_VARS)


def _resolve_user_session(
    auth: FabAuth,
    username: Optional[str],
    tenant_id: Optional[str],
    action: str,
    require_valid: bool = False,
) -> dict[str, Any]:
    sessions = auth.get_user_sessions()
    if not sessions:
        raise FabricCLIError(
            ErrorMessages.Auth.no_user_sessions_found(),
            fab_constant.ERROR_NOT_FOUND,
        )

    active_session = auth.get_active_user_session()
    active_session_id = active_session.get("session_id") if active_session else None

    candidates = []
    for session in sessions:
        if username and session.get("account_name") != username:
            continue
        if tenant_id and session.get("tenant_id") != tenant_id:
            continue
        if require_valid and not auth.is_user_session_valid(session):
            continue
        candidates.append(session)

    if not candidates:
        if require_valid:
            error_message = (
                "No valid stored user sessions matched the requested selection"
            )
        else:
            error_message = ErrorMessages.Auth.no_user_sessions_found()
        raise FabricCLIError(error_message, fab_constant.ERROR_NOT_FOUND)

    if len(candidates) == 1:
        return candidates[0]

    if not username and not tenant_id and len(candidates) == 2:
        for session in candidates:
            if session.get("session_id") != active_session_id:
                return session

    prompt_map = {}
    for session in candidates:
        label = f"{session.get('account_name', 'Unknown')} ({session.get('tenant_id', 'Unknown')})"
        if session.get("session_id") == active_session_id:
            label += " [active]"
        prompt_map[label] = session

    selected_label = fab_ui.prompt_select_item(
        f"Which account would you like to {action}?",
        list(prompt_map.keys()),
    )
    if selected_label is None:
        raise FabricCLIError(
            "Operation cancelled",
            fab_constant.ERROR_OPERATION_CANCELLED,
        )

    return prompt_map[selected_label]


# Utils
def _get_token_info_from_bearer_token(bearer_token: str) -> Optional[dict[str, str]]:
    return FabAuth()._get_claims_from_token(
        bearer_token, ["upn", "oid", "tid", "appid"]
    )
