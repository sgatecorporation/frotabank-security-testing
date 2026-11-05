import requests, uuid, json, sys

BASE = "https://api.c03.frotabank.com.br"
HEADERS = {
    "x-app-name": "frotabank",
    "x-app-platform": "android",
    "x-app-finger-print": "a1b2c3d4e5f6",
    "x-app-build-number": "87",
    "x-app-version": "1.15.0",
    "x-app-device-model": "SM-G998B",
    "content-type": "application/json",
    "user-agent": "okhttp/4.11.0",
}

def h():
    d = HEADERS.copy()
    d["x-correlation-id"] = str(uuid.uuid4())
    return d

cpf = input("CPF (so numeros): ").strip()
phone = input("Telefone (+5511...): ").strip()

print("\n[1] Checando CPF (com document)...")
r = requests.post(f"{BASE}/v2/credentials/exists", json={"username": cpf, "document": cpf}, headers=h())
print(f"  {r.status_code}: {r.text}")

print("\n[2] Whitelist...")
r = requests.get(f"{BASE}/v2/whitelist/validate-document/{cpf}", headers=h())
print(f"  {r.status_code}: {r.text}")

print("\n[3a] Enviando SMS (verificationCodeType=sms)...")
r = requests.post(f"{BASE}/v2/verification-code/send", json={"phone": phone, "verificationCodeType": "sms"}, headers=h())
print(f"  {r.status_code}: {r.text}")

if r.status_code != 200:
    print("\n[3b] Tentando verificationCodeType=SMS...")
    r = requests.post(f"{BASE}/v2/verification-code/send", json={"phone": phone, "verificationCodeType": "SMS"}, headers=h())
    print(f"  {r.status_code}: {r.text}")

if r.status_code != 200:
    print("\n[3c] Tentando verificationCodeType=whatsapp...")
    r = requests.post(f"{BASE}/v2/verification-code/send", json={"phone": phone, "verificationCodeType": "whatsapp"}, headers=h())
    print(f"  {r.status_code}: {r.text}")

code = input("\nCodigo recebido: ").strip()
print("\n[4] Confirmando...")
r = requests.post(f"{BASE}/phone/confirmation", json={"phone": phone, "code": code}, headers=h())
print(f"  {r.status_code}: {r.text}")
try:
    data = r.json()
    sid = data.get("sessionId")
    if sid:
        print(f"\n*** SESSION ID: {sid} ***")
except:
    print("  (nao eh JSON)")
