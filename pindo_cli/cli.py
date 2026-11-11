"""
Pindo CLI entry point.

Commands are thin: they gather options, build a :class:`PindoClient` via
:func:`get_client`, call one method on it, and print the result with Rich.
API failures surface as a one-line ``Error: ...`` on stderr with exit code 1
(see :func:`handle_errors`); ``--debug`` adds request/response logging with
secrets redacted.
"""

from __future__ import annotations

import functools
import logging
import re
from collections.abc import Callable
from typing import Any, TypeVar

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from pindo_cli import config as cfg
from pindo_cli.client import PindoClient, PindoClientException, redact
from pindo_cli.reports import report

console = Console()
err_console = Console(stderr=True)

F = TypeVar('F', bound=Callable[..., Any])

_PHONE_RE = re.compile(r'^\+?[1-9]\d{7,14}$')  # E.164: up to 15 digits

# --------------------------------------------------------------- helpers


def get_client(
    ctx: click.Context, token: str | None = None, require_token: bool = True
) -> PindoClient:
    """Build a client from the resolved settings (flag > env > config file)."""
    obj = ctx.obj or {}
    settings = cfg.resolve(token=token, base_url=obj.get('base_url'))
    if require_token:
        settings.require_token()
    return PindoClient(base_url=settings.base_url, token=settings.token)


def handle_errors(func: F) -> F:
    """Turn client/config errors into a clean ``Error: ...`` and exit code 1."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except cfg.MissingTokenError as exc:
            raise click.ClickException(str(exc)) from None
        except PindoClientException as exc:
            ctx = click.get_current_context(silent=True)
            if ctx and (ctx.obj or {}).get('debug') and exc.payload is not None:
                err_console.print(Pretty(redact(exc.payload)))
            raise click.ClickException(str(exc)) from None
        except ValueError as exc:
            raise click.ClickException(str(exc)) from None

    return wrapper  # type: ignore[return-value]


token_option = click.option(
    '--token',
    '-t',
    default=None,
    metavar='TOKEN',
    help='API token. Defaults to $PINDO_TOKEN, then the token saved by `pindo login`.',
)
username_option = click.option(
    '--username', '-u', prompt=True, required=True, help='Your Pindo username.'
)
password_option = click.option(
    '--password', '-p', prompt=True, hide_input=True, required=True, help='Your Pindo password.'
)


def _auth_error_message(exc: PindoClientException) -> str:
    if exc.status_code in (401, 403):
        return 'Wrong username or password'
    return str(exc)


def _validate_phone(ctx: click.Context, param: click.Parameter, value: str) -> str:
    cleaned = re.sub(r'[\s\-().]', '', value or '')
    if not _PHONE_RE.match(cleaned):
        raise click.BadParameter(
            'use the international format with country code, e.g. +250781234567'
        )
    return cleaned if cleaned.startswith('+') else '+' + cleaned


def _validate_url(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if not re.fullmatch(r'https?://\S+', value or ''):
        raise click.BadParameter('must be an http(s) URL, e.g. https://example.com/dlr')
    return value


def _fetch_token(client: PindoClient, username: str, password: str, refresh: bool = False) -> str:
    with console.status('Requesting token...'):
        try:
            if refresh:
                return client.refresh_token(username, password)
            return client.get_token(username, password)
        except PindoClientException as exc:
            raise click.ClickException(_auth_error_message(exc)) from None


# ------------------------------------------------------------------ root


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Log every API request and response to stderr (secrets are redacted).',
)
@click.option(
    '--base-url',
    default=None,
    metavar='URL',
    help='API base URL (default: $PINDO_BASE_URL or https://api.pindo.io).',
)
@click.version_option(None, '--version', '-v', package_name='pindo-cli')
@click.pass_context
def cli(ctx: click.Context, debug: bool, base_url: str | None) -> None:
    """
    Pindo CLI

    Authenticate with the Pindo API, send test messages and pull reports
    from your account.

    Run `pindo login` once; afterwards every command picks the saved token
    up automatically. See `pindo report --help` for the reporting commands.

    https://www.pindo.io/
    """
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['base_url'] = base_url
    if debug:
        _enable_debug_logging()


def _enable_debug_logging() -> None:
    logger = logging.getLogger('pindo_cli')
    logger.setLevel(logging.DEBUG)
    if not any(isinstance(h, RichHandler) for h in logger.handlers):
        handler = RichHandler(console=err_console, show_path=False, show_time=False)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)


cli.add_command(report)


# ----------------------------------------------------- authentication


@cli.command()
@username_option
@password_option
@click.option(
    '--no-save',
    is_flag=True,
    default=False,
    help='Only print the token; do not write it to the config file.',
)
@click.pass_context
@handle_errors
def login(ctx: click.Context, username: str, password: str, no_save: bool) -> None:
    """
    Log in and save your API token for later commands.

    The token is written to ~/.pindo/config.toml (readable only by you).
    Set $PINDO_CONFIG to use a different file.
    """
    client = get_client(ctx, require_token=False)
    token = _fetch_token(client, username, password)
    if no_save:
        console.print(Panel(token, title='API Token', expand=False))
        return
    base_url = None if client.base_url == cfg.DEFAULT_BASE_URL else client.base_url
    path = cfg.update_config(token=token, username=username, base_url=base_url)
    console.print(
        f'[bold green]Logged in[/bold green] as [bold]{username}[/bold]. Token saved to {path}'
    )


@cli.command()
@handle_errors
def logout() -> None:
    """Remove the saved token and config file."""
    if cfg.clear_config():
        console.print(f'Logged out. Removed {cfg.config_path()}')
    else:
        console.print('No saved credentials found.')


@cli.command()
@username_option
@password_option
@click.pass_context
@handle_errors
def token(ctx: click.Context, username: str, password: str) -> None:
    """Request an API token (printed, not saved)."""
    value = _fetch_token(get_client(ctx, require_token=False), username, password)
    console.print(Panel(value, title='API Token', expand=False))


@cli.command()
@username_option
@password_option
@click.option('--save/--no-save', default=True, help='Also update the saved token (default: save).')
@click.pass_context
@handle_errors
def refresh_token(ctx: click.Context, username: str, password: str, save: bool) -> None:
    """Request a fresh API token (and update the saved one)."""
    client = get_client(ctx, require_token=False)
    value = _fetch_token(client, username, password, refresh=True)
    console.print(Panel(value, title='New API Token', expand=False), style='bold green')
    if save and cfg.config_path().exists():
        cfg.update_config(token=value, username=username)
        console.print('Saved token updated.')


@cli.command()
@username_option
@click.option('--email', '-e', prompt=True, required=True, help='Your email address.')
@click.option(
    '--password',
    '-p',
    prompt=True,
    required=True,
    hide_input=True,
    confirmation_prompt=True,
    help='Choose a password.',
)
@click.pass_context
@handle_errors
def register(ctx: click.Context, username: str, email: str, password: str) -> None:
    """Create a new Pindo account."""
    client = get_client(ctx, require_token=False)
    with console.status('Creating account...'):
        try:
            message = client.register(username, email, password)
        except PindoClientException as exc:
            if exc.status_code in (400, 409):
                raise click.ClickException(exc.message) from None
            raise
    console.print(message)


@click.command()
@click.option('--email', '-e', prompt=True, required=True, help='The email of your account.')
@click.pass_context
@handle_errors
def forgot_password(ctx: click.Context, email: str) -> None:
    """Email yourself a password-recovery token."""
    client = get_client(ctx, require_token=False)
    with console.status('Sending recovery email...'):
        try:
            client.forgot_password(email)
        except PindoClientException as exc:
            if exc.status_code in (400, 404):
                raise click.ClickException('The email provided does not exist.') from None
            raise
    console.print(
        'A recovery token has been sent to your email. Run '
        '[bold green]pindo recover-password[/bold green] to set a new password.'
    )


cli.add_command(forgot_password, 'forgot-password')
# Old, misspelled name kept working for existing scripts.
cli.add_command(
    click.Command(
        'forget-password',
        params=forgot_password.params,
        callback=forgot_password.callback,
        help=forgot_password.help,
        hidden=True,
    )
)


@cli.command()
@click.option(
    '--token',
    '-t',
    'recovery_token',
    prompt='Recovery token',
    required=True,
    help='The recovery token sent to your email.',
)
@click.option(
    '--password', prompt='New password', hide_input=True, required=True, help='Your new password.'
)
@click.option(
    '--confirm-password',
    '--confirm_password',
    'confirm_password',
    prompt='Confirm new password',
    hide_input=True,
    required=True,
    help='Repeat the new password.',
)
@click.pass_context
@handle_errors
def recover_password(
    ctx: click.Context, recovery_token: str, password: str, confirm_password: str
) -> None:
    """Set a new password with a recovery token."""
    if password != confirm_password:
        raise click.BadParameter('passwords do not match', param_hint="'--confirm-password'")
    client = get_client(ctx, require_token=False)
    with console.status('Updating password...'):
        message = client.recover_password(recovery_token, password, confirm_password)
    console.print(message)


# -------------------------------------------------------------- account


@cli.command()
@token_option
@click.option(
    '--to',
    prompt='Recipient phone number',
    required=True,
    callback=_validate_phone,
    help='Recipient phone number in international format, e.g. +250781234567.',
)
@click.option('--text', prompt=True, required=True, default='Hello Pindo', help='Message text.')
@click.option('--sender', prompt=True, required=True, default='Pindo', help='Sender ID.')
@click.pass_context
@handle_errors
def sms(ctx: click.Context, token: str | None, to: str, text: str, sender: str) -> None:
    """Send a test message."""
    client = get_client(ctx, token)
    with console.status(f'Sending SMS to {to}...'):
        result = client.send_sms(to, text, sender)
    console.print(Panel(Pretty(result, expand_all=True), title='SMS', expand=False))


@cli.command()
@token_option
@click.pass_context
@handle_errors
def balance(ctx: click.Context, token: str | None) -> None:
    """Show your account balance."""
    client = get_client(ctx, token)
    with console.status('Fetching balance...'):
        wallet = client.wallet()
    if isinstance(wallet, dict):
        amount, currency = wallet.get('amount'), wallet.get('currency', 'USD')
    else:
        amount, currency = wallet, 'USD'
    console.print(Panel(f'{currency} {amount}', title='Balance', expand=False))


@cli.command()
@token_option
@click.option('--name', prompt=True, required=True, help='Organization name.')
@click.option(
    '--webhook-url',
    '--webhook_url',
    'webhook_url',
    prompt='Webhook URL',
    required=True,
    callback=_validate_url,
    help='Where delivery reports are POSTed, e.g. https://example.com/dlr.',
)
@click.option(
    '--retries-count',
    '--retries_count',
    'retries_count',
    prompt='SMS retries count',
    type=click.IntRange(min=0),
    required=True,
    help='How many times a failed SMS is retried.',
)
@click.pass_context
@handle_errors
def org(
    ctx: click.Context, token: str | None, name: str, webhook_url: str, retries_count: int
) -> None:
    """Update your organization settings."""
    client = get_client(ctx, token)
    with console.status('Updating organization...'):
        result = client.update_organization(name, webhook_url, retries_count)
    console.print(Pretty(result, expand_all=True))


# ------------------------------------------------------------- config


@cli.group(name='config')
def config_group() -> None:
    """Show or inspect the CLI configuration."""


_TOKEN_SOURCES = {
    cfg.SOURCE_FLAG: '--token flag',
    cfg.SOURCE_ENV: f'${cfg.ENV_TOKEN} environment variable',
    cfg.SOURCE_FILE: 'config file',
    cfg.SOURCE_NONE: 'not set (run `pindo login`)',
}


@config_group.command('show')
@token_option
@click.pass_context
def config_show(ctx: click.Context, token: str | None) -> None:
    """Show the effective settings and where the token comes from."""
    settings = cfg.resolve(token=token, base_url=(ctx.obj or {}).get('base_url'))
    table = Table(title='Pindo CLI configuration', show_header=False, expand=False)
    table.add_column('Field', style='bold')
    table.add_column('Value')
    table.add_row('Config file', str(cfg.config_path()))
    table.add_row('Base URL', settings.base_url)
    table.add_row('Username', settings.username or '(unknown)')
    table.add_row('Token', settings.masked_token)
    table.add_row('Token source', _TOKEN_SOURCES[settings.token_source])
    console.print(table)


@config_group.command('path')
def config_path_cmd() -> None:
    """Print the config file path."""
    click.echo(str(cfg.config_path()))
