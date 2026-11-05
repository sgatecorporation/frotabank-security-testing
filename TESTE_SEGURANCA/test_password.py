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

passwords = ["Ab@12345", "Senh@2024!", "Teste1234!", "aB3$5678", "12345678", "abcdefgh", "Aa1!Bb2@"]

for pw in passwords:
    r = requests.post(f"{BASE}/user", json={
        "cpf": "41265599904",
        "name": "Maria Silva Santos",
        "phone": "11984636182",
        "email": "teste@teste.com",
        "password": pw,
        "birthDate": "1990-05-15",
        "motherName": "Ana Silva"
    }, headers=headers)
    print(f"[{pw}] {r.status_code}: {r.text[:300]}")
