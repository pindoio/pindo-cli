# pindo-cli

![Tests](https://github.com/pindoio/pindo-cli/workflows/Tests/badge.svg)
![fury](https://badge.fury.io/py/pindo-cli.svg)
![pipy](https://pypip.in/d/pindo-cli/badge.png)

## Installation

Install from PyPi using [pip](http://www.pip-installer.org/en/latest), a package manager for Python.

`pip install pindo-cli`

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
	
A simple Command Line Interface that allows you to authenticate with the Pindo API
	
https://www.pindo.io

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
201 | sent | Successfully sent
401 | unauthorized | unauthorized access
404 | not found | invalid resource URI
409 | conflict | number is from unsupported country
409 | conflict | number is from unsupported telco
409 | conflict | Wrong phone number format

- An example of a successfully sent SMS.

```json
{
    "count": 1,
    "remaining_balance": 3.11,
	"sms_id":"1058918",
    "self_url": "https://api.pindo.io/v1/sms/1058918",
    "sms_items": [
        {
            "id": 1062502,
            "item_price": 0.01,
            "network": "63510",
            "remaining_balance": 3.11,
            "status": "sent",
            "to": "+250785000000"
        }
    ]
}
```

- Pindo Delivery Report (DLR) Webhook Event example `POST` methods

```json
{
    "status": "DELIVRD",
    "sms_id": 1058918,
    "modified_at": "24-07-2020, 23:35:32",
    "retries_count": 0
}

```

## SMS API Usage

The `pindo api` needs your Token. You can either pass the token directly to the constructor (see the code below) or via environment variables.

```bash

# cURL

curl -X POST \
https://api.pindo.io/v1/sms/ \
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

url = 'https://api.pindo.io/v1/sms/'
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
  url: "https://api.pindo.io/v1/sms/",
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
.url("https://api.pindo.io/v1/sms/")
.post(body)
.addHeader("Content-Type", "application/json")
.addHeader("Authorization", "Bearer your-token")
.build();
Response response = client.newCall(request).execute();
```

```php

// PHP

$request = new HttpRequest();
$request->setUrl('https://api.pindo.io/v1/sms/');
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

// cURL

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => "https://api.pindo.io/v1/sms/",
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => "",
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => true,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => "POST",
  CURLOPT_POSTFIELDS =>"{\n\t\"to\" : \"+250781234567\",\n\t\"text\" : \"Test SMS.\",\n\t\"sender\" : \"Pindo\"\n}",
  CURLOPT_HTTPHEADER => array(
    "Authorization: Bearer token",
    "Content-Type: application/json"
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
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

url := "https://api.pindo.io/v1/sms/"

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

var client = new RestClient("https://api.pindo.io/v1/sms/");
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

uri = URI('https://api.pindo.io/v1/sms/')
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
  String url = 'https://api.pindo.io/v1/sms/';
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

## Inbound SMS API Usage

Pindo Inbound messaging allows you to have two-way SMS communication. By quickly setting up a Webhook URL in Pindo's dashboard, you will receive any event on your configured short or long code.

- Pindo Inbound Webhook Event example `POST` methods

```json
{
    "from": "+25078123456",
    "to": "7878",
    "created_at": "24-07-2020, 23:35:32",
    "sms_id": 1058918,
    "text": "Hello from Pindo",
    "telco": "MTN"
}

```
- List All Inbound SMS

```json
{
   "inbound_sms":[
      {
         "account_id":11783,
         "conversation_id":null,
         "created_at":"2022-08-05T12:32:42.196907",
         "id":20,
         "id_smsc":null,
         "inbound_sms_number":"+250781113333",
         "language_id":null,
         "telco_id":null,
         "text":"Hello world !"
      }
   ],
   "pages":{
      "first_url":"http://api.pindo.io/v1/sms/inbounds?page=1&per_page=20",
      "last_url":"http://api.pindo.io/v1/sms/inbounds?page=1&per_page=20",
      "next_url":null,
      "page":1,
      "pages":1,
      "per_page":20,
      "prev_url":null,
      "total":20
   }
}
```


## Verify API Usage

`PindoVerfiy` API lets you send a PIN to a user's phone and validate that they received it. PindoVerfiy can be used for a number of authentication and anti-fraud purposes, such as 2-factor authentication, password-less sign-in, and validating users’ phone numbers.

- An example of a successfully generated PIN.

```json
{
    "message": "success",
    "network": "63510",
    "remaining_balance": 487.49,
    "request_id": 4
}
```

- An example of a successfully verified PIN.

```
{
    "message": "success",
    "remaining_balance": 487.49,
    "request_id": 4
}
```


- Generate a PIN.

```python

# python

import requests
import json

url = "https://api.pindo.io/v1/verify"

payload = json.dumps({
  "brand": "Pindo",
  "number": "+250781234567"
})
headers = {
  'Authorization': 'Bearer your-token',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.json())
```


```javascript

// NodeJS

var request = require('request');
var options = {
  'method': 'POST',
  'url': 'https://api.pindo.io/v1/verify',
  'headers': {
    'Authorization': 'Bearer your-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    "brand": "Pindo",
    "number": "+250781234567"
  })

};
request(options, function (error, response) {
  if (error) throw new Error(error);
  console.log(response.body);
});
```


```java

// Java

OkHttpClient client = new OkHttpClient().newBuilder()
  .build();
MediaType mediaType = MediaType.parse("application/json");
RequestBody body = RequestBody.create(mediaType, "{\n    \"brand\":\"Pindo\",\n    \"number\":\"+250781234567\"\n}\n");
Request request = new Request.Builder()
  .url("https://api.pindo.io/v1/verify")
  .method("POST", body)
  .addHeader("Authorization", "Bearer your-token")
  .addHeader("Content-Type", "application/json")
  .build();
Response response = client.newCall(request).execute();

```

```php

// PHP

<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.pindo.io/v1/verify',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => true,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'POST',
  CURLOPT_POSTFIELDS =>'{
    "brand":"Pindo",
    "number":"+250781234567"
}
',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer your-token',
    'Content-Type: application/json'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;

```


- Verify a PIN

```javascript

// NodeJS

var request = require('request');
var options = {
  'method': 'POST',
  'url': 'https://api.pindo.io/v1/verify/check',
  'headers': {
    'Authorization': 'Bearer your-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    "code": "752623",
    "request_id": 4
  })

};
request(options, function (error, response) {
  if (error) throw new Error(error);
  console.log(response.body);
});

```

- Check PIN status

```javascript

// NodeJS 

var request = require('request');
var options = {
  'method': 'GET',
  'url': 'https://api.pindo.io/v1/verify/status/:request_id',
  'headers': {
    'Authorization': 'Bearer your-token'
  }
};
request(options, function (error, response) {
  if (error) throw new Error(error);
  console.log(response.body);
});

```

- Cancel a PIN

```javascript

// NodeJS

var request = require('request');
var options = {
  'method': 'PUT',
  'url': 'https://api.pindo.io/v1/verify/cancel/:request_id',
  'headers': {
    'Authorization': 'Bearer your-token'
  }
};
request(options, function (error, response) {
  if (error) throw new Error(error);
  console.log(response.body);
});
```
