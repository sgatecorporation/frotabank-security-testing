import requests

BASE = "https://api.c03.frotabank.com.br"
SID = "4c71d719-d7d0-4a10-8580-4c8a4ec4403f"
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
    "sessionid": SID,
}

# Teste diferentes combinacoes de campos
tests = [
    ("so password", {"password": "Senh@2024!"}),
    ("password+cpf", {"password": "Senh@2024!", "cpf": "41265599904"}),
    ("pw+cpf+phone", {"password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182"}),
    ("pw+cpf+phone+name", {"password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182", "name": "Maria Silva Santos"}),
    ("pw+cpf+phone+fullName", {"password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182", "fullName": "Maria Silva Santos"}),
    ("pw+cpf+phone+name+birth", {"password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182", "name": "Maria Silva Santos", "birthDate": "1990-05-15"}),
    ("pw+cpf+phone+name+birth+mother", {"password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182", "name": "Maria Silva Santos", "birthDate": "1990-05-15", "motherName": "Ana Silva"}),
    ("pw+cpf+phone+name+birth+mother+email", {"password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182", "name": "Maria Silva Santos", "birthDate": "1990-05-15", "motherName": "Ana Silva", "email": "mariasilva@gmail.com"}),
    ("tudo junto camelCase", {
        "password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182",
        "name": "Maria Silva Santos", "birthDate": "1990-05-15", "motherName": "Ana Silva",
        "email": "mariasilva@gmail.com", "professionId": "11",
        "zipCode": "80420000", "street": "Rua Comendador Araujo", "number": "100",
        "complement": "", "neighborhood": "Centro", "city": "Curitiba", "state": "PR",
        "termsTokens": ["fa34f05d-928b-4738-b430-c3571acefd9c", "933fa7e1-28da-436e-b767-d568f07b2bcb"]
    }),
    ("endereco flat", {
        "password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182",
        "name": "Maria Silva Santos", "birthDate": "15/05/1990", "motherName": "Ana Silva",
        "email": "mariasilva@gmail.com", "professionId": 11,
        "zipCode": "80420000", "street": "Rua Comendador Araujo", "number": "100",
        "complement": "", "neighborhood": "Centro", "city": "Curitiba", "state": "PR"
    }),
    ("birth dd/mm/yyyy", {
        "password": "Senh@2024!", "cpf": "41265599904", "phone": "11984636182",
        "name": "Maria Silva Santos", "birthDate": "15/05/1990", "motherName": "Ana Silva",
        "email": "mariasilva@gmail.com"
    }),
]

for label, payload in tests:
    r = requests.post(f"{BASE}/user", json=payload, headers=headers)
    code = r.status_code
    body = r.text[:250]
    flag = ">>>" if code != 500 else ""
    print(f"{flag} [{label}] {code}: {body}")
    print()
