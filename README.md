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

```bash

# cURL

curl -X POST \
http://api.pindo.io/v1/sms/ \
-H 'Accept: */*' \
-H 'Authorization: Bearer your-token' \
-H 'Content-Type: application/json' \
-d '{
"to" : "+250785383100", 
"text" : "Hello from Pindo",
"sender" : "Pindo"
}'
```

```python

# python

import requests

token='your-token'
headers = {'Authorization': 'Bearer ' + token}
data = {'to' : '+250xxxxxxxx', 'text' : 'Hello from Pindo', 'sender' : 'Pindo'}

url = 'http://api.pindo.io/v1/sms/'
response = requests.post(url, json=data, headers=headers)
print(response)
print(response.json())

```

```javascript
// NodeJS

var request = require("request");
data = { to: "+250xxxxxxxx", text: "Hello from Pindo", sender: "Pindo" };

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

```java

// Java

OkHttpClient client = new OkHttpClient();

MediaType mediaType = MediaType.parse("application/json");
RequestBody body = RequestBody.create(mediaType, "{"to" : "+250xxxxxxxx", "text" : "Hello from Pindo","sender" : "Pindo"}");
Request request = new Request.Builder()
.url("http://api.pindo.io/v1/sms/")
.post(body)
.addHeader("Content-Type", "application/json")
.addHeader("Authorization", "Bearer your-token")
.build();
Response response = client.newCall(request).execute();
```


```php

// PHP

$request = new HttpRequest();
$request->setUrl('http://api.pindo.io/v1/sms/');
$request->setMethod(HTTP_METH_POST);

$request->setHeaders(array(
'Authorization' => 'Bearer your-token',
'Content-Type' => 'application/json'
));

$request->setBody('{
"to" : "+250xxxxxxxx", 
"text" : "Hello from Pindo",
"sender" : "Pindo"
}');

try {
$response = $request->send();

echo $response->getBody();
} catch (HttpException $ex) {
echo $ex;
}
```

```Go

// GO

package main

import (
"fmt"
"strings"
"net/http"
"io/ioutil"
)

func main() {

url := "http://api.pindo.io/v1/sms/"

payload := strings.NewReader("{"to" : "+250xxxxxxxx", "text" : "Hello from Pindo","sender" : "Pindo"}")

req, _ := http.NewRequest("POST", url, payload)

req.Header.Add("Content-Type", "application/json")
req.Header.Add("Authorization", "Bearer your-token")

res, _ := http.DefaultClient.Do(req)

defer res.Body.Close()
body, _ := ioutil.ReadAll(res.Body)

fmt.Println(res)
fmt.Println(string(body))

}
```
