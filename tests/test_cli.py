"""CLI tests. All HTTP is mocked with ``responses``; nothing touches the network."""
import pytest
from importlib.metadata import version as pkg_version

import pindo_cli.cli as pindo
from pindo_cli import config as cfg


def test_pindo_cli_help(runner):
    result = runner.invoke(pindo.cli, ['--help'])
    assert result.exit_code == 0
    assert 'Pindo CLI' in result.output
    assert 'report' in result.output


def test_pindo_cli_version_flag(runner):
    result = runner.invoke(pindo.cli, ['--version'])
    assert result.exit_code == 0
    assert pkg_version('pindo-cli') in result.output


# ------------------------------------------------------------- login

def test_login_saves_token(runner, mocked, url, isolated_config):
    mocked.get(url('/users/token'), json={'token': 'NEWTOKEN'})
    result = runner.invoke(pindo.cli, ['login', '-u', 'remy', '-p', 'pw'])
    assert result.exit_code == 0, result.output
    assert 'Logged in' in result.output
    data = cfg.load_config()
    assert data['token'] == 'NEWTOKEN'
    assert data['username'] == 'remy'
    assert 'base_url' not in data


def test_login_saves_custom_base_url(runner, mocked, isolated_config):
    mocked.get('https://staging.example/users/token', json={'token': 'T'})
    result = runner.invoke(
        pindo.cli, ['--base-url', 'https://staging.example', 'login', '-u', 'r', '-p', 'p'])
    assert result.exit_code == 0, result.output
    assert cfg.load_config()['base_url'] == 'https://staging.example'


def test_login_no_save(runner, mocked, url, isolated_config):
    mocked.get(url('/users/token'), json={'token': 'NEWTOKEN'})
    result = runner.invoke(pindo.cli, ['login', '-u', 'remy', '-p', 'pw', '--no-save'])
    assert result.exit_code == 0
    assert 'NEWTOKEN' in result.output
    assert not isolated_config.exists()


def test_login_wrong_credentials(runner, mocked, url):
    mocked.get(url('/users/token'), json={'message': 'bad'}, status=401)
    result = runner.invoke(pindo.cli, ['login', '-u', 'dgd', '-p', 'oUhdo'])
    assert result.exit_code == 1
    assert 'Wrong username or password' in result.output


def test_logout(runner, saved_token, isolated_config):
    result = runner.invoke(pindo.cli, ['logout'])
    assert result.exit_code == 0
    assert 'Logged out' in result.output
    assert not isolated_config.exists()
    result = runner.invoke(pindo.cli, ['logout'])
    assert 'No saved credentials' in result.output


# ------------------------------------------------------------- token

def test_command_token(runner, mocked, url):
    mocked.get(url('/users/token'), json={'token': 'ABC'})
    result = runner.invoke(pindo.cli, ['token', '-u', 'u', '-p', 'p'])
    assert result.exit_code == 0
    assert 'ABC' in result.output


def test_command_token_wrong_password(runner, mocked, url):
    mocked.get(url('/users/token'), json={}, status=401)
    result = runner.invoke(pindo.cli, ['token', '-u', 'dgd', '-p', 'oUhdo'])
    assert result.exit_code == 1
    assert 'Wrong username or password' in result.output


def test_command_refresh_token_updates_saved(runner, mocked, url, saved_token):
    mocked.get(url('/users/refresh/token'), json={'token': 'FRESH'})
    result = runner.invoke(pindo.cli, ['refresh-token', '-u', 'remy', '-p', 'pw'])
    assert result.exit_code == 0, result.output
    assert 'FRESH' in result.output
    assert cfg.load_config()['token'] == 'FRESH'


def test_command_refresh_token_no_config(runner, mocked, url, isolated_config):
    mocked.get(url('/users/refresh/token'), json={'token': 'FRESH'})
    result = runner.invoke(pindo.cli, ['refresh-token', '-u', 'remy', '-p', 'pw'])
    assert result.exit_code == 0
    assert not isolated_config.exists()


def test_command_refresh_token_bad(runner, mocked, url):
    mocked.get(url('/users/refresh/token'), status=401)
    result = runner.invoke(pindo.cli, ['refresh-token', '-u', 'abc', '-p', 'cbd'])
    assert result.exit_code == 1
    assert 'Wrong username or password' in result.output


# ---------------------------------------------------------- register etc.

def test_command_register(runner, mocked, url):
    mocked.post(url('/users/register'), json={'message': 'account created'})
    result = runner.invoke(pindo.cli, ['register', '-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 0
    assert 'account created' in result.output


def test_command_register_conflict(runner, mocked, url):
    mocked.post(url('/users/register'),
                json={'message': 'username already exists in the database'}, status=409)
    result = runner.invoke(pindo.cli, ['register', '-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 0
    assert 'username already exists in the database' in result.output


def test_command_register_server_error(runner, mocked, url):
    mocked.post(url('/users/register'), body='down', status=500)
    result = runner.invoke(pindo.cli, ['register', '-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 1
    assert 'Error:' in result.output


def test_command_forget_password(runner, mocked, url):
    mocked.post(url('/users/forgot'), json={'message': 'ok'})
    result = runner.invoke(pindo.cli, ['forget-password', '--email', 'remy@bar.io'])
    assert result.exit_code == 0
    assert 'recover-password' in result.output


def test_command_forget_password_wrong_email(runner, mocked, url):
    mocked.post(url('/users/forgot'), json={'message': 'no such user'}, status=404)
    result = runner.invoke(pindo.cli, ['forget-password', '--email', 'nobody@bar.io'])
    assert result.exit_code == 0
    assert 'Wrong email' in result.output


def test_command_recover_password(runner, mocked, url):
    mocked.put(url('/users/recovery/RT'), json={'message': 'password updated'})
    result = runner.invoke(pindo.cli, ['recover-password', '-t', 'RT',
                                       '--password', 'a', '--confirm_password', 'a'])
    assert result.exit_code == 0
    assert 'password updated' in result.output


# ------------------------------------------------------- authenticated

def test_command_sms_with_flag_token(runner, mocked, url):
    mocked.post(url('/v1/sms/'), json={'status': 'sent', 'sms_id': 'out_1'})
    result = runner.invoke(pindo.cli, ['sms', '--token', 'tok', '--to', '+250785383100',
                                       '--text', 'Hello Pindo', '--sender', 'Pindo'])
    assert result.exit_code == 0, result.output
    assert 'sent' in result.output
    assert mocked.calls[0].request.headers['Authorization'] == 'Bearer tok'


def test_command_sms_uses_saved_token(runner, mocked, url, saved_token):
    mocked.post(url('/v1/sms/'), json={'status': 'sent'})
    result = runner.invoke(pindo.cli, ['sms', '--to', '+250785383100',
                                       '--text', 'Hi', '--sender', 'Pindo'])
    assert result.exit_code == 0, result.output
    assert mocked.calls[0].request.headers['Authorization'] == 'Bearer ' + saved_token


def test_command_sms_uses_env_token(runner, mocked, url, monkeypatch):
    monkeypatch.setenv('PINDO_TOKEN', 'envtok')
    mocked.post(url('/v1/sms/'), json={'status': 'sent'})
    result = runner.invoke(pindo.cli, ['sms', '--to', '+1', '--text', 'Hi', '--sender', 'P'])
    assert result.exit_code == 0, result.output
    assert mocked.calls[0].request.headers['Authorization'] == 'Bearer envtok'


def test_command_sms_without_token(runner, mocked):
    result = runner.invoke(pindo.cli, ['sms', '--to', '+1', '--text', 'Hi', '--sender', 'P'])
    assert result.exit_code == 1
    assert 'No API token found' in result.output
    assert len(mocked.calls) == 0


def test_command_sms_api_error(runner, mocked, url):
    mocked.post(url('/v1/sms/'), json={'message': 'Wrong phone number format'}, status=409)
    result = runner.invoke(pindo.cli, ['sms', '-t', 'tok', '--to', 'x', '--text', 'Hi',
                                       '--sender', 'P'])
    assert result.exit_code == 1
    assert 'Wrong phone number format (HTTP 409)' in result.output


def test_command_balance(runner, mocked, url):
    mocked.get(url('/wallets/self'), json={'amount': 71421.953, 'currency': 'RWF'})
    result = runner.invoke(pindo.cli, ['balance', '--token', 'tok'])
    assert result.exit_code == 0, result.output
    assert 'RWF 71421.953' in result.output


def test_command_balance_defaults_usd(runner, mocked, url):
    mocked.get(url('/wallets/self'), json={'amount': 5})
    result = runner.invoke(pindo.cli, ['balance', '--token', 'tok'])
    assert 'USD 5' in result.output


def test_command_balance_unauthorized(runner, mocked, url):
    mocked.get(url('/wallets/self'), status=401)
    result = runner.invoke(pindo.cli, ['balance', '--token', 'bad'])
    assert result.exit_code == 1
    assert 'Unauthorized' in result.output


def test_command_org(runner, mocked, url):
    mocked.put(url('/orgs/self'), json={'message': 'updated'})
    result = runner.invoke(pindo.cli, ['org', '--token', 'tok', '--name', 'Pindo',
                                       '--webhook_url', 'https://pindo.io/webhook',
                                       '--retries_count', '10'])
    assert result.exit_code == 0, result.output
    assert 'updated' in result.output


# ------------------------------------------------------------- config

def test_config_show_sources(runner, saved_token, monkeypatch):
    result = runner.invoke(pindo.cli, ['config', 'show'])
    assert result.exit_code == 0
    assert 'config file' in result.output
    assert 'file...3456' in result.output
    assert 'remy' in result.output

    monkeypatch.setenv('PINDO_TOKEN', 'envtoken987654')
    result = runner.invoke(pindo.cli, ['config', 'show'])
    assert 'PINDO_TOKEN' in result.output

    result = runner.invoke(pindo.cli, ['config', 'show', '--token', 'flagtoken1234'])
    assert '--token flag' in result.output


def test_config_show_none(runner):
    result = runner.invoke(pindo.cli, ['config', 'show'])
    assert 'not set' in result.output


def test_config_path(runner, isolated_config):
    result = runner.invoke(pindo.cli, ['config', 'path'])
    assert result.output.strip() == str(isolated_config)


# -------------------------------------------------------------- debug

def test_debug_logs_requests(runner, mocked, url):
    mocked.get(url('/wallets/self'), json={'message': 'nope'}, status=500)
    result = runner.invoke(pindo.cli, ['--debug', 'balance', '--token', 'tok'])
    assert result.exit_code == 1
    assert 'GET ' + url('/wallets/self') in result.output
    assert "'nope'" in result.output  # payload pretty-printed


def test_report_group_help(runner):
    result = runner.invoke(pindo.cli, ['report', '--help'])
    assert result.exit_code == 0
    assert '--from/--to' in result.output


# --------------------------------------------------------------- live

@pytest.mark.live
def test_live_wrong_credentials(runner):
    """Hits the real API. Run with ``pytest --run-live``."""
    result = runner.invoke(pindo.cli, ['token', '-u', 'dgd', '-p', 'oUhdo'])
    assert result.exit_code == 1
    assert 'Wrong username or password' in result.output
