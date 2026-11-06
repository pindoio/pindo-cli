"""CLI tests. All HTTP is mocked with ``responses``; nothing touches the network."""

from importlib.metadata import version as pkg_version

import pytest

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
    mocked.get(url('/junction/users/auth/otp'), json={'token': 'NEWTOKEN'})
    result = runner.invoke(pindo.cli, ['login', '-u', 'remy', '-p', 'pw'])
    assert result.exit_code == 0, result.output
    assert 'Logged in' in result.output
    data = cfg.load_config()
    assert data['token'] == 'NEWTOKEN'
    assert data['username'] == 'remy'
    assert 'base_url' not in data


def test_login_saves_custom_base_url(runner, mocked, isolated_config):
    mocked.get('https://staging.example/junction/users/auth/otp', json={'token': 'T'})
    result = runner.invoke(
        pindo.cli, ['--base-url', 'https://staging.example', 'login', '-u', 'r', '-p', 'p']
    )
    assert result.exit_code == 0, result.output
    assert cfg.load_config()['base_url'] == 'https://staging.example'


def test_login_no_save(runner, mocked, url, isolated_config):
    mocked.get(url('/junction/users/auth/otp'), json={'token': 'NEWTOKEN'})
    result = runner.invoke(pindo.cli, ['login', '-u', 'remy', '-p', 'pw', '--no-save'])
    assert result.exit_code == 0
    assert 'NEWTOKEN' in result.output
    assert not isolated_config.exists()


def test_login_wrong_credentials(runner, mocked, url):
    mocked.get(url('/junction/users/auth/otp'), json={'message': 'bad'}, status=401)
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
    mocked.get(url('/junction/users/auth/otp'), json={'token': 'ABC'})
    result = runner.invoke(pindo.cli, ['token', '-u', 'u', '-p', 'p'])
    assert result.exit_code == 0
    assert 'ABC' in result.output


def test_command_token_wrong_password(runner, mocked, url):
    mocked.get(url('/junction/users/auth/otp'), json={}, status=401)
    result = runner.invoke(pindo.cli, ['token', '-u', 'dgd', '-p', 'oUhdo'])
    assert result.exit_code == 1
    assert 'Wrong username or password' in result.output


def test_command_refresh_token_updates_saved(runner, mocked, url, saved_token):
    mocked.get(url('/junction/users/auth/token/refresh'), json={'token': 'FRESH'})
    result = runner.invoke(pindo.cli, ['refresh-token', '-u', 'remy', '-p', 'pw'])
    assert result.exit_code == 0, result.output
    assert 'FRESH' in result.output
    assert cfg.load_config()['token'] == 'FRESH'


def test_command_refresh_token_no_config(runner, mocked, url, isolated_config):
    mocked.get(url('/junction/users/auth/token/refresh'), json={'token': 'FRESH'})
    result = runner.invoke(pindo.cli, ['refresh-token', '-u', 'remy', '-p', 'pw'])
    assert result.exit_code == 0
    assert not isolated_config.exists()


def test_command_refresh_token_bad(runner, mocked, url):
    mocked.get(url('/junction/users/auth/token/refresh'), status=401)
    result = runner.invoke(pindo.cli, ['refresh-token', '-u', 'abc', '-p', 'cbd'])
    assert result.exit_code == 1
    assert 'Wrong username or password' in result.output


# ---------------------------------------------------------- register etc.


def test_command_register(runner, mocked, url):
    mocked.post(url('/junction/users/auth/register'), json={'message': 'account created'})
    result = runner.invoke(pindo.cli, ['register', '-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 0
    assert 'account created' in result.output


def test_command_register_conflict(runner, mocked, url):
    mocked.post(
        url('/junction/users/auth/register'),
        json={'message': 'username already exists in the database'},
        status=409,
    )
    result = runner.invoke(pindo.cli, ['register', '-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 1
    assert 'Error: username already exists in the database' in result.output


def test_command_register_server_error(runner, mocked, url):
    mocked.post(url('/junction/users/auth/register'), body='down', status=500)
    result = runner.invoke(pindo.cli, ['register', '-u', 'ken', '-e', 'remy@bar.io', '-p', 'bar'])
    assert result.exit_code == 1
    assert 'Error:' in result.output


@pytest.mark.parametrize('command', ['forgot-password', 'forget-password'])
def test_command_forgot_password(runner, mocked, url, command):
    """``forget-password`` is the old name and must keep working."""
    mocked.post(url('/junction/users/password/forgot'), json={'message': 'ok'})
    result = runner.invoke(pindo.cli, [command, '--email', 'remy@bar.io'])
    assert result.exit_code == 0, result.output
    assert 'recover-password' in result.output


def test_forget_password_alias_is_hidden(runner):
    result = runner.invoke(pindo.cli, ['--help'])
    assert 'forgot-password' in result.output
    assert 'forget-password' not in result.output
    assert 'recover-password' in result.output


def test_command_forgot_password_wrong_email(runner, mocked, url):
    mocked.post(
        url('/junction/users/password/forgot'), json={'message': 'no such user'}, status=404
    )
    result = runner.invoke(pindo.cli, ['forgot-password', '--email', 'nobody@bar.io'])
    assert result.exit_code == 1
    assert 'The email provided does not exist' in result.output


def test_command_recover_password(runner, mocked, url):
    mocked.put(url('/junction/users/password/recovery/RT'), json={'message': 'password updated'})
    result = runner.invoke(
        pindo.cli, ['recover-password', '-t', 'RT', '--password', 'a', '--confirm_password', 'a']
    )
    assert result.exit_code == 0
    assert 'password updated' in result.output
    assert mocked.calls[0].request.body == b'{"password": "a", "confirm_password": "a"}'


def test_command_recover_password_mismatch(runner, mocked):
    result = runner.invoke(
        pindo.cli, ['recover-password', '-t', 'RT', '--password', 'a', '--confirm-password', 'b']
    )
    assert result.exit_code == 2
    assert 'passwords do not match' in result.output
    assert len(mocked.calls) == 0


# ------------------------------------------------------- authenticated


def test_command_sms_with_flag_token(runner, mocked, url):
    mocked.post(url('/v1/sms/'), json={'status': 'sent', 'sms_id': 'out_1'})
    result = runner.invoke(
        pindo.cli,
        [
            'sms',
            '--token',
            'tok',
            '--to',
            '+250781234567',
            '--text',
            'Hello Pindo',
            '--sender',
            'Pindo',
        ],
    )
    assert result.exit_code == 0, result.output
    assert 'sent' in result.output
    assert mocked.calls[0].request.headers['Authorization'] == 'Bearer tok'


def test_command_sms_uses_saved_token(runner, mocked, url, saved_token):
    mocked.post(url('/v1/sms/'), json={'status': 'sent'})
    result = runner.invoke(
        pindo.cli, ['sms', '--to', '+250781234567', '--text', 'Hi', '--sender', 'Pindo']
    )
    assert result.exit_code == 0, result.output
    assert mocked.calls[0].request.headers['Authorization'] == 'Bearer ' + saved_token


def test_command_sms_uses_env_token(runner, mocked, url, monkeypatch):
    monkeypatch.setenv('PINDO_TOKEN', 'envtok')
    mocked.post(url('/v1/sms/'), json={'status': 'sent'})
    result = runner.invoke(
        pindo.cli, ['sms', '--to', '+250781234567', '--text', 'Hi', '--sender', 'P']
    )
    assert result.exit_code == 0, result.output
    assert mocked.calls[0].request.headers['Authorization'] == 'Bearer envtok'


def test_command_sms_without_token(runner, mocked):
    result = runner.invoke(
        pindo.cli, ['sms', '--to', '+250781234567', '--text', 'Hi', '--sender', 'P']
    )
    assert result.exit_code == 1
    assert 'No API token found' in result.output
    assert len(mocked.calls) == 0


def test_command_sms_api_error(runner, mocked, url):
    mocked.post(url('/v1/sms/'), json={'message': 'Wrong phone number format'}, status=409)
    result = runner.invoke(
        pindo.cli, ['sms', '-t', 'tok', '--to', '+250781234567', '--text', 'Hi', '--sender', 'P']
    )
    assert result.exit_code == 1
    assert 'Wrong phone number format (HTTP 409)' in result.output


@pytest.mark.parametrize(
    ('given', 'sent'),
    [('+250 78-123-4567', '+250781234567'), ('250781234567', '+250781234567')],
)
def test_command_sms_normalises_phone(runner, mocked, url, given, sent):
    mocked.post(url('/v1/sms/'), json={'status': 'sent'})
    result = runner.invoke(
        pindo.cli, ['sms', '-t', 'tok', '--to', given, '--text', 'Hi', '--sender', 'P']
    )
    assert result.exit_code == 0, result.output
    assert f'"to": "{sent}"'.encode() in mocked.calls[0].request.body


@pytest.mark.parametrize('bad', ['x', '+1', '0781234567', '+2507812345678901'])
def test_command_sms_rejects_bad_phone(runner, mocked, bad):
    result = runner.invoke(pindo.cli, ['sms', '-t', 'tok', '--to', bad, '--text', 'Hi'])
    assert result.exit_code == 2
    assert 'international format' in result.output
    assert len(mocked.calls) == 0


def test_command_sms_has_no_default_recipient(runner, mocked):
    """The recipient must always be chosen by the user, never defaulted."""
    result = runner.invoke(pindo.cli, ['sms', '-t', 'tok', '--text', 'Hi'], input='\n')
    assert result.exit_code != 0
    assert len(mocked.calls) == 0


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
    result = runner.invoke(
        pindo.cli,
        [
            'org',
            '--token',
            'tok',
            '--name',
            'Pindo',
            '--webhook_url',
            'https://pindo.io/webhook',
            '--retries_count',
            '10',
        ],
    )
    assert result.exit_code == 0, result.output
    assert 'updated' in result.output


def test_command_org_dash_options_and_validation(runner, mocked, url):
    mocked.put(url('/orgs/self'), json={'message': 'updated'})
    args = ['org', '-t', 'tok', '--name', 'P', '--retries-count', '2', '--webhook-url']
    result = runner.invoke(pindo.cli, [*args, 'https://pindo.io/dlr'])
    assert result.exit_code == 0, result.output
    assert mocked.calls[0].request.body == (
        b'{"name": "P", "webhook_url": "https://pindo.io/dlr", "sms_retries": 2}'
    )

    result = runner.invoke(pindo.cli, [*args, 'not-a-url'])
    assert result.exit_code == 2
    assert 'http(s) URL' in result.output


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


def test_debug_never_logs_secrets(runner, mocked, url):
    mocked.get(url('/junction/users/auth/otp'), json={'token': 'SECRET-TOKEN'})
    mocked.put(url('/junction/users/password/recovery/RT'), json={'message': 'ok'})
    result = runner.invoke(pindo.cli, ['--debug', 'token', '-u', 'u', '-p', 'pw'])
    assert result.exit_code == 0
    assert '"token": "***"' in result.output  # redacted in the debug log...
    assert result.output.count('SECRET-TOKEN') == 1  # ...and printed once, in the panel
    result = runner.invoke(
        pindo.cli,
        [
            '--debug',
            'recover-password',
            '-t',
            'RT',
            '--password',
            'hunter2',
            '--confirm-password',
            'hunter2',
        ],
    )
    assert result.exit_code == 0
    assert 'hunter2' not in result.output
    assert '***' in result.output


def test_short_help_flag(runner):
    result = runner.invoke(pindo.cli, ['-h'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output


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
