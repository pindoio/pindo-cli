"""The pre-0.3 ``pindo_cli.http`` classes must keep working (with a deprecation warning)."""

import importlib
import sys

import pytest


@pytest.fixture
def http():
    sys.modules.pop('pindo_cli.http', None)
    with pytest.warns(DeprecationWarning, match='pindo_cli.http is deprecated'):
        return importlib.import_module('pindo_cli.http')


def test_shim_classes(mocked, url, http):
    mocked.get(url('/users/token'), json={'token': 'T'})
    mocked.get(url('/users/refresh/token'), json={'token': 'R'})
    mocked.post(url('/users/register'), json={'message': 'created'})
    mocked.post(url('/users/forgot'), json={'message': 'sent'})
    mocked.put(url('/users/recovery/RT'), json={'message': 'done'})
    mocked.post(url('/v1/sms/'), json={'status': 'sent'})
    mocked.get(url('/wallets/self'), json={'amount': 3})
    mocked.put(url('/orgs/self'), json={'message': 'ok'})

    assert str(http.Token('u', 'p')) == 'T'
    assert str(http.RefreshToken('u', 'p')) == 'R'
    assert str(http.Register('u', 'e', 'p')) == 'created'
    assert http.ForgetPassword('e').resp().status_code == 200
    assert str(http.RecoverPassword('RT', 'a', 'a')) == 'done'
    assert http.SMS('tok', '+1', 'hi', 'P').send() == {'status': 'sent'}
    assert str(http.Balance('tok')) == '3'
    assert "'message': 'ok'" in str(http.Organization('tok', 'n', 'w', 1))
