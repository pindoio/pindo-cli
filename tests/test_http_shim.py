"""The pre-0.3 ``pindo_cli.http`` classes must keep working."""
from pindo_cli.http import (SMS, Balance, ForgetPassword, Organization, RecoverPassword,
                            RefreshToken, Register, Token)


def test_shim_classes(mocked, url):
    mocked.get(url('/users/token'), json={'token': 'T'})
    mocked.get(url('/users/refresh/token'), json={'token': 'R'})
    mocked.post(url('/users/register'), json={'message': 'created'})
    mocked.post(url('/users/forgot'), json={'message': 'sent'})
    mocked.put(url('/users/recovery/RT'), json={'message': 'done'})
    mocked.post(url('/v1/sms/'), json={'status': 'sent'})
    mocked.get(url('/wallets/self'), json={'amount': 3})
    mocked.put(url('/orgs/self'), json={'message': 'ok'})

    assert str(Token('u', 'p')) == 'T'
    assert str(RefreshToken('u', 'p')) == 'R'
    assert str(Register('u', 'e', 'p')) == 'created'
    assert ForgetPassword('e').resp().status_code == 200
    assert str(RecoverPassword('RT', 'a', 'a')) == 'done'
    assert SMS('tok', '+1', 'hi', 'P').send() == {'status': 'sent'}
    assert str(Balance('tok')) == '3'
    assert "'message': 'ok'" in str(Organization('tok', 'n', 'w', 1))
