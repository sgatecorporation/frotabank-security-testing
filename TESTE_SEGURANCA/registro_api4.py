import requests, uuid, json

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

phone = input("Telefone (+55...): ").strip()
print("Receber codigo por:")
print("  1 - SMS")
print("  2 - WhatsApp")
canal = input("Escolha (1 ou 2): ").strip()

# Testar varias opcoes de enum
tipos = ["WHATSAPP", "whatsapp", "Whatsapp", "WAPP"] if canal == "2" else ["SMS", "sms", "Sms"]

for t in tipos:
    print(f"\n[*] Tentando verificationCodeType={t}...")
    r = requests.post(f"{BASE}/v2/verification-code/send", json={"phone": phone, "verificationCodeType": t}, headers=h())
    print(f"  {r.status_code}: {r.text}")
    if r.status_code == 200:
        print(f"  *** FUNCIONOU com: {t} ***")
        break
    # Tentar tambem como "type"
    print(f"[*] Tentando type={t}...")
    r = requests.post(f"{BASE}/v2/verification-code/send", json={"phone": phone, "type": t}, headers=h())
    print(f"  {r.status_code}: {r.text}")
    if r.status_code == 200:
        print(f"  *** FUNCIONOU com type={t} ***")
        break

if r.status_code == 200:
    code = input("\nCodigo recebido: ").strip()
    print("\n[*] Confirmando codigo...")
    r = requests.post(f"{BASE}/phone/confirmation", json={"phone": phone, "code": code}, headers=h())
    print(f"  {r.status_code}: {r.text}")
    try:
        data = r.json()
        sid = data.get("sessionId")
        if sid:
            print(f"\n*** SESSION ID: {sid} ***")
            cpf = input("\nAgora digite o CPF: ").strip()
            hh = h()
            hh["sessionid"] = sid
            print("\n[*] Validando CPF...")
            r = requests.post(f"{BASE}/user/cpf-validation", json={"cpf": cpf}, headers=hh)
            print(f"  {r.status_code}: {r.text}")
    except:
        print("  (resposta nao eh JSON)")
else:
    print("\nNenhum enum funcionou. Precisamos capturar o valor exato do app.")
