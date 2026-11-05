"""Cria senha (credential) para conta aprovada - envia codigo e chama POST /v2/auth/credential"""
import requests, uuid, time, jwt, sys
from curl_cffi import requests as curl_requests

BASE = "https://api.c03.frotabank.com.br"
CORR = uuid.uuid4().hex
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

CPF = sys.argv[1] if len(sys.argv) > 1 else "41265599904"
PHONE = sys.argv[2] if len(sys.argv) > 2 else "11984636182"
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else "Senh@2024!"

http = requests.Session()
http.timeout = 15
http2 = curl_requests.Session(impersonate="chrome120", timeout=30)

def pinning_token():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")

def h(sid=None):
    return {
        "x-app-name": "br.com.frotabank.app", "x-app-platform": "android",
        "x-app-finger-print": "63201bd095adc55e", "x-app-build-number": "2026012801",
        "x-app-version": "18.10.18",
        "x-app-device-model": "google / goldfish_x86 / generic_x86_arm / ranchu",
        "content-type": "application/json", "user-agent": "okhttp/4.11.0",
        "accept": "application/json, text/plain, */*", "accept-encoding": "gzip",
        "x-correlation-id": CORR, "sessionId": sid or str(uuid.uuid4()),
        "sg-signature": pinning_token(),
    }

phone_fmt = f"({PHONE[:2]}) {PHONE[2:7]}-{PHONE[7:]}"

print("=" * 60)
print(f"CRIAR SENHA - CPF {CPF}")
print(f"Phone: {phone_fmt} | Senha: {PASSWORD}")
print("=" * 60)

# 1) Verificar se credential ja existe
print("\n[1] Verificando /v2/credentials/exists...")
r = http2.post(f"{BASE}/v2/credentials/exists", json={"document": CPF}, headers=h())
print(f"  {r.status_code} | {r.text[:200]}")

# === FASE 1: Obter sessionId (codigo onboarding) ===
print("\n[2] Enviando codigo ONBOARDING (pra pegar sessionId)...")
for ph in [phone_fmt, PHONE]:
    body = {"phone": ph, "verificationCodeType": "onboarding",
            "deliveryMethod": "whatsapp", "document": CPF}
    r = http.post(f"{BASE}/v2/verification-code/send", json=body, headers=h())
    if r.status_code == 200:
        print(f"  Enviado via WhatsApp (onboarding)!")
        break

code1 = input("\n>>> CODIGO 1 (onboarding) recebido no WhatsApp: ").strip()

print(f"\n[3] Validando codigo onboarding...")
sid = None
for ph in [phone_fmt, PHONE]:
    try:
        r = http2.post(f"{BASE}/phone/confirmation",
            json={"phone": ph, "verificationCode": code1}, headers=h(), timeout=30)
        fmt_l = "fmt" if "(" in ph else "raw"
        print(f"  {fmt_l}: {r.status_code} | {r.text[:200]}")
        if r.status_code == 200:
            data = r.json()
            sid = data.get("sessionId")
            if sid:
                print(f"  sessionId: {sid}")
                break
    except Exception as e:
        print(f"  TIMEOUT: {e}")

if not sid:
    print("  ERRO: Nao conseguiu sessionId!")
    sys.exit(1)

# === FASE 2: Enviar codigo createCredential ===
print(f"\n[4] Enviando codigo CREATE_CREDENTIAL...")
for ph in [phone_fmt, PHONE]:
    body = {"phone": ph, "verificationCodeType": "createCredential",
            "deliveryMethod": "whatsapp", "document": CPF}
    r = http.post(f"{BASE}/v2/verification-code/send", json=body, headers=h(sid))
    if r.status_code == 200:
        print(f"  Enviado via WhatsApp (createCredential)!")
        break

code2 = input("\n>>> CODIGO 2 (createCredential) recebido no WhatsApp: ").strip()

# === FASE 3: Criar credential ===
print(f"\n[5] POST /v2/auth/credential...")
cred_body = {"document": CPF, "password": PASSWORD, "verificationCode": code2}
print(f"  Payload: document={CPF}, password=***, verificationCode={code2}")

r = http2.post(f"{BASE}/v2/auth/credential", json=cred_body, headers=h(sid))
print(f"  {r.status_code} | {r.text[:500]}")

if r.status_code in (200, 201):
    print("\n  SENHA CRIADA COM SUCESSO!")

    # 5) Tentar login
    print("\n[4] Login...")
    r2 = http2.post(f"{BASE}/v2/auth/multifactor-login",
        json={"document": CPF, "password": PASSWORD}, headers=h())
    print(f"  {r2.status_code} | {r2.text[:500]}")
    if r2.status_code == 200:
        data = r2.json()
        token = data.get("token") or data.get("accessToken")
        if token:
            print(f"\n  BEARER TOKEN: {token[:80]}...")
else:
    print(f"\n  ERRO ao criar senha: {r.status_code}")

print("\n" + "=" * 60)
print("FIM")
