"""
Backward-compatible wrappers around :class:`pindo_cli.client.PindoClient`.

These classes are the pre-0.3 API (``str(Token(user, pw))`` etc.). New code
should use :class:`PindoClient` directly; this module exists so that anything
importing ``pindo_cli.http`` keeps working. It is deprecated and will be
removed in the next major release.
"""

import warnings

import requests

from pindo_cli.client import DEFAULT_TIMEOUT, ENDPOINTS, PindoClient, PindoClientException
from pindo_cli.config import DEFAULT_BASE_URL

__all__ = [
    'SMS',
    'Balance',
    'Config',
    'ForgetPassword',
    'Organization',
    'PindoClient',
    'PindoClientException',
    'RecoverPassword',
    'RefreshToken',
    'Register',
    'Token',
]

warnings.warn(
    'pindo_cli.http is deprecated; use pindo_cli.client.PindoClient instead.',
    DeprecationWarning,
    stacklevel=2,
)


class Config:
    BASE_URL = DEFAULT_BASE_URL


def _client(token=None):
    return PindoClient(base_url=Config.BASE_URL, token=token)


class Token(Config):
    """Request a Pindo Token"""

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __str__(self):
        return str(_client().get_token(self.username, self.password))


class RefreshToken(Config):
    """Refresh a Pindo token"""

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __str__(self):
        return str(_client().refresh_token(self.username, self.password))


class Register(Config):
    """Register a new account"""

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __str__(self):
        return str(_client().register(self.username, self.email, self.password))


class ForgetPassword(Config):
    """Forget Password"""

    def __init__(self, email):
        self.email = email

    def resp(self):
        return requests.post(
            Config.BASE_URL + ENDPOINTS['forgot_password'],
            json={'email': self.email},
            timeout=DEFAULT_TIMEOUT,
        )


class RecoverPassword(Config):
    """Recover Password"""

    def __init__(self, token, password, confirm_password):
        self.token = token
        self.password = password
        self.confirm_password = confirm_password

    def __str__(self):
        return str(_client().recover_password(self.token, self.password, self.confirm_password))


class SMS(Config):
    """Send a test Message"""

    def __init__(self, token, to, text, sender):
        self.token = token
        self.to = to
        self.text = text
        self.sender = sender

    def send(self):
        return _client(self.token).send_sms(self.to, self.text, self.sender)


class Balance(Config):
    """Get user's wallet"""

    def __init__(self, token):
        self.token = token

    def __str__(self):
        return str(_client(self.token).balance())


class Organization(Config):
    """Organization setup"""

    def __init__(self, token, name, webhook_url, retries_count):
        self.token = token
        self.name = name
        self.webhook_url = webhook_url
        self.retries_count = retries_count

    def __str__(self):
        return str(
            _client(self.token).update_organization(self.name, self.webhook_url, self.retries_count)
        )
