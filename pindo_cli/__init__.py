import click
import click_spinner
import time

from http import Token, Register


@click.command()
@click.option(
    '--name', default='world',
    prompt='greet whom?',
    help='who should i greet?'
)
def main(name):
    click.echo('Hello {}!'.format(name))


@click.group()
def cli():
    """
    Pindo CLI

    A simple Command Line Interface that allow you to create an account
    and request a token for using Pindo API 
    """
    pass

@cli.command()  # @cli, not @click!
@click.option('--username', '-u', prompt=True, help='Please enter your username')
@click.option('--password', '-p', prompt=True, hide_input=True, help='Please enter your password')
def token(username, password):
    """
    Request a token for using Pindo API.
    """
    click.echo('token...')
    with click_spinner.spinner():
        click.echo(Token(username, password))
        

@cli.command()
@click.option('--username', '-u', prompt=True, help='Please enter your username')
@click.option('--email', '-e', prompt=True, help='Please enter your email')
@click.option('--password', '-p', prompt=True, hide_input=True, confirmation_prompt=True,
              help='Please enter your password')
def register(username, email, password):
    """
    Create a new Pindo account.
    """
    click.echo(Register(username, email, password))
    # 
