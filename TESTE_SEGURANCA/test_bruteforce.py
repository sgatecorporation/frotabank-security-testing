import requests

BASE = "https://api.c03.frotabank.com.br"
SESSION = "678bdf37-c6ac-4b5f-9548-e4890af7876c"
CORR = "c640c437d8bff45059b526752a8dc633"

headers = {
    "x-app-name": "br.com.frotabank.app",
    "x-app-platform": "android",
    "x-app-finger-print": "63201bd095adc55e",
    "x-app-build-number": "2026012801",
    "x-app-version": "18.10.18",
    "x-app-device-model": "google / goldfish_x86 / generic_x86_arm / ranchu",
    "content-type": "application/json",
    "user-agent": "okhttp/4.11.0",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip",
    "x-correlation-id": CORR,
    "sessionid": SESSION,
}

endpoints = [
    ("POST", "/user/registration"),
    ("POST", "/user/create"),
    ("POST", "/user/register"),
    ("POST", "/user/onboarding"),
    ("POST", "/user/complete"),
    ("POST", "/user/save"),
    ("POST", "/user/personal-data"),
    ("POST", "/user/person-details"),
    ("POST", "/onboarding/complete"),
    ("POST", "/onboarding/register"),
    ("POST", "/v2/onboarding/register"),
    ("POST", "/v2/people/register"),
    ("POST", "/v2/user/create"),
    ("POST", "/v2/accounts"),
    ("POST", "/v1/accounts"),
    ("POST", "/terms/acceptance"),
    ("POST", "/user/terms-acceptance"),
    ("PUT", "/user/registration"),
    ("PUT", "/user/personal-data"),
    ("POST", "/user"),
]

payload = {
    "fullName": "Maria Silva Santos",
    "birthDate": "1990-05-15",
    "motherName": "Ana Silva",
    "email": "teste@teste.com",
    "cpf": "41265599904",
    "phone": "11984636182",
    "professionId": 11,
    "address": {
        "zipCode": "80420-000",
        "street": "Rua Comendador Araujo",
        "number": "100",
        "neighborhood": "Centro",
        "city": "Curitiba",
        "state": "PR"
    },
    "termsTokens": [
        "fa34f05d-928b-4738-b430-c3571acefd9c",
        "933fa7e1-28da-436e-b767-d568f07b2bcb"
    ]
}

for method, path in endpoints:
    try:
        if method == "POST":
            r = requests.post(f"{BASE}{path}", json=payload, headers=headers)
        else:
            r = requests.put(f"{BASE}{path}", json=payload, headers=headers)
        status = r.status_code
        body = r.text[:200]
        marker = "***" if status != 404 and status != 403 else ""
        print(f"{marker} {method} {path} -> {status}: {body}")
    except Exception as e:
        print(f"ERR {method} {path}: {e}")
