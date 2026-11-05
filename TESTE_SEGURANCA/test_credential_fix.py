"""
FIX: Fluxo CORRETO de criacao de credenciais do Frotabank.

O app tem 2 bugs na CreateCredentialVerificationCodeScreen (linhas 1314710-1314730):
  BUG 1: phone = undefined (nunca busca de props/context)
  BUG 2: deliveryMethod = [2,327,4,3,1005,1011] (array de moduleRefs em vez de 'whatsapp')

Este script faz a chamada CORRETA:
  POST /v2/verification-code/send com phone REAL e deliveryMethod='whatsapp'
  Depois POST /v2/auth/credential com {document, password, verificationCode}
"""
import tls_client
import uuid, json, time, jwt, sys

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

CPF = "41265599904"
PHONE = "11984636182"
PASSWORD = "Senh@2024!"
CORR = uuid.uuid4().hex


def pt():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")


def h(sid=None, bearer=None):
    hh = {
        "x-app-name": "br.com.frotabank.app",
        "x-app-platform": "android",
        "x-app-finger-print": "63201bd095adc55e",
        "x-app-build-number": "2026012801",
        "x-app-version": "18.10.18",
        "x-app-device-model": "google / goldfish_x86 / generic_x86_arm / ranchu",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip",
        "x-correlation-id": CORR,
        "sg-signature": pt(),
        "x-device-coords-latitude": "-25.4284",
        "x-device-coords-longitude": "-49.2733",
        "x-device-coords-altitude": "0",
        "x-device-coords-speed": "0",
    }
    if sid:
        hh["sessionId"] = sid
    if bearer:
        hh["Authorization"] = f"Bearer {bearer}"
    return hh


http = tls_client.Session(client_identifier="okhttp4_android_13", random_tls_extension_order=True)

print("=" * 60)
print("FIX: CRIACAO DE CREDENCIAIS (chamada correta)")
print("=" * 60)

# === PASSO 1: Obter sessionId ===
print("\n[1] Obtendo sessionId via onboarding...")
r = http.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h())
print(f"  Envio onboarding: {r.status_code}")
if r.status_code != 200:
    print(f"  ERRO: {r.text[:300]}")
    sys.exit(1)

code1 = input("\n>>> CODIGO ONBOARDING (WhatsApp): ").strip()

r = http.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code1},
    headers=h(), timeout_seconds=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  SessionId: {sid}")

# === PASSO 2: Enviar codigo createCredential CORRETAMENTE ===
print("\n" + "=" * 60)
print("[2] Enviar createCredential com phone e deliveryMethod CORRETOS")
print("    (O app envia phone=undefined e deliveryMethod=[array] - BUGS)")
print("=" * 60)

payload_correto = {
    "verificationCodeType": "createCredential",
    "document": CPF,
    "phone": PHONE,                # FIX BUG 1: phone real em vez de undefined
    "deliveryMethod": "whatsapp",  # FIX BUG 2: 'whatsapp' em vez de [2,327,...]
}
print(f"\n  Payload: {json.dumps(payload_correto, indent=2)}")

r = http.post(f"{BASE}/v2/verification-code/send",
    json=payload_correto,
    headers=h(sid=sid), timeout_seconds=15)
print(f"\n  Status: {r.status_code}")
print(f"  Body: {r.text[:500]}")

if r.status_code != 200:
    print("\n  [!] Tentando sem sessionId...")
    r = http.post(f"{BASE}/v2/verification-code/send",
        json=payload_correto,
        headers=h(), timeout_seconds=15)
    print(f"  Sem session: {r.status_code} | {r.text[:300]}")

    print("\n  [!] Tentando com deliveryMethod='sms'...")
    payload_sms = {**payload_correto, "deliveryMethod": "sms"}
    r = http.post(f"{BASE}/v2/verification-code/send",
        json=payload_sms,
        headers=h(sid=sid), timeout_seconds=15)
    print(f"  SMS: {r.status_code} | {r.text[:300]}")

if r.status_code != 200:
    print("\n  ERRO: Nao conseguiu enviar codigo createCredential")
    sys.exit(1)

print("\n  CODIGO ENVIADO COM SUCESSO!")

code2 = input("\n>>> CODIGO CREDENTIAL (WhatsApp): ").strip()

# === PASSO 3: Criar credenciais ===
print("\n" + "=" * 60)
print("[3] POST /v2/auth/credential - Criar senha")
print("=" * 60)

cred_payload = {
    "document": CPF,
    "password": PASSWORD,
    "verificationCode": code2,
}
print(f"  Payload: {json.dumps(cred_payload, indent=2)}")

# 3a: Com sessionId
print("\n  3a: Com sessionId...")
r = http.post(f"{BASE}/v2/auth/credential",
    json=cred_payload, headers=h(sid=sid), timeout_seconds=15)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:500]}")

cred_ok = r.status_code in (200, 201, 204)

# 3b: Sem sessionId se falhou
if not cred_ok:
    print("\n  3b: Sem sessionId...")
    r = http.post(f"{BASE}/v2/auth/credential",
        json=cred_payload, headers=h(), timeout_seconds=15)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:500]}")
    cred_ok = r.status_code in (200, 201, 204)

if cred_ok:
    print("\n  *** CREDENCIAIS CRIADAS COM SUCESSO! ***")
else:
    print(f"\n  Falhou ({r.status_code}). Possiveis causas:")
    print("    - Conta nao existe (precisa completar cadastro primeiro)")
    print("    - Codigo expirado ou incorreto")
    print("    - Credenciais ja existem para este CPF")

# === PASSO 4: Tentar login ===
print("\n" + "=" * 60)
print("[4] Login")
print("=" * 60)

r = http.post(f"{BASE}/v2/auth/multifactor-login",
    json={"document": CPF, "password": PASSWORD},
    headers=h(sid=sid), timeout_seconds=15)
print(f"  Login: {r.status_code}")
print(f"  Body: {r.text[:500]}")

token = None
if r.status_code == 200:
    data = r.json()
    token = data.get("token", "")
    if token:
        print(f"\n  *** BEARER TOKEN: {token[:80]}... ***")

# === PASSO 5: Se temos Bearer, testar endpoints protegidos ===
if token:
    print("\n" + "=" * 60)
    print("[5] Testar endpoints com Bearer token")
    print("=" * 60)

    endpoints = [
        ("GET", "/v2/personstatus"),
        ("GET", "/v2/persons/documents-upload-lock"),
        ("POST", "/v2/persons/send-document"),
    ]
    for method, ep in endpoints:
        body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"} if "send" in ep else None
        if method == "GET":
            r = http.get(f"{BASE}{ep}", headers=h(sid=sid, bearer=token), timeout_seconds=15)
        else:
            r = http.post(f"{BASE}{ep}", json=body, headers=h(sid=sid, bearer=token), timeout_seconds=15)
        print(f"  {method} {ep}: {r.status_code} | {r.text[:200] or '(vazio)'}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
