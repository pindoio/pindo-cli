import os

import pytest
import responses as responses_lib
from click.testing import CliRunner

from pindo_cli.config import DEFAULT_BASE_URL

API = DEFAULT_BASE_URL


def pytest_addoption(parser):
    parser.addoption(
        '--run-live',
        action='store_true',
        default=False,
        help='run tests that hit the real Pindo API',
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-live'):
        return
    skip = pytest.mark.skip(reason='needs --run-live')
    for item in items:
        if 'live' in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point the CLI at a throwaway config file and scrub env overrides."""
    path = tmp_path / 'config.toml'
    monkeypatch.setenv('PINDO_CONFIG', str(path))
    monkeypatch.delenv('PINDO_TOKEN', raising=False)
    monkeypatch.delenv('PINDO_BASE_URL', raising=False)
    return path


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mocked():
    """A ``responses`` mock that fails on any unexpected request."""
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def url():
    def _url(path):
        return API + path

    return _url


@pytest.fixture
def saved_token(isolated_config):
    isolated_config.write_text('token = "filetoken123456"\nusername = "remy"\n')
    return 'filetoken123456'


def env(**kw):
    """Helper for tests that need extra env vars."""
    return dict(os.environ, **kw)
