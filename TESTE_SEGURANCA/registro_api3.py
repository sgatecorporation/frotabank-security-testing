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

cpf = input("CPF: ").strip()
phone = input("Telefone (+55...): ").strip()
canal = input("Receber codigo por (sms/whatsapp): ").strip()

print("\n[1] Checando CPF...")
r = requests.post(f"{BASE}/v2/credentials/exists", json={"username": cpf, "document": cpf}, headers=h())
print(f"  {r.status_code}: {r.text}")

print("\n[2] Whitelist...")
r = requests.get(f"{BASE}/v2/whitelist/validate-document/{cpf}", headers=h())
print(f"  {r.status_code}: {r.text}")

print(f"\n[3] Enviando codigo via {canal}...")
r = requests.post(f"{BASE}/v2/verification-code/send", json={"phone": phone, "verificationCodeType": canal}, headers=h())
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
        hh = h()
        hh["sessionid"] = sid
        print("\n[5] Validando CPF...")
        r = requests.post(f"{BASE}/user/cpf-validation", json={"cpf": cpf}, headers=hh)
        print(f"  {r.status_code}: {r.text}")
    else:
        print("ERRO: sem sessionId")
except:
    print("  (resposta nao eh JSON)")
