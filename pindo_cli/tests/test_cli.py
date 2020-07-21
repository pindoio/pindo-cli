import pytest
from click.testing import CliRunner
from pkg_resources import get_distribution

import pindo_cli


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_pindo_cli(runner):
    result = runner.invoke(pindo_cli.cli, ['--help'])
    assert result.exit_code == 0
    assert 'Pindo CLI' in result.output


def test_command_token(runner):
    result = runner.invoke(pindo_cli.token, ['-u', 'abc', '-p', 'cbd'])
    assert result.exit_code == 0
    assert 'message' in result.output


def test_command_refresh_token(runner):
    result = runner.invoke(pindo_cli.refresh_token, ['-u', 'abc', '-p', 'cbd'])
    assert result.exit_code == 0
    assert 'message' in result.output


def test_command_register(runner):
    result = runner.invoke(
        pindo_cli.register,
        ['-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 0
    assert 'message' in result.output


def test_command_sms(runner):
    result = runner.invoke(
        pindo_cli.sms, [
            '--token', 'oeiroeoeioeoiroe',
            '--to', '+250785383100',
            '--text', 'Hello Pindo',
            '--sender', 'Pindo'
        ])
    assert result.exit_code == 0
    assert 'message' in result.output


def test_command_(runner):
    result = runner.invoke(
        pindo_cli.balance, [
            '--token', 'oeiroeoeioeoiroe',
        ])
    assert result.exit_code == 0
    assert 'message' in result.output


def test_pindo_cli_version_flag(runner):
    result = runner.invoke(pindo_cli.cli, ['--version', "-v"])
    assert result.exit_code == 0
    assert get_distribution('pindo-cli').version in result.output


def test_command_org(runner):
    result = runner.invoke(
        pindo_cli.org, [
            '--token', 'oeiroeoeioeoiroe',
            '--name', 'Pindo',
            '--webhook_url', 'https://pindo.io/webhook',
            '--retries_count', 10
        ])
    assert result.exit_code == 0
    assert 'message' in result.output
