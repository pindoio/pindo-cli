import click
import click_spinner

from pindo_cli.http import Token, RefreshToken, Register, SMS, Balance, Organization


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.version_option(None, "--version", "-v")
def cli(debug):
    """
    Pindo CLI

    A simple Command Line Interface that allow you to create an account
    and request a token for using Pindo API
    """


@cli.command()  # @cli, not @click!
@click.option(
    '--username', '-u', prompt=True, help='Please enter your username')
@click.option(
    '--password', '-p',
    prompt=True, hide_input=True, help='Please enter your password')
def token(username, password):
    """
    Request a token for using Pindo API.
    """
    click.echo('token...')
    with click_spinner.spinner():
        click.echo(Token(username, password))


@cli.command()  # @cli, not @click!
@click.option(
    '--username', '-u', prompt=True, help='Please enter your username')
@click.option(
    '--password', '-p',
    prompt=True, hide_input=True, help='Please enter your password')
def refresh_token(username, password):
    """
    Refresh a Token.
    """
    click.echo('token...')
    with click_spinner.spinner():
        click.echo(RefreshToken(username, password))


@cli.command()
@click.option(
    '--username', '-u', prompt=True, help='Please enter your username')
@click.option(
    '--email', '-e', prompt=True, help='Please enter your email')
@click.option(
    '--password', '-p', prompt=True, hide_input=True, confirmation_prompt=True,
    help='Please enter your password')
def register(username, email, password):
    """
    Create a new Pindo account.
    """
    click.echo(Register(username, email, password))


@cli.command()
@click.option('--token', prompt=True, help='API Token')
@click.option(
    '--to', prompt=True, help='Receiver phone number (+250xxxxxx)',
    default='+250785383100')
@click.option(
    '--text', prompt=True, help='Message to send', default='Hello Pindo')
@click.option('--sender', prompt=True, default='Pindo', help='Sender name')
def sms(token, to, text, sender):
    """
    Send a test message
    """
    click.echo(SMS(token, to, text, sender))


@cli.command()
@click.option('--token', prompt=True, help='API Token')
def balance(token):
    """
    Get account balance
    """
    click.echo(Balance(token))


@cli.command()
@click.option('--token', prompt=True, help='API Token')
@click.option('--name', prompt=True, help='Organization name')
@click.option('--webhook_url', prompt=True, help='Webhook URL. Eg (https://pindo.io/dlr)')
@click.option('--retries_count', prompt=True, type=(int), help='SMS retries count settings')
def org(token, name, webhook_url, retries_count):
    """
    Organization
    """
    click.echo(Organization(token, name, webhook_url, retries_count))
