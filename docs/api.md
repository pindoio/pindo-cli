# Pindo API quick reference

Base URL: `https://api.pindo.io`. Every request needs your API token in an
`Authorization: Bearer <token>` header. You can get a token with
`pindo login` or `pindo token`.

- [Send SMS](#send-sms)
- [Response codes](#response-codes)
- [Delivery reports (DLR webhook)](#delivery-reports-dlr-webhook)
- [Inbound SMS](#inbound-sms)
- [PindoVerify (one-time PINs)](#pindoverify-one-time-pins)

## Send SMS

| | Endpoint | Body |
|---|---|---|
| Single | `POST /v1/sms/` | `{"to": "+250781234567", "text": "Hello from Pindo", "sender": "Pindo"}` |
| Bulk | `POST /v1/sms/bulk` | `{"recipients": [{"phonenumber": "+250781234567", "name": "Remy"}], "text": "Hello @contact.name", "sender": "Pindo"}` |

In bulk messages, `@contact.name` is replaced with each recipient's `name`.

A successful send returns `201`:

```json
{
  "bonus": 0.0,
  "discount": 0.4,
  "item_count": 1,
  "item_price": 0.006,
  "remaining_balance": 71421.953,
  "self_url": "https://api.pindo.io/v1/sms/out_sms_01H7DJEJ1YZKTNT8EDXY2C7YG9",
  "sms_id": "out_sms_01H7DJEJ1YZKTNT8EDXY2C7YG9",
  "status": "sent",
  "to": "+250781234567",
  "total_cost": 0.006
}
```

### cURL

```bash
# Single SMS
curl -X POST https://api.pindo.io/v1/sms/ \
  -H "Authorization: Bearer $PINDO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to": "+250781234567", "text": "Hello from Pindo", "sender": "Pindo"}'

# Bulk SMS
curl -X POST https://api.pindo.io/v1/sms/bulk \
  -H "Authorization: Bearer $PINDO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipients": [{"phonenumber": "+250781234567", "name": "Remy"}],
       "text": "Hello @contact.name, welcome to Pindo", "sender": "Pindo"}'
```

### Python

```python
import os

import requests

headers = {"Authorization": f"Bearer {os.environ['PINDO_TOKEN']}"}

# Single SMS
resp = requests.post(
    "https://api.pindo.io/v1/sms/",
    json={"to": "+250781234567", "text": "Hello from Pindo", "sender": "Pindo"},
    headers=headers,
    timeout=30,
)
resp.raise_for_status()
print(resp.json())

# Bulk SMS
resp = requests.post(
    "https://api.pindo.io/v1/sms/bulk",
    json={
        "recipients": [{"phonenumber": "+250781234567", "name": "Remy"}],
        "text": "Hello @contact.name, welcome to Pindo",
        "sender": "Pindo",
    },
    headers=headers,
    timeout=30,
)
print(resp.json())
```

### Node.js (18+, built-in `fetch`)

```javascript
const res = await fetch("https://api.pindo.io/v1/sms/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.PINDO_TOKEN}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ to: "+250781234567", text: "Hello from Pindo", sender: "Pindo" }),
});
console.log(res.status, await res.json());
```

### PHP

```php
<?php
$ch = curl_init('https://api.pindo.io/v1/sms/');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . getenv('PINDO_TOKEN'),
        'Content-Type: application/json',
    ],
    CURLOPT_POSTFIELDS => json_encode([
        'to' => '+250781234567',
        'text' => 'Hello from Pindo',
        'sender' => 'Pindo',
    ]),
]);
$response = curl_exec($ch);
curl_close($ch);
echo $response;
```

### Ruby

```ruby
require 'net/http'
require 'json'

uri = URI('https://api.pindo.io/v1/sms/')
req = Net::HTTP::Post.new(uri)
req['Authorization'] = "Bearer #{ENV.fetch('PINDO_TOKEN')}"
req['Content-Type'] = 'application/json'
req.body = { to: '+250781234567', text: 'Hello from Pindo', sender: 'Pindo' }.to_json

res = Net::HTTP.start(uri.host, uri.port, use_ssl: true) { |http| http.request(req) }
puts res.body
```

### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
)

func main() {
	body, _ := json.Marshal(map[string]string{
		"to": "+250781234567", "text": "Hello from Pindo", "sender": "Pindo",
	})
	req, _ := http.NewRequest("POST", "https://api.pindo.io/v1/sms/", bytes.NewReader(body))
	req.Header.Set("Authorization", "Bearer "+os.Getenv("PINDO_TOKEN"))
	req.Header.Set("Content-Type", "application/json")

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer res.Body.Close()
	out, _ := io.ReadAll(res.Body)
	fmt.Println(res.Status, string(out))
}
```

### Java (11+, `java.net.http`)

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

String json = """
    {"to": "+250781234567", "text": "Hello from Pindo", "sender": "Pindo"}
    """;
HttpRequest request = HttpRequest.newBuilder(URI.create("https://api.pindo.io/v1/sms/"))
    .header("Authorization", "Bearer " + System.getenv("PINDO_TOKEN"))
    .header("Content-Type", "application/json")
    .POST(HttpRequest.BodyPublishers.ofString(json))
    .build();
HttpResponse<String> response =
    HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
System.out.println(response.statusCode() + " " + response.body());
```

### C# (.NET 6+)

```csharp
using System.Net.Http.Headers;
using System.Net.Http.Json;

using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization =
    new AuthenticationHeaderValue("Bearer", Environment.GetEnvironmentVariable("PINDO_TOKEN"));

var response = await client.PostAsJsonAsync("https://api.pindo.io/v1/sms/",
    new { to = "+250781234567", text = "Hello from Pindo", sender = "Pindo" });
Console.WriteLine($"{(int)response.StatusCode} {await response.Content.ReadAsStringAsync()}");
```

## Response codes

| Code | Text | Meaning |
|---|---|---|
| 201 | sent | Successfully sent |
| 401 | unauthorized | Missing, invalid or expired token |
| 404 | not found | Invalid resource URI |
| 409 | conflict | Number is from an unsupported country |
| 409 | conflict | Number is from an unsupported telco |
| 409 | conflict | Wrong phone number format |

## Delivery reports (DLR webhook)

Set your webhook URL with `pindo org --webhook-url https://example.com/dlr`
(or in the dashboard). Pindo then `POST`s a delivery report for each message:

```json
{
  "status": "DELIVRD",
  "sms_id": 1058918,
  "modified_at": "24-07-2020, 23:35:32",
  "retries_count": 0
}
```

## Inbound SMS

Inbound messaging gives you two-way SMS. After you set a webhook URL in the
Pindo dashboard, every message sent to your short or long code is `POST`ed to it:

```json
{
  "from": "+250781234567",
  "to": "7878",
  "created_at": "24-07-2020, 23:35:32",
  "sms_id": 1058918,
  "text": "Hello from Pindo",
  "telco": "MTN"
}
```

`GET /v1/sms/inbounds?page=1&per_page=20` lists received messages. Responses
are paginated: follow `pages.next_url` until it is `null`.

```json
{
  "inbound_sms": [
    {
      "account_id": 11783,
      "conversation_id": null,
      "created_at": "2022-08-05T12:32:42.196907",
      "id": 20,
      "id_smsc": null,
      "inbound_sms_number": "+250781113333",
      "language_id": null,
      "telco_id": null,
      "text": "Hello world !"
    }
  ],
  "pages": {
    "first_url": "https://api.pindo.io/v1/sms/inbounds?page=1&per_page=20",
    "last_url": "https://api.pindo.io/v1/sms/inbounds?page=1&per_page=20",
    "next_url": null,
    "page": 1,
    "pages": 1,
    "per_page": 20,
    "prev_url": null,
    "total": 20
  }
}
```

## PindoVerify (one-time PINs)

PindoVerify sends a PIN to a user's phone and checks that they received it.
Use it for two-factor authentication, password-less sign-in or phone-number
validation.

| Action | Request | Body |
|---|---|---|
| Send a PIN | `POST /v1/sms/verify` | `{"brand": "Pindo", "number": "+250781234567"}` |
| Check a PIN | `POST /v1/sms/verify/check` | `{"code": "752623", "request_id": 4}` |
| PIN status | `GET /v1/sms/verify/status/{request_id}` | |
| Cancel a PIN | `PUT /v1/sms/verify/cancel/{request_id}` | |

Sending a PIN returns a `request_id` to use in the other calls:

```json
{"message": "success", "network": "63510", "remaining_balance": 487.49, "request_id": 4}
```

A successful check returns:

```json
{"message": "success", "remaining_balance": 487.49, "request_id": 4}
```

```bash
# Send a PIN
curl -X POST https://api.pindo.io/v1/sms/verify \
  -H "Authorization: Bearer $PINDO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"brand": "Pindo", "number": "+250781234567"}'

# Check the code the user typed
curl -X POST https://api.pindo.io/v1/sms/verify/check \
  -H "Authorization: Bearer $PINDO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "752623", "request_id": 4}'

# Status / cancel
curl https://api.pindo.io/v1/sms/verify/status/4 -H "Authorization: Bearer $PINDO_TOKEN"
curl -X PUT https://api.pindo.io/v1/sms/verify/cancel/4 -H "Authorization: Bearer $PINDO_TOKEN"
```

```python
import os

import requests

API = "https://api.pindo.io/v1/sms/verify"
headers = {"Authorization": f"Bearer {os.environ['PINDO_TOKEN']}"}

sent = requests.post(
    API, json={"brand": "Pindo", "number": "+250781234567"}, headers=headers, timeout=30
).json()
code = input("Code: ")
check = requests.post(
    f"{API}/check", json={"code": code, "request_id": sent["request_id"]},
    headers=headers, timeout=30,
).json()
print(check)
```
