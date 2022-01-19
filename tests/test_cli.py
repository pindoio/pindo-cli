import pytest
from click.testing import CliRunner
from pkg_resources import get_distribution

import pindo_cli.cli as pindo


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_pindo_cli(runner):
    result = runner.invoke(pindo.cli, ['--help'])
    assert result.exit_code == 0
    assert 'Pindo CLI' in result.output


def test_command_token(runner):
    result = runner.invoke(pindo.token, ['-u', 'dgd', '-p', 'oUhdo'])
    assert result.exit_code == 0
    assert result.output is 'Wrong username or password'


def test_command_refresh_token(runner):
    result = runner.invoke(pindo.refresh_token, ['-u', 'abc', '-p', 'cbd'])
    assert result.exit_code == 1
    assert result.output is ''


def test_command_register(runner):
    result = runner.invoke(
        pindo.register,
        ['-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 0
    assert 'username already exists in the database' in result.output


def test_command_sms(runner):
    result = runner.invoke(
        pindo.sms, [
            '--token', 'oeiroeoeioeoiroe',
            '--to', '+250785383100',
            '--text', 'Hello Pindo',
            '--sender', 'Pindo'
        ])
    assert result.exit_code == 0
    assert 'message' in result.output


def test_command_balance(runner):
    result = runner.invoke(
        pindo.balance, [
            '--token', 'oeiroeoeioeoiroe',
        ])
    assert result.exit_code == 1
    assert result.output is ''


def test_pindo_cli_version_flag(runner):
    result = runner.invoke(pindo.cli, ['--version', "-v"])
    assert result.exit_code == 0
    assert get_distribution('pindo-cli').version in result.output


def test_command_org(runner):
    result = runner.invoke(
        pindo.org, [
            '--token', 'oeiroeoeioeoiroe',
            '--name', 'Pindo',
            '--webhook_url', 'https://pindo.io/webhook',
            '--retries_count', 10
        ])
    assert result.exit_code == 0
    assert 'message' in result.output


def test_command_forget_password(runner):
    result = runner.invoke(
        pindo.forget_password, [
            '--email', 'luinmeme@gmail.com'
        ])
    assert result.exit_code == 0
    assert 'Wrong email' in result.output
