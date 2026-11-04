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

from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomlkit

DEFAULT_BASE_URL = 'https://api.pindo.io'
ENV_TOKEN = 'PINDO_TOKEN'
ENV_BASE_URL = 'PINDO_BASE_URL'
ENV_CONFIG_PATH = 'PINDO_CONFIG'

_PRIVATE_FILE = stat.S_IRUSR | stat.S_IWUSR  # 0600
_PRIVATE_DIR = stat.S_IRWXU  # 0700

# Where the token came from; shown by ``pindo config show``.
SOURCE_FLAG = 'flag'
SOURCE_ENV = 'env'
SOURCE_FILE = 'file'
SOURCE_NONE = 'none'


class MissingTokenError(Exception):
    """Raised when a command needs a token and none can be found."""

    def __init__(self):
        super().__init__(
            f'No API token found. Run `pindo login`, set the {ENV_TOKEN} environment '
            'variable, or pass --token.'
        )


def config_path() -> Path:
    """Path of the config file. Override with ``PINDO_CONFIG`` (used by tests)."""
    override = os.environ.get(ENV_CONFIG_PATH)
    if override:
        return Path(override).expanduser()
    return Path.home() / '.pindo' / 'config.toml'


def load_config() -> dict[str, Any]:
    """Return the config file contents as a plain dict (empty if absent)."""
    path = config_path()
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8') as fh:
        return tomlkit.parse(fh.read()).unwrap()


def save_config(data: dict[str, Any]) -> Path:
    """Write ``data`` to the config file.

    The file is created with owner-only permissions (0600) from the start and
    swapped into place atomically, so the token is never briefly readable by
    other users and a crash mid-write never leaves a truncated file.
    """
    path = config_path()
    _ensure_private_dir(path.parent)
    doc = tomlkit.document()
    for key, value in data.items():
        if value is not None:
            doc[key] = value

    fd, tmp_name = tempfile.mkstemp(prefix='.config-', suffix='.toml', dir=path.parent)
    tmp = Path(tmp_name)
    try:
        os.chmod(tmp, _PRIVATE_FILE)  # mkstemp already uses 0600 on POSIX; be explicit
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write(tomlkit.dumps(doc))
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path


def _ensure_private_dir(directory: Path) -> None:
    if directory.exists():
        return
    directory.mkdir(parents=True, mode=_PRIVATE_DIR)


def update_config(**changes: Any) -> Path:
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
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True


@dataclass
class Settings:
    token: str | None
    token_source: str
    base_url: str
    username: str | None = None

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
        return f'{self.token[:4]}...{self.token[-4:]}'


def resolve(token: str | None = None, base_url: str | None = None) -> Settings:
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
        base_url or os.environ.get(ENV_BASE_URL) or file_cfg.get('base_url') or DEFAULT_BASE_URL
    )
    base_url = str(base_url).rstrip('/')

    return Settings(
        token=token,
        token_source=source,
        base_url=base_url,
        username=file_cfg.get('username'),
    )
