import urllib.request
import json

token = "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"
url = "https://api.github.com/user"
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

req = urllib.request.Request(url, headers=headers, method="GET")

with urllib.request.urlopen(req) as response:
    res_data = json.loads(response.read().decode())
    print(res_data.get("login"))
