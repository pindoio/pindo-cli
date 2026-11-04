"""
Configuration and credential storage for the Pindo CLI.

Resolution order for the API token (highest priority first):

1. ``--token`` passed on the command line
2. the ``PINDO_TOKEN`` environment variable
3. the ``token`` key in ``~/.pindo/config.toml`` (written by ``pindo login``)

Resolution order for the API base URL:

1. the ``PINDO_BASE_URL`` environment variable
2. the ``base_url`` key in the config file
3. ``https://api.pindo.io``
"""
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import tomlkit

DEFAULT_BASE_URL = 'https://api.pindo.io'
ENV_TOKEN = 'PINDO_TOKEN'
ENV_BASE_URL = 'PINDO_BASE_URL'
ENV_CONFIG_PATH = 'PINDO_CONFIG'

# Where the token came from; shown by ``pindo config show``.
SOURCE_FLAG = 'flag'
SOURCE_ENV = 'env'
SOURCE_FILE = 'file'
SOURCE_NONE = 'none'


class MissingTokenError(Exception):
    """Raised when a command needs a token and none can be found."""

    def __init__(self):
        super().__init__(
            'No API token found. Run `pindo login`, set the {} environment '
            'variable, or pass --token.'.format(ENV_TOKEN))


def config_path() -> Path:
    """Path of the config file. Override with ``PINDO_CONFIG`` (used by tests)."""
    override = os.environ.get(ENV_CONFIG_PATH)
    if override:
        return Path(override).expanduser()
    return Path.home() / '.pindo' / 'config.toml'


def load_config() -> dict:
    """Return the config file contents as a plain dict (empty if absent)."""
    path = config_path()
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8') as fh:
        return dict(tomlkit.parse(fh.read()))


def save_config(data: dict) -> Path:
    """Write ``data`` to the config file, creating the directory and restricting
    permissions so the token is readable only by the current user."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = tomlkit.document()
    for key, value in data.items():
        if value is not None:
            doc[key] = value
    with path.open('w', encoding='utf-8') as fh:
        fh.write(tomlkit.dumps(doc))
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:  # pragma: no cover - e.g. Windows without POSIX perms
        pass
    return path


def update_config(**changes) -> Path:
    """Merge ``changes`` into the config file. ``None`` removes a key."""
    data = load_config()
    for key, value in changes.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    return save_config(data)


def clear_config() -> bool:
    """Delete the config file. Returns True if a file was removed."""
    path = config_path()
    if path.exists():
        path.unlink()
        return True
    return False


@dataclass
class Settings:
    token: Optional[str]
    token_source: str
    base_url: str
    username: Optional[str] = None

    def require_token(self) -> str:
        if not self.token:
            raise MissingTokenError()
        return self.token

    @property
    def masked_token(self) -> str:
        if not self.token:
            return '(none)'
        if len(self.token) <= 8:
            return '*' * len(self.token)
        return '{}...{}'.format(self.token[:4], self.token[-4:])


def resolve(token: Optional[str] = None, base_url: Optional[str] = None) -> Settings:
    """Resolve the effective settings.

    ``token`` and ``base_url`` are the command-line flag values and win over
    environment variables and the config file.
    """
    file_cfg = load_config()

    if token:
        source = SOURCE_FLAG
    elif os.environ.get(ENV_TOKEN):
        token = os.environ[ENV_TOKEN]
        source = SOURCE_ENV
    elif file_cfg.get('token'):
        token = str(file_cfg['token'])
        source = SOURCE_FILE
    else:
        token = None
        source = SOURCE_NONE

    base_url = (
        base_url
        or os.environ.get(ENV_BASE_URL)
        or file_cfg.get('base_url')
        or DEFAULT_BASE_URL
    )
    base_url = str(base_url).rstrip('/')

    return Settings(
        token=token,
        token_source=source,
        base_url=base_url,
        username=file_cfg.get('username'),
    )
