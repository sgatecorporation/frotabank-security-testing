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

# Teste 1: aceite de termos
print("=== TESTE: v2/terms/acceptance ===")
r1 = requests.post(f"{BASE}/v2/terms/acceptance", json={
    "tokens": [
        "fa34f05d-928b-4738-b430-c3571acefd9c",
        "933fa7e1-28da-436e-b767-d568f07b2bcb"
    ]
}, headers=headers)
print(f"  {r1.status_code}: {r1.text[:500]}")

# Teste 2: person-details
print("\n=== TESTE: v2/person-details ===")
r2 = requests.post(f"{BASE}/v2/person-details", json={
    "fullName": "Maria Silva Santos",
    "birthDate": "1990-05-15",
    "motherName": "Ana Silva",
    "email": "teste@teste.com",
    "professionId": 11,
    "address": {
        "zipCode": "80420-000",
        "street": "Rua Comendador Araujo",
        "number": "100",
        "complement": "",
        "neighborhood": "Centro",
        "city": "Curitiba",
        "state": "PR"
    }
}, headers=headers)
print(f"  {r2.status_code}: {r2.text[:500]}")

# Teste 3: user/documents/upload (selfie) com essa sessao
print("\n=== TESTE: selfie upload ===")
h2 = {k:v for k,v in headers.items() if k != "content-type"}
img = r"C:\Users\Acer\AppData\Local\Temp\claude\C--Users-Acer-Documents-Frota\d74a258b-2478-41ad-8c0e-554cc53b8db0\images\42.jpg"
with open(img, "rb") as f:
    r3 = requests.post(f"{BASE}/user/documents/upload", headers=h2,
        files={"file": ("selfie.jpg", f, "image/jpeg")})
print(f"  {r3.status_code}: {r3.text[:500]}")
