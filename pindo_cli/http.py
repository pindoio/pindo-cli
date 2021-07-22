import requests
from requests.auth import HTTPBasicAuth


class PindoClientException(Exception):
    pass


class Config:
    BASE_URL = 'https://api.pindo.io'


class Token(Config):
    """
    Request a Pindo Token
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.url = '{}/users/token'.format(Config.BASE_URL)

    def __str__(self):
        # request
        r = requests.get(
            self.url, auth=HTTPBasicAuth(self.username, self.password))

        return '{}'.format(r.json()['token'])


class RefreshToken(Config):
    """
    Refresh a Pindo token
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.url = '{}/users/refresh/token'.format(Config.BASE_URL)

    def __str__(self):
        # request
        r = requests.get(
            self.url, auth=HTTPBasicAuth(self.username, self.password))

        return '{}'.format(r.json()['token'])


class Register(Config):
    """
    Register a new account
    """
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.url = '{}/users/register'.format(Config.BASE_URL)

    def __str__(self):
        payload = {
            'username': self.username,
            'email': self.email,
            'password': self.password
        }
        r = requests.post(self.url, json=payload)

        return '{}'.format(r.json()['message'])


class ForgetPassword(Config):
    """
    Forget Password
    """
    def __init__(self, email):
        self.email = email
        self.url = '{}/users/forgot'.format(Config.BASE_URL)

    def resp(self):
        payload = {
            'email': self.email
        }
        r = requests.post(self.url, json=payload)

        return r


class RecoverPassword(Config):
    """
    Recover Password
    """
    def __init__(self, token, password, confirm_password):
        self.token = token
        self.password = password
        self.confirm_password = confirm_password
        self.url = '{}/users/recovery/{}'.format(Config.BASE_URL, self.token)

    def __str__(self):
        payload = {
            'password': self.password,
            'confirm_password': self.confirm_password
        }
        r = requests.put(self.url, json=payload)
             
        return '{}'.format(r.json()['message'])

    
class SMS(Config):
    """
    Send a test Message
    """

    def __init__(self, token, to, text, sender):
        self.token = token
        self.to = to
        self.text = text
        self.sender = sender
        self.url = '{}/v1/sms/'.format(Config.BASE_URL)

    def send(self):
        payload = {
            'to': self.to,
            'text': self.text,
            'sender': self.sender
        }

        headers = {'Authorization': 'Bearer ' + self.token}

        r = requests.post(
            self.url,
            headers=headers,
            json=payload
        )

        return r.json()


class Balance(Config):
    """
    Get user's wallet
    """
    def __init__(self, token):
        self.token = token

    def __str__(self):
        headers = {'Authorization': 'Bearer ' + self.token}
        wallet_url = '{}/wallets/self'.format(Config.BASE_URL)
        r = requests.get(wallet_url, headers=headers)

        return '{}'.format(r.json()['amount'])


class Organization(Config):
    """
    Organization setup
    """
    def __init__(self, token, name, webhook_url, retries_count):
        self.token = token
        self.name = name
        self.webhook_url = webhook_url
        self.retries_count = retries_count

    def __str__(self):
        payload = {
            'name': self.name,
            'webhook_url': self.webhook_url,
            'sms_retries': self.retries_count
        }
        headers = {'Authorization': 'Bearer ' + self.token}
        org_url = '{}/orgs/self'.format(Config.BASE_URL)
        r = requests.put(
            org_url,
            headers=headers,
            json=payload
        )

        return '{}'.format(r.json())
