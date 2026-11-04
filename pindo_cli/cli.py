"""
Pindo CLI entry point.

Commands are thin: they gather options, build a :class:`PindoClient` via
:func:`get_client`, call one method on it, and print the result with Rich.
API failures surface as a one-line ``Error: ...`` on stderr with exit code 1
(see :func:`handle_errors`); ``--debug`` adds request/response logging.
"""
import functools
import logging

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from pindo_cli import config as cfg
from pindo_cli.client import PindoClient, PindoClientException
from pindo_cli.reports import report

console = Console()
err_console = Console(stderr=True)


# --------------------------------------------------------------- helpers

def get_client(ctx, token=None, require_token=True):
    """Build a client from the resolved settings (flag > env > config file)."""
    obj = ctx.obj or {}
    settings = cfg.resolve(token=token, base_url=obj.get('base_url'))
    if require_token:
        settings.require_token()
    return PindoClient(base_url=settings.base_url, token=settings.token)


def handle_errors(func):
    """Turn client/config errors into a clean ``Error: ...`` and exit code 1."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except cfg.MissingTokenError as exc:
            raise click.ClickException(str(exc))
        except PindoClientException as exc:
            ctx = click.get_current_context(silent=True)
            if ctx and (ctx.obj or {}).get('debug') and exc.payload is not None:
                err_console.print(Pretty(exc.payload))
            raise click.ClickException(str(exc))
        except ValueError as exc:
            raise click.ClickException(str(exc))
    return wrapper


token_option = click.option(
    '--token', '-t', default=None, metavar='TOKEN',
    help='API token. Defaults to $PINDO_TOKEN, then the token saved by `pindo login`.')


def _auth_error_message(exc):
    if exc.status_code in (401, 403):
        return 'Wrong username or password'
    return str(exc)


# ------------------------------------------------------------------ root

@click.group()
@click.option('--debug/--no-debug', default=False,
              help='Log every API request and response to stderr.')
@click.option('--base-url', default=None, metavar='URL',
              help='API base URL (default: $PINDO_BASE_URL or https://api.pindo.io).')
@click.version_option(None, '--version', '-v')
@click.pass_context
def cli(ctx, debug, base_url):
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


def _enable_debug_logging():
    logger = logging.getLogger('pindo_cli')
    logger.setLevel(logging.DEBUG)
    if not any(isinstance(h, RichHandler) for h in logger.handlers):
        handler = RichHandler(console=err_console, show_path=False, show_time=False)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)


cli.add_command(report)


# ----------------------------------------------------- authentication

@cli.command()
@click.option('--username', '-u', prompt=True, required=True, help='Your Pindo username')
@click.option('--password', '-p', prompt=True, hide_input=True, required=True,
              help='Your Pindo password')
@click.option('--no-save', is_flag=True, default=False,
              help='Only print the token; do not write it to the config file.')
@click.pass_context
@handle_errors
def login(ctx, username, password, no_save):
    """
    Log in and save your API token for later commands.

    The token is written to ~/.pindo/config.toml (readable only by you).
    Set $PINDO_CONFIG to use a different file.
    """
    client = get_client(ctx, require_token=False)
    with console.status('Requesting token...'):
        try:
            token = client.get_token(username, password)
        except PindoClientException as exc:
            raise click.ClickException(_auth_error_message(exc))
    if no_save:
        console.print(Panel(token, title='API Token', expand=False))
        return
    path = cfg.update_config(token=token, username=username,
                             base_url=None if client.base_url == cfg.DEFAULT_BASE_URL
                             else client.base_url)
    console.print('[bold green]Logged in[/bold green] as [bold]{}[/bold]. '
                  'Token saved to {}'.format(username, path))


@cli.command()
@handle_errors
def logout():
    """Remove the saved token and config file."""
    if cfg.clear_config():
        console.print('Logged out. Removed {}'.format(cfg.config_path()))
    else:
        console.print('No saved credentials found.')


@cli.command()
@click.option('--username', '-u', prompt=True, required=True, help='Your Pindo username')
@click.option('--password', '-p', prompt=True, hide_input=True, required=True,
              help='Your Pindo password')
@click.pass_context
@handle_errors
def token(ctx, username, password):
    """
    Request a token for using Pindo API (printed, not saved).
    """
    client = get_client(ctx, require_token=False)
    with console.status(''):
        try:
            value = client.get_token(username, password)
        except PindoClientException as exc:
            raise click.ClickException(_auth_error_message(exc))
    console.print(Panel(value, title='API Token', expand=False))


@cli.command()
@click.option('--username', '-u', prompt=True, required=True, help='Your Pindo username')
@click.option('--password', '-p', prompt=True, hide_input=True, required=True,
              help='Your Pindo password')
@click.option('--save/--no-save', default=True,
              help='Also update the saved token (default: save).')
@click.pass_context
@handle_errors
def refresh_token(ctx, username, password, save):
    """
    Refresh a Token.
    """
    client = get_client(ctx, require_token=False)
    with console.status(''):
        try:
            value = client.refresh_token(username, password)
        except PindoClientException as exc:
            raise click.ClickException(_auth_error_message(exc))
    console.print(Panel(value, title='New API Token', expand=False), style='bold green')
    if save and cfg.config_path().exists():
        cfg.update_config(token=value, username=username)
        console.print('Saved token updated.')


@cli.command()
@click.option('--username', '-u', prompt=True, required=True, help='Please enter your username')
@click.option('--email', '-e', prompt=True, required=True, help='Please enter your email')
@click.option('--password', '-p', prompt=True, required=True, hide_input=True,
              confirmation_prompt=True, help='Please enter your password')
@click.pass_context
@handle_errors
def register(ctx, username, email, password):
    """
    Create a new Pindo account.
    """
    client = get_client(ctx, require_token=False)
    with console.status(''):
        try:
            message = client.register(username, email, password)
        except PindoClientException as exc:
            if exc.status_code in (400, 409):
                console.print(exc.message)
                return
            raise
    console.print(message)


@cli.command()
@click.option('--email', '-e', prompt=True, required=True, help='Please enter your email')
@click.pass_context
@handle_errors
def forget_password(ctx, email):
    """
    Request a password-recovery token by email.
    """
    client = get_client(ctx, require_token=False)
    with console.status(''):
        try:
            client.forgot_password(email)
        except PindoClientException as exc:
            if exc.status_code in (400, 404):
                console.print(Panel('The email provided does not exist.',
                                    title='Wrong email', expand=False))
                return
            raise
    console.print('A recover token has been sent to your email. Run '
                  '[bold green]pindo recover-password[/bold green] to set a new password.')


@cli.command(hidden=True)
@click.option('--token', '-t', prompt=True, required=True,
              help='Enter the recover token sent to your email.')
@click.option('--password', prompt=True, hide_input=True, required=True,
              help='Enter your new password')
@click.option('--confirm_password', prompt=True, hide_input=True, required=True,
              help='Confirm your password')
@click.pass_context
@handle_errors
def recover_password(ctx, token, password, confirm_password):
    """
    Recover Password
    """
    client = get_client(ctx, require_token=False)
    with console.status(''):
        console.print(client.recover_password(token, password, confirm_password))


# -------------------------------------------------------------- account

@cli.command()
@token_option
@click.option('--to', prompt=True, required=True, help='Receiver phone number (+250xxxxxx)',
              default='+250785383100')
@click.option('--text', prompt=True, required=True, help='Message to send',
              default='Hello Pindo')
@click.option('--sender', prompt=True, required=True, default='Pindo', help='Sender name')
@click.pass_context
@handle_errors
def sms(ctx, token, to, text, sender):
    """
    Send a test message
    """
    client = get_client(ctx, token)
    with console.status(''):
        result = client.send_sms(to, text, sender)
    console.print(Panel(Pretty(result, expand_all=True), title='SMS', expand=False))


@cli.command()
@token_option
@click.pass_context
@handle_errors
def balance(ctx, token):
    """
    Get account balance
    """
    client = get_client(ctx, token)
    with console.status(''):
        wallet = client.wallet()
    amount = wallet.get('amount') if isinstance(wallet, dict) else wallet
    currency = wallet.get('currency', 'USD') if isinstance(wallet, dict) else 'USD'
    console.print(Panel('{} {}'.format(currency, amount), title='Balance', expand=False))


@cli.command()
@token_option
@click.option('--name', prompt=True, required=True, help='Organization name')
@click.option('--webhook_url', prompt=True, required=True,
              help='Webhook URL. Eg (https://pindo.io/dlr)')
@click.option('--retries_count', prompt=True, type=int, required=True,
              help='SMS retries count settings')
@click.pass_context
@handle_errors
def org(ctx, token, name, webhook_url, retries_count):
    """
    Update Organization Settings
    """
    client = get_client(ctx, token)
    with console.status(''):
        result = client.update_organization(name, webhook_url, retries_count)
    console.print(Pretty(result, expand_all=True))


# ------------------------------------------------------------- config

@cli.group(name='config')
def config_group():
    """Show or inspect the CLI configuration."""


@config_group.command('show')
@token_option
@click.pass_context
def config_show(ctx, token):
    """Show the effective settings and where the token comes from."""
    settings = cfg.resolve(token=token, base_url=(ctx.obj or {}).get('base_url'))
    table = Table(title='Pindo CLI configuration', show_header=False, expand=False)
    table.add_column('Field', style='bold')
    table.add_column('Value')
    table.add_row('Config file', str(cfg.config_path()))
    table.add_row('Base URL', settings.base_url)
    table.add_row('Username', settings.username or '(unknown)')
    table.add_row('Token', settings.masked_token)
    table.add_row('Token source', {
        cfg.SOURCE_FLAG: '--token flag',
        cfg.SOURCE_ENV: '${} environment variable'.format(cfg.ENV_TOKEN),
        cfg.SOURCE_FILE: 'config file',
        cfg.SOURCE_NONE: 'not set (run `pindo login`)',
    }[settings.token_source])
    console.print(table)


@config_group.command('path')
def config_path_cmd():
    """Print the config file path."""
    click.echo(str(cfg.config_path()))
