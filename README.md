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

Once you have installed **Pindo CLI** you're ready to go.

```bash 
pindo --help
```
```bash
Usage: pindo [OPTIONS] COMMAND [ARGS]...

  Pindo CLI

  A simple Command Line Interface that allow you to create an account and
  request a token for using Pindo API

Options:
  --debug / --no-debug
  -v, --version         Show the version and exit.
  --help                Show this message and exit.

Commands:
  balance        Get account balance
  org            Organization
  refresh-token  Refresh a Token.
  register       Create a new Pindo account.
  sms            Send a test message
  token          Request a token for using Pindo API.
```
- Send a test message

```bash 
pindo sms --help
```
```bash
Usage: pindo sms [OPTIONS]

  Send a test message

Options:
  --token TEXT   API Token
  --to TEXT      Receiver phone number (+250xxxxxx)
  --text TEXT    Message to send
  --sender TEXT  Sender name
  --help         Show this message and exit.
```

## API Response Code

| **Code** | **Text** | **Meaning** |
---| --- | ---
200 | sent | Successfully sent
401 | unauthorized | unauthorized access
404 | not found | invalid resource URI
409 | conflict | number is from unsupported country
409 | conflict | number is from unsupported telco
409 | conflict | Wrong phone number format

An example of a successfully sent SMS.

```json
{
    "count": 1,
    "remaining_balance": 3.11,
    "self_url": "https://api.pindo.io/v1/sms/1058918",
    "sms_items": [
        {
            "id": 1062502,
            "item_price": 0.01,
            "network": "63510",
            "remaining_balance": 3.11,
            "status": "sent",
            "to": "+250785383100"
        }
    ]
}
```

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
"to" : "+250781234567",
"text" : "Hello from Pindo",
"sender" : "Pindo"
}'
```

```python

# python

import requests

token='your-token'
headers = {'Authorization': 'Bearer ' + token}
data = {'to' : '+250781234567', 'text' : 'Hello from Pindo', 'sender' : 'Pindo'}

url = 'http://api.pindo.io/v1/sms/'
response = requests.post(url, json=data, headers=headers)
print(response)
print(response.json())

```

```javascript
// NodeJS

var request = require("request");
data = { to: "+250781234567", text: "Hello from Pindo", sender: "Pindo" };

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
RequestBody body = RequestBody.create(mediaType, "{"to" : "+250781234567", "text" : "Hello from Pindo","sender" : "Pindo"}");
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
"to" : "+250781234567",
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

payload := strings.NewReader("{"to" : "+250781234567", "text" : "Hello from Pindo","sender" : "Pindo"}")

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

```csharp

// C#

var client = new RestClient("http://api.pindo.io/v1/sms/");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer your-token");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("undefined", "{\n\t\"to\" : \"+250781234567\", \n\t\"text\" : \"Hello from Pindo\",\n\t\"sender\" : \"Pindo\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```ruby
# ruby

require 'net/http'
require 'json'
require 'uri'

data = { to: '+250781234567', text: 'Hello from Pindo', sender: 'Pindo' };

uri = URI('http://api.pindo.io/v1/sms/')
http = Net::HTTP.new(uri.host, uri.port)
req = Net::HTTP::Post.new(uri)
req['Authorization'] = 'Bearer your-token'
req['Content-Type'] = 'application/json'
req.body = data.to_json
http.request(req)

```

```dart

// Dart

import 'dart:convert';
import 'package:http/http.dart' as http;

Future main() async {
  String url = 'http://api.pindo.io/v1/sms/';
  Map<String, String> data = {
    'to': '+250781234567',
    'text': 'Hello from Pindo',
    'sender': 'Pindo'
  };

  Map<String, String> headers = {
    'Authorization': 'Bearer your-token',
    'Content-Type': 'application/json'
  };

  http.Response response = await http.post(
    url,
    body: jsonEncode(data),
    headers: headers,
  );
  print(response.statusCode);
  print(jsonDecode(response.body));
}

```
