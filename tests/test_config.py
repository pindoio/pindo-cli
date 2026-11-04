import os
import stat
import sys

import pytest

from pindo_cli import config as cfg


def test_defaults_when_nothing_configured():
    s = cfg.resolve()
    assert s.token is None
    assert s.token_source == cfg.SOURCE_NONE
    assert s.base_url == cfg.DEFAULT_BASE_URL
    assert s.masked_token == '(none)'
    with pytest.raises(cfg.MissingTokenError):
        s.require_token()


def test_flag_beats_env_beats_file(isolated_config, monkeypatch):
    isolated_config.write_text('token = "from-file"\n')
    assert cfg.resolve().token_source == cfg.SOURCE_FILE
    assert cfg.resolve().token == 'from-file'

    monkeypatch.setenv('PINDO_TOKEN', 'from-env')
    assert cfg.resolve().token == 'from-env'
    assert cfg.resolve().token_source == cfg.SOURCE_ENV

    s = cfg.resolve(token='from-flag')
    assert s.token == 'from-flag'
    assert s.token_source == cfg.SOURCE_FLAG
    assert s.require_token() == 'from-flag'


def test_base_url_resolution(isolated_config, monkeypatch):
    isolated_config.write_text('base_url = "https://file.example/"\n')
    assert cfg.resolve().base_url == 'https://file.example'
    monkeypatch.setenv('PINDO_BASE_URL', 'https://env.example')
    assert cfg.resolve().base_url == 'https://env.example'
    assert cfg.resolve(base_url='https://flag.example').base_url == 'https://flag.example'


def test_update_and_clear_config(isolated_config):
    path = cfg.update_config(token='abc', username='remy')
    assert path == isolated_config
    data = cfg.load_config()
    assert data == {'token': 'abc', 'username': 'remy'}

    cfg.update_config(username=None, base_url='https://staging.example')
    assert cfg.load_config() == {'token': 'abc', 'base_url': 'https://staging.example'}

    if sys.platform != 'win32':
        mode = stat.S_IMODE(os.stat(isolated_config).st_mode)
        assert mode == 0o600

    assert cfg.clear_config() is True
    assert not isolated_config.exists()
    assert cfg.clear_config() is False


def test_masked_token():
    assert cfg.Settings('abcdefghijkl', cfg.SOURCE_FLAG, 'x').masked_token == 'abcd...ijkl'
    assert cfg.Settings('short', cfg.SOURCE_FLAG, 'x').masked_token == '*****'


def test_config_path_default(monkeypatch):
    monkeypatch.delenv('PINDO_CONFIG')
    assert cfg.config_path().name == 'config.toml'
    assert cfg.config_path().parent.name == '.pindo'


@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX permissions')
def test_config_dir_and_file_are_private(tmp_path, monkeypatch):
    path = tmp_path / 'nested' / 'config.toml'
    monkeypatch.setenv('PINDO_CONFIG', str(path))
    cfg.save_config({'token': 'secret'})
    assert stat.S_IMODE(os.stat(path.parent).st_mode) == 0o700
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_save_config_is_atomic(isolated_config, monkeypatch):
    cfg.save_config({'token': 'old'})

    def boom(*args, **kwargs):
        raise OSError('disk full')

    monkeypatch.setattr(cfg.os, 'replace', boom)
    with pytest.raises(OSError, match='disk full'):
        cfg.save_config({'token': 'new'})
    # the original file is untouched and no temp files are left behind
    assert cfg.load_config() == {'token': 'old'}
    assert [p.name for p in isolated_config.parent.iterdir()] == ['config.toml']


def test_load_config_returns_plain_types(isolated_config):
    isolated_config.write_text('token = "abc"\nusername = "remy"\n')
    data = cfg.load_config()
    assert type(data['token']) is str
