import click
import click_spinner
from rich import print
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.pretty import Pretty

from pindo_cli.http import Token, RefreshToken, Register, SMS, Balance, Organization, ForgetPassword, RecoverPassword


console = Console()

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.version_option(None, "--version", "-v")
def cli(debug):
    """
    Pindo CLI

    A simple Command Line Interface that allows you to authenticate with 
    the Pindo API
    
    https://www.pindo.io/
    """


@cli.command()  # @cli, not @click!
@click.option(
    '--username', '-u', prompt=True, required=True, help='Please enter your username')
@click.option(
    '--password', '-p',
    prompt=True, hide_input=True, required=True, help='Please enter your password')
def token(username, password):
    """
    Request a token for using Pindo API.
    """
    with console.status(""):
        try:
            token = Panel(str(Token(username, password)), title="API Token", expand=False)
            console.print(token)
        except KeyError:
            console.print("Wrong username or password")


@cli.command()  # @cli, not @click!
@click.option(
    '--username', '-u', prompt=True, required=True, help='Please enter your username')
@click.option(
    '--password', '-p',
    prompt=True, hide_input=True, required=True, help='Please enter your password')
def refresh_token(username, password):
    """
    Refresh a Token.
    """
    with console.status(""):
        token = Panel(str(RefreshToken(username, password)), title="New API Token", expand=False)
        console.print(token, style="bold green")


@cli.command()
@click.option(
    '--username', '-u', prompt=True, required=True, help='Please enter your username')
@click.option(
    '--email', '-e', prompt=True, required=True, help='Please enter your email')
@click.option(
    '--password', '-p', prompt=True, required=True, hide_input=True, confirmation_prompt=True,
    help='Please enter your password')
def register(username, email, password):
    """
    Create a new Pindo account.
    """
    with console.status(""):
        console.print(str(Register(username, email, password)))


@cli.command()
@click.option('--email', '-e', prompt=True, required=True, help='Please enter your email')
@click.pass_context
def forget_password(ctx, email):
    """
    Forget Password
    """
    with console.status(""):
        resp = ForgetPassword(email).resp()
        if resp.status_code == 200:
            print('A recover token has been sent to your email. Run the command [bold green]pindo recover-password[/bold green] to recover your password account.')
            syntax = Syntax('run: pindo recover-password', "bash", theme="monokai", line_numbers=False)
            panel = Panel(syntax, title="Command", expand=False)
            console.print(panel)
        else:
            panel = Panel('The email provided does not exist.', title="Wrong email", expand=False)
            console.print(panel)


@cli.command(hidden=True)
@click.option('--token', '-t', prompt=True, required=True, help='Enter the recover token sent to your email.')
@click.option('--password', prompt=True, hide_input=True, required=True, help='Enter your new password')
@click.option('--confirm_password', prompt=True, hide_input=True, required=True, help='Confirm your password')
def recover_password(token, password, confirm_password):
    """
    Recover Password
    """
    with console.status(""):
        console.print(str(RecoverPassword(token, password, confirm_password)))


@cli.command()
@click.option('--token', prompt=True, required=True, help='API Token')
@click.option(
    '--to', prompt=True, required=True, help='Receiver phone number (+250xxxxxx)',
    default='+250785383100')
@click.option(
    '--text', prompt=True, required=True, help='Message to send', default='Hello Pindo')
@click.option('--sender', prompt=True, required=True, default='Pindo', help='Sender name')
def sms(token, to, text, sender):
    """
    Send a test message
    """
    with console.status(""):
        sms = SMS(token, to, text, sender).send()
        pretty = Pretty(sms, expand_all=True)
        console.print(Panel(pretty, title="SMS", expand=False))


@cli.command()
@click.option('--token', prompt=True, required=True, help='API Token')
def balance(token): 
    """
    Get account balance
    """
    with console.status(""):
        balance = "USD " + str(Balance(token))
        panel =Panel(balance, title="Balance", expand=False)
        console.print(panel)


@cli.command()
@click.option('--token', prompt=True, required=True, help='API Token')
@click.option('--name', prompt=True, required=True, help='Organization name')
@click.option('--webhook_url', prompt=True, required=True, help='Webhook URL. Eg (https://pindo.io/dlr)')
@click.option('--retries_count', prompt=True, type=(int), required=True, help='SMS retries count settings')
def org(token, name, webhook_url, retries_count):
    """
    Update Organization Settings
    """
    console.print(str(Organization(token, name, webhook_url, retries_count)))
