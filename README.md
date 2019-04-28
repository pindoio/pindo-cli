# pindo-cli

![travis](https://travis-ci.org/pindo-io/pindo-cli.svg?branch=master)
![fury](https://badge.fury.io/py/pindo-cli.svg)
![pipy](https://pypip.in/d/pindo-cli/badge.png)

## Installation

Install from PyPi using [pip](http://www.pip-installer.org/en/latest), a package manager for Python.

`pip3 install pindo-cli`

Don't have pip installed? Try installing it, by running this from the command line:

`$ curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python`

`python setup.py install`

You may need to run the above commands with `sudo`.

## Getting Started

Once you're have install **Pindo CLI** you're ready to go.

`pindo --help`

## Create an account

For creating a Pindo account you need to provide your username, email, and password

`pindo register`

## Token

Requesting a token require you to provide your username and password

`pindo token`

Refresh your token

`pindo refresh-token`

## Send a test message

Sending a test message will require you providing the requested token, a receiver, the message your want to send, and also the sender id.

`pindo sms`

## API Usage

The `pindo api` needs your Token. You can either pass the token directly to the constructor (see the code below) or via environment variables.

```python

# python

import requests

token='kbkcmbkcmbkcbc9ic9vixc9vixc9v'
headers = {'Authorization': 'Bearer ' + token}
data = {'to' : '+250700000000', 'text' : 'Hello from Pindo', 'sender' : 'Pindo'}

url = 'http://api.pindo.io/v1/sms/'
response = requests.post(url, json=data, headers=headers)
print(response)
print(response.json())

```

```javascript
// NodeJS

var request = require("request");
data = { to: "+250700000000", text: "Hello from Pindo", sender: "Pindo" };

var options = {
  method: "POST",
  body: data,
  json: true,
  url: "http://api.pindo.io/v1/sms/",
  headers: {
    Authorization: "Bearer your-token"
  }
};

function callback(error, response, body) {
  if (!error && response.statusCode == 200) {
    console.log(body);
  }
}
//call the request

request(options, callback);
```
