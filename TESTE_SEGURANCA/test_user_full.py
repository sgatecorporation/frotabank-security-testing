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

# Teste 1: com endereco e profissao
print("=== TESTE 1: campos completos ===")
r = requests.post(f"{BASE}/user", json={
    "cpf": "41265599904",
    "name": "Maria Silva Santos",
    "phone": "11984636182",
    "email": "teste@teste.com",
    "password": "Senh@2024!",
    "birthDate": "1990-05-15",
    "motherName": "Ana Silva",
    "professionId": 11,
    "address": {
        "zipCode": "80420000",
        "street": "Rua Comendador Araujo",
        "number": "100",
        "complement": "",
        "neighborhood": "Centro",
        "city": "Curitiba",
        "state": "PR"
    }
}, headers=headers)
print(f"  {r.status_code}: {r.text[:500]}")

# Teste 2: com termsTokens
print("\n=== TESTE 2: com termsTokens ===")
r = requests.post(f"{BASE}/user", json={
    "cpf": "41265599904",
    "name": "Maria Silva Santos",
    "phone": "11984636182",
    "email": "teste@teste.com",
    "password": "Senh@2024!",
    "birthDate": "1990-05-15",
    "motherName": "Ana Silva",
    "professionId": 11,
    "address": {
        "zipCode": "80420000",
        "street": "Rua Comendador Araujo",
        "number": "100",
        "complement": "",
        "neighborhood": "Centro",
        "city": "Curitiba",
        "state": "PR"
    },
    "termsTokens": [
        "fa34f05d-928b-4738-b430-c3571acefd9c",
        "933fa7e1-28da-436e-b767-d568f07b2bcb"
    ]
}, headers=headers)
print(f"  {r.status_code}: {r.text[:500]}")

# Teste 3: com gender e nationality
print("\n=== TESTE 3: com gender/nationality ===")
r = requests.post(f"{BASE}/user", json={
    "cpf": "41265599904",
    "name": "Maria Silva Santos",
    "phone": "11984636182",
    "email": "teste@teste.com",
    "password": "Senh@2024!",
    "birthDate": "1990-05-15",
    "motherName": "Ana Silva",
    "professionId": 11,
    "gender": "F",
    "nationality": "brasileira",
    "address": {
        "zipCode": "80420000",
        "street": "Rua Comendador Araujo",
        "number": "100",
        "complement": "",
        "neighborhood": "Centro",
        "city": "Curitiba",
        "state": "PR"
    },
    "termsTokens": [
        "fa34f05d-928b-4738-b430-c3571acefd9c",
        "933fa7e1-28da-436e-b767-d568f07b2bcb"
    ]
}, headers=headers)
print(f"  {r.status_code}: {r.text[:500]}")
