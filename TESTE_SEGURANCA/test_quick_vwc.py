"""
Teste rapido: validate-with-code SEM device key headers.
Hipotese: o 401 e causado pelo servidor rejeitar device key signature de uma key "created".
Se funcionar sem DK headers, confirma que o servidor so aceita DK de keys "validated".
"""
import tls_client
import uuid
import json
import time
import jwt
import hashlib
import hmac as hmac_mod
import base64
import sys

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

CPF = "41265599904"
PHONE = "11984636182"
CORR = uuid.uuid4().hex
DEVICE_UUID = str(uuid.uuid4())
DEVICE_ID = uuid.uuid4().hex[:16]


def pinning_token():
    return jwt.encode(
        {"iss": PINNING_ISSUER, "iat": int(time.time())},
        PINNING_SECRET,
        algorithm="HS256",
    )


def base_headers(sid=None):
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
        "sg-signature": pinning_token(),
        "x-device-coords-latitude": "-25.4284",
        "x-device-coords-longitude": "-49.2733",
        "x-device-coords-altitude": "0",
        "x-device-coords-speed": "0",
    }
    if sid:
        hh["sessionId"] = sid
    return hh


http = tls_client.Session(
    client_identifier="okhttp4_android_13", random_tls_extension_order=True
)

print("=" * 60)
print("TESTE RAPIDO: validate-with-code SEM device key headers")
print("=" * 60)

# 1. Phone verify
print("\n[1] Onboarding...")
r = http.post(
    f"{BASE}/v2/verification-code/send",
    json={
        "phone": PHONE,
        "verificationCodeType": "onboarding",
        "deliveryMethod": "whatsapp",
        "document": CPF,
    },
    headers=base_headers(),
)
print(f"  Envio: {r.status_code}")

code = input("\n>>> CODIGO ONBOARDING: ").strip()
r = http.post(
    f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=base_headers(),
    timeout_seconds=45,
)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  SessionId: {sid}")

# 2. Create device key
print("\n[2] Criar device key...")
r = http.post(
    f"{SAFEGUARD_API_URL}device_key",
    json={
        "deviceId": DEVICE_ID,
        "isRoot": False,
        "userId": CPF,
        "uuid": DEVICE_UUID,
        "userMetadata": None,
        "operatingSystem": "android",
    },
    headers={"SG-API-KEY": SAFEGUARD_API_KEY, "Content-Type": "application/json"},
)
dk = r.json() if r.status_code in (200, 201) else {}
pk = dk.get("privateKey", "")
if not pk:
    print(f"  FALHOU: {r.text[:200]}")
    sys.exit(1)
print(f"  OK: key={pk[:30]}...")

# 3. Send deviceKeyLight code
print("\n[3] Enviar codigo deviceKeyLight...")
r = http.post(
    f"{BASE}/v2/verification-code/send",
    json={
        "phone": PHONE,
        "verificationCodeType": "deviceKeyLight",
        "deliveryMethod": "whatsapp",
        "document": CPF,
    },
    headers=base_headers(sid),
)
print(f"  Envio: {r.status_code}")
if r.status_code != 200:
    print(f"  {r.text[:200]}")
    sys.exit(1)

code2 = input("\n>>> CODIGO DEVICE KEY: ").strip()

# 4. Validate-with-code SEM device key headers
print("\n" + "=" * 60)
print("[4a] validate-with-code SEM device key headers")
print("=" * 60)
body = {
    "uuid": DEVICE_UUID,
    "deviceId": DEVICE_ID,
    "document": CPF,
    "phone": PHONE,
    "verificationCode": code2,
}
r = http.post(
    f"{BASE}/v2/device-key/validate-with-code",
    json=body,
    headers=base_headers(sid),
    timeout_seconds=15,
)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:400] or '(vazio)'}")

if r.status_code == 401:
    print("\n  Ainda 401 sem DK. Tentando sem sg-signature tambem...")
    hh = base_headers(sid)
    del hh["sg-signature"]
    r = http.post(
        f"{BASE}/v2/device-key/validate-with-code",
        json=body,
        headers=hh,
        timeout_seconds=15,
    )
    print(f"  Sem sg: {r.status_code} | {r.text[:200] or '(vazio)'}")

# 4b. Also try documents-upload-lock
print("\n[4b] GET /v2/persons/documents-upload-lock")
r = http.get(
    f"{BASE}/v2/persons/documents-upload-lock",
    headers=base_headers(sid),
    timeout_seconds=15,
)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:300] or '(vazio)'}")

# 4c. Try send-document SEM device key headers
print("\n[4c] send-document SEM device key headers")
r = http.post(
    f"{BASE}/v2/persons/send-document",
    json={"link": "https://test.com/selfie.jpg", "type": "selfie"},
    headers=base_headers(sid),
    timeout_seconds=15,
)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:300] or '(vazio)'}")

# 5. Check SafeGuard status
print("\n[5] SafeGuard status...")
r = http.get(
    f"{SAFEGUARD_API_URL}device_key/status?uuid={DEVICE_UUID}&deviceId={DEVICE_ID}",
    headers={"SG-API-KEY": SAFEGUARD_API_KEY},
)
print(f"  {r.text[:200]}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
