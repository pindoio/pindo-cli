import requests
from requests.auth import HTTPBasicAuth


class PindoClientException(Exception):
    pass


class Token:
    """
    Request a Pindo Token
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.url = 'http://188.166.168.177/users/token'

    def __str__(self):
        # request
        r = requests.get(
            self.url, auth=HTTPBasicAuth(self.username, self.password))
        if r.status_code == 200:
            return '{}'.format(r.json()['token'])
        raise PindoClientException('Pindo API authentication failed.')


class Register:
    """
    Register a new account
    """
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.url = 'http://188.166.168.177/users/registration'

    def __str__(self):
        payload = {
            'username': self.username,
            'email': self.email,
            'password': self.password
        }
        r = requests.post(self.url, json=payload)
        if r.status_code == 201:
            return ' Account successfully created'
        raise PindoClientException('Pindo API registration failed.')
