"""
HTTP client for the Pindo API.

Every CLI command talks to the backend through :class:`PindoClient`, which
owns a single ``requests.Session``, attaches the bearer token, applies a
timeout, retries transient failures on safe requests, logs requests when
``--debug`` is on (with secrets redacted), and converts any failure (network
error, non-2xx status, malformed JSON) into :class:`PindoClientException`
with a human-readable message.

Endpoint paths live in :data:`ENDPOINTS` so that a backend route change is a
one-line fix here rather than a hunt through the command code.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

from pindo_cli import __version__
from pindo_cli.config import DEFAULT_BASE_URL

log = logging.getLogger('pindo_cli')

DEFAULT_TIMEOUT = 30.0  # seconds
DEFAULT_RETRIES = 3

ENDPOINTS = {
    # authentication / account
    'token': '/users/token',
    'refresh_token': '/users/refresh/token',
    'register': '/users/register',
    'forgot_password': '/users/forgot',
    'recover_password': '/users/recovery/{token}',
    # messaging
    'sms_send': '/v1/sms/',
    # account resources
    'wallet': '/wallets/self',
    'organization': '/orgs/self',
}

# Keys whose values must never reach debug logs.
SENSITIVE_KEYS = frozenset(
    {'password', 'confirm_password', 'token', 'access_token', 'refresh_token', 'authorization'}
)
REDACTED = '***'


class PindoClientException(Exception):
    """Any error talking to the Pindo API, with a message safe to show users."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        payload: Any = None,
        url: str | None = None,
    ):
        super().__init__(message, status_code, payload, url)
        self.message = message
        self.status_code = status_code
        self.payload = payload
        self.url = url

    def __str__(self) -> str:
        if self.status_code:
            return f'{self.message} (HTTP {self.status_code})'
        return self.message


def redact(value: Any) -> Any:
    """Return a copy of ``value`` with secrets replaced, for logging."""
    if isinstance(value, Mapping):
        return {
            k: REDACTED if str(k).lower() in SENSITIVE_KEYS else redact(v) for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def _redact_text(text: str) -> str:
    """Redact a response body that may be JSON containing a token."""
    try:
        return json.dumps(redact(json.loads(text)))
    except ValueError:
        return text


def _extract_message(payload: Any, default: str) -> str:
    """Pull the most useful error text out of an API error body."""
    if isinstance(payload, dict):
        for key in ('message', 'error', 'detail', 'msg'):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, dict):
                # e.g. {"message": {"username": "already exists"}}
                return '; '.join(f'{k}: {v}' for k, v in value.items())
        if payload:
            return json.dumps(payload)
    if isinstance(payload, str) and payload.strip():
        return payload.strip()[:200]
    return default


def _retrying_adapter(retries: int) -> HTTPAdapter:
    """Retry idempotent requests on connection errors, 429 and 5xx gateway
    errors with exponential backoff, honouring ``Retry-After``. POSTs (e.g.
    sending an SMS) are never retried so a message is never sent twice."""
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 502, 503, 504),
        allowed_methods=frozenset({'GET', 'HEAD', 'OPTIONS'}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    return HTTPAdapter(max_retries=retry)


class PindoClient:
    """Thin wrapper over the Pindo REST API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
        retries: int = DEFAULT_RETRIES,
    ):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        if session is None:
            session = requests.Session()
            adapter = _retrying_adapter(retries)
            session.mount('https://', adapter)
            session.mount('http://', adapter)
        self.session = session
        self.session.headers.update(
            {
                'Accept': 'application/json',
                'User-Agent': f'pindo-cli/{__version__}',
            }
        )

    # ------------------------------------------------------------------ core

    def url(self, path: str, **fmt: Any) -> str:
        if path.startswith(('http://', 'https://')):
            return path
        return self.base_url + path.format(**fmt)

    def _request(
        self,
        method: str,
        path: str,
        *,
        auth: HTTPBasicAuth | None = None,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        authenticated: bool = True,
        **fmt: Any,
    ) -> Any:
        """Perform a request and return the decoded JSON body.

        Raises :class:`PindoClientException` on network errors, non-2xx
        responses, or bodies that are not JSON.
        """
        url = self.url(path, **fmt)
        headers: dict[str, str] = {}
        if authenticated and auth is None:
            if not self.token:
                raise PindoClientException('No API token configured.', url=url)
            headers['Authorization'] = 'Bearer ' + self.token

        log.debug('%s %s params=%s body=%s', method, url, params, redact(json_body))
        try:
            resp = self.session.request(
                method,
                url,
                auth=auth,
                json=json_body,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise PindoClientException(
                f'The request to {url} timed out after {self.timeout:g}s.', url=url
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise PindoClientException(
                f'Could not connect to {self.base_url}. Check your network or PINDO_BASE_URL.',
                url=url,
            ) from exc
        except requests.exceptions.RequestException as exc:  # pragma: no cover
            raise PindoClientException(f'Request failed: {exc}', url=url) from exc

        log.debug('-> HTTP %s %s', resp.status_code, _redact_text(resp.text[:2000]))
        return _decode_response(resp, url)

    def get(self, path: str, params: dict[str, Any] | None = None, **kw: Any) -> Any:
        return self._request('GET', path, params=params, **kw)

    def post(self, path: str, json_body: dict[str, Any] | None = None, **kw: Any) -> Any:
        return self._request('POST', path, json_body=json_body, **kw)

    def put(self, path: str, json_body: dict[str, Any] | None = None, **kw: Any) -> Any:
        return self._request('PUT', path, json_body=json_body, **kw)

    # ------------------------------------------------------------ pagination

    def get_page(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        items_key: str | None = None,
    ) -> tuple[list[Any], dict[str, Any]]:
        """Fetch one page and return ``(items, pages)``.

        The Pindo API wraps lists as ``{"<items_key>": [...], "pages": {...}}``
        where ``pages`` carries ``page``, ``pages``, ``per_page``, ``total`` and
        ``next_url``. When ``items_key`` is omitted the first list value in
        the body is used. A bare JSON list is also accepted.
        """
        body = self.get(path, params=params)
        if isinstance(body, list):
            return body, {}
        if not isinstance(body, dict):
            return [], {}
        if items_key is None:
            items_key = next((k for k, v in body.items() if isinstance(v, list)), None)
        items = body.get(items_key, []) if items_key else []
        return list(items), dict(body.get('pages') or {})

    def iter_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        items_key: str | None = None,
        max_pages: int | None = None,
    ) -> Iterator[Any]:
        """Yield items across all pages, following ``pages.next_url``."""
        params = dict(params or {})
        fetched = 0
        next_path: str | None = path
        while next_path:
            items, pages = self.get_page(next_path, params=params, items_key=items_key)
            yield from items
            fetched += 1
            if max_pages is not None and fetched >= max_pages:
                return
            next_path = pages.get('next_url') or None
            # next_url already encodes page/per_page; don't resend them.
            params = {}
            if not items:
                return

    # ---------------------------------------------------------- auth / user

    def get_token(self, username: str, password: str) -> str:
        body = self.get(ENDPOINTS['token'], auth=HTTPBasicAuth(username, password))
        return _require_key(body, 'token')

    def refresh_token(self, username: str, password: str) -> str:
        body = self.get(ENDPOINTS['refresh_token'], auth=HTTPBasicAuth(username, password))
        return _require_key(body, 'token')

    def register(self, username: str, email: str, password: str) -> str:
        body = self.post(
            ENDPOINTS['register'],
            json_body={'username': username, 'email': email, 'password': password},
            authenticated=False,
        )
        return _require_key(body, 'message')

    def forgot_password(self, email: str) -> Any:
        return self.post(
            ENDPOINTS['forgot_password'], json_body={'email': email}, authenticated=False
        )

    def recover_password(self, token: str, password: str, confirm_password: str) -> str:
        body = self.put(
            ENDPOINTS['recover_password'],
            json_body={'password': password, 'confirm_password': confirm_password},
            authenticated=False,
            token=token,
        )
        return _require_key(body, 'message')

    # ----------------------------------------------------------- messaging

    def send_sms(self, to: str, text: str, sender: str) -> dict[str, Any]:
        return self.post(
            ENDPOINTS['sms_send'], json_body={'to': to, 'text': text, 'sender': sender}
        )

    # ------------------------------------------------------------- account

    def wallet(self) -> dict[str, Any]:
        return self.get(ENDPOINTS['wallet'])

    def balance(self) -> Any:
        return _require_key(self.wallet(), 'amount')

    def update_organization(self, name: str, webhook_url: str, sms_retries: int) -> dict[str, Any]:
        return self.put(
            ENDPOINTS['organization'],
            json_body={'name': name, 'webhook_url': webhook_url, 'sms_retries': sms_retries},
        )


_STATUS_MESSAGES = {
    401: 'Unauthorized. Your token is invalid or expired; run `pindo login`.',
    403: 'Forbidden. Your account is not allowed to do this.',
    404: 'Not found.',
    409: 'Conflict.',
    429: 'Too many requests. Wait a moment and try again.',
}


def _decode_response(resp: requests.Response, url: str) -> Any:
    """Decode a JSON body, raising a clean exception for errors."""
    payload: Any
    try:
        payload = resp.json() if resp.content else None
    except ValueError:
        payload = resp.text

    if not resp.ok:
        default = _STATUS_MESSAGES.get(resp.status_code, 'The Pindo API returned an error.')
        raise PindoClientException(
            _extract_message(payload, default),
            status_code=resp.status_code,
            payload=payload,
            url=url,
        )

    if resp.content and not isinstance(payload, dict | list):
        raise PindoClientException(
            'Unexpected non-JSON response from the API.',
            status_code=resp.status_code,
            payload=payload,
            url=url,
        )
    return payload


def _require_key(body: Any, key: str) -> Any:
    if not isinstance(body, dict) or key not in body:
        raise PindoClientException(
            f'Unexpected response from the API: missing "{key}".', payload=body
        )
    return body[key]
