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
        try:
            r = requests.get(
                self.url, auth=HTTPBasicAuth(self.username, self.password))
            return '{}'.format(r.json())
        except:
            return 'Something went wrong try again.'


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
        return '{}'.format(r.json())


class SMS:
    """
        Send a test Message
    """

    def __init__(self, token, to, text, sender):
        self.token = token
        self.to = to
        self.text = text 
        self.sender = sender
        self.url = 'http://188.166.168.177/sms/'

    def __str__(self):
        payload = {
            'to': self.to,
            'text': self.text,
            'sender': self.sender
        }
        r = requests.post(
            self.url,
            auth=HTTPBasicAuth(self.token, ''),
            json=payload
        )
        return '{}'.format(r.json())

