import pytest
import responses
from responses import matchers
from requests.exceptions import ConnectionError as ReqConnectionError, Timeout

from pindo_cli.client import PindoClient, PindoClientException, _extract_message


@pytest.fixture
def client():
    return PindoClient(token='tok')


def test_token_and_refresh(mocked, client, url):
    mocked.get(url('/users/token'), json={'token': 'T1'})
    mocked.get(url('/users/refresh/token'), json={'token': 'T2'})
    assert client.get_token('u', 'p') == 'T1'
    assert client.refresh_token('u', 'p') == 'T2'
    # basic auth, no bearer header on auth endpoints
    req = mocked.calls[0].request
    assert req.headers['Authorization'].startswith('Basic ')
    assert 'pindo-cli/' in req.headers['User-Agent']


def test_bearer_header_on_authenticated_calls(mocked, client, url):
    mocked.get(url('/wallets/self'), json={'amount': 12.5, 'currency': 'USD'})
    assert client.balance() == 12.5
    assert mocked.calls[0].request.headers['Authorization'] == 'Bearer tok'


def test_missing_token_raises_before_request(mocked):
    with pytest.raises(PindoClientException) as exc:
        PindoClient().wallet()
    assert 'No API token' in str(exc.value)
    assert len(mocked.calls) == 0


def test_http_error_uses_api_message(mocked, client, url):
    mocked.post(url('/users/register'), json={'message': 'username already exists'}, status=409)
    with pytest.raises(PindoClientException) as exc:
        client.register('u', 'e@x.io', 'p')
    assert exc.value.status_code == 409
    assert exc.value.message == 'username already exists'
    assert str(exc.value) == 'username already exists (HTTP 409)'


def test_http_error_default_messages(mocked, client, url):
    mocked.get(url('/wallets/self'), body='', status=401)
    with pytest.raises(PindoClientException) as exc:
        client.wallet()
    assert 'Unauthorized' in exc.value.message
    assert exc.value.status_code == 401


def test_non_json_body(mocked, client, url):
    mocked.get(url('/wallets/self'), body='<html>oops</html>', status=200)
    with pytest.raises(PindoClientException) as exc:
        client.wallet()
    assert 'non-JSON' in exc.value.message


def test_missing_key_in_response(mocked, client, url):
    mocked.get(url('/users/token'), json={'nope': 1})
    with pytest.raises(PindoClientException) as exc:
        client.get_token('u', 'p')
    assert 'missing "token"' in exc.value.message


def test_network_errors(mocked, client, url):
    mocked.get(url('/wallets/self'), body=ReqConnectionError('boom'))
    with pytest.raises(PindoClientException) as exc:
        client.wallet()
    assert 'Could not connect' in exc.value.message

    mocked.replace(responses.GET, url('/wallets/self'), body=Timeout())
    with pytest.raises(PindoClientException) as exc:
        client.wallet()
    assert 'timed out' in exc.value.message


def test_send_sms_and_org_and_recover(mocked, client, url):
    mocked.post(url('/v1/sms/'), json={'status': 'sent', 'sms_id': 'out_1'})
    mocked.put(url('/orgs/self'), json={'message': 'updated'})
    mocked.put(url('/users/recovery/RT'), json={'message': 'password changed'})
    mocked.post(url('/users/forgot'), json={'message': 'sent'})

    assert client.send_sms('+250', 'hi', 'Pindo')['status'] == 'sent'
    assert client.update_organization('Pindo', 'https://x', 3) == {'message': 'updated'}
    assert client.recover_password('RT', 'a', 'a') == 'password changed'
    assert client.forgot_password('e@x.io') == {'message': 'sent'}

    body = mocked.calls[1].request.body
    assert b'"sms_retries": 3' in body


def test_get_page_shapes(mocked, client, url):
    mocked.get(url('/list1'), json={'items': [{'id': 1}], 'pages': {'page': 1}})
    mocked.get(url('/list2'), json=[{'id': 2}])
    mocked.get(url('/list3'), json={'foo': 'bar'})
    assert client.get_page('/list1') == ([{'id': 1}], {'page': 1})
    assert client.get_page('/list1', items_key='items')[0] == [{'id': 1}]
    assert client.get_page('/list2') == ([{'id': 2}], {})
    assert client.get_page('/list3') == ([], {})


def test_iter_pages_follows_next_url(mocked, client, url):
    page1 = {
        'inbound_sms': [{'id': 1}, {'id': 2}],
        'pages': {'next_url': url('/v1/sms/inbounds?page=2&per_page=2')},
    }
    page2 = {'inbound_sms': [{'id': 3}], 'pages': {'next_url': None}}
    mocked.get(url('/v1/sms/inbounds'), json=page1,
               match=[matchers.query_param_matcher({'per_page': '2'})])
    mocked.get(url('/v1/sms/inbounds'), json=page2,
               match=[matchers.query_param_matcher({'page': '2', 'per_page': '2'})])
    ids = [i['id'] for i in client.iter_pages('/v1/sms/inbounds', params={'per_page': 2})]
    assert ids == [1, 2, 3]
    assert len(mocked.calls) == 2
    # next_url is followed verbatim; the original params are not re-sent
    assert mocked.calls[1].request.url == url('/v1/sms/inbounds?page=2&per_page=2')


def test_iter_pages_max_pages(mocked, client, url):
    mocked.get(url('/v1/sms/inbounds'), json={
        'inbound_sms': [{'id': 1}, {'id': 2}],
        'pages': {'next_url': url('/v1/sms/inbounds?page=2')},
    })
    ids = [i['id'] for i in client.iter_pages('/v1/sms/inbounds', max_pages=1)]
    assert ids == [1, 2]
    assert len(mocked.calls) == 1


def test_iter_pages_stops_on_empty_page(mocked, client, url):
    mocked.get(url('/x'), json={'rows': [], 'pages': {'next_url': url('/x?page=2')}})
    assert list(client.iter_pages('/x')) == []
    assert len(mocked.calls) == 1


def test_extract_message_variants():
    assert _extract_message({'message': 'm'}, 'd') == 'm'
    assert _extract_message({'error': 'e'}, 'd') == 'e'
    assert _extract_message({'message': {'username': 'taken'}}, 'd') == 'username: taken'
    assert _extract_message({'other': 1}, 'd') == '{"other": 1}'
    assert _extract_message('plain text', 'd') == 'plain text'
    assert _extract_message('', 'd') == 'd'
    assert _extract_message(None, 'd') == 'd'


def test_url_building():
    c = PindoClient(base_url='https://x.example/')
    assert c.url('/a') == 'https://x.example/a'
    assert c.url('/users/recovery/{token}', token='T') == 'https://x.example/users/recovery/T'
    assert c.url('https://other.example/full') == 'https://other.example/full'
