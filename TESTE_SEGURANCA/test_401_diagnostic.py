"""
DIAGNOSTICO: Por que /v2/persons/send-document retorna 401?

Endpoints que PASSAM: phone/confirmation, verification-code/send, cpf-validation,
    terms, zipcode, validate-selfie-and-document, /user (400 mas passa WAF)
Endpoints que BLOQUEIAM: /v2/persons/send-document, /v2/device-key/validate-with-code

Testa sistematicamente:
1. Cookies de responses anteriores
2. Bearer token (fake vs ausente)
3. Diferentes combinacoes de headers
4. Outros endpoints em /v2/persons/*
5. Resposta headers (Set-Cookie, etc)
"""
import tls_client
import uuid
import json
import time
import jwt
import sys

BASE = "https://api.c03.frotabank.com.br"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"
CPF = "41265599904"
PHONE = "11984636182"
CORR = uuid.uuid4().hex


def pt():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")


def h(sid=None, bearer=None, extras=None):
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
    if extras:
        hh.update(extras)
    return hh


def dump_response(label, r):
    print(f"\n  [{label}]")
    print(f"    Status: {r.status_code}")
    body = r.text[:300] if r.text else "(vazio)"
    print(f"    Body: {body}")
    print(f"    Headers:")
    for k, v in r.headers.items():
        print(f"      {k}: {v[:100]}")


http = tls_client.Session(
    client_identifier="okhttp4_android_13", random_tls_extension_order=True
)

print("=" * 70)
print("DIAGNOSTICO 401: /v2/persons/send-document")
print("=" * 70)

# Obter sessionId
print("\n[1] Obter sessionId...")
r = http.post(
    f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h(),
)
print(f"  Envio: {r.status_code}")
dump_response("verification-code/send response", r)

code = input("\n>>> CODIGO (WhatsApp): ").strip()

r = http.post(
    f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(),
    timeout_seconds=45,
)
dump_response("phone/confirmation response", r)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    sys.exit(1)
print(f"\n  SessionId: {sid}")

# Checar cookies apos login
print("\n[2] Cookies apos autenticacao:")
cookies = http.cookies.get_dict()
if cookies:
    for k, v in cookies.items():
        print(f"  {k} = {v[:80]}")
else:
    print("  (nenhum cookie)")

# === TESTES RAPIDOS em /v2/persons/* ===
print("\n" + "=" * 70)
print("[3] TESTAR VARIOS ENDPOINTS /v2/persons/*")
print("=" * 70)

test_body = {"link": "https://example.com/test.jpg", "type": "selfie"}

endpoints = [
    ("GET", "/v2/personstatus", None),
    ("GET", "/v2/persons/documents-upload-lock", None),
    ("POST", "/v2/persons/send-document", test_body),
    ("POST", "/user/documents/upload", {"fileName": "test.jpg", "contentType": "image/jpeg"}),
    ("GET", "/v2/persons/basic-info", None),
    ("GET", "/v2/persons/address", None),
]

for method, path, body in endpoints:
    if method == "GET":
        r = http.get(f"{BASE}{path}", headers=h(sid=sid), timeout_seconds=10)
    else:
        r = http.post(f"{BASE}{path}", json=body, headers=h(sid=sid), timeout_seconds=10)
    tag = "OK" if r.status_code != 401 else "401!"
    print(f"  {tag:4s} {method:4s} {path:50s} => {r.status_code} | {r.text[:100] or '(vazio)'}")

# === TESTE 4: send-document com Bearer fake ===
print("\n" + "=" * 70)
print("[4] send-document COM Bearer token (fake)")
print("=" * 70)

fake_bearer = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
path = "/v2/persons/send-document"

r = http.post(f"{BASE}{path}", json=test_body,
    headers=h(sid=sid, bearer=fake_bearer), timeout_seconds=10)
dump_response("send-document + Bearer fake", r)

# === TESTE 5: send-document com diferentes combinacoes ===
print("\n" + "=" * 70)
print("[5] send-document: combinacoes de headers")
print("=" * 70)

combos = [
    ("Padrao (sessionId + sg)", h(sid=sid)),
    ("Sem sg-signature", {k: v for k, v in h(sid=sid).items() if k != "sg-signature"}),
    ("Sem sessionId", h()),
    ("Sem x-app headers", {k: v for k, v in h(sid=sid).items() if not k.startswith("x-app")}),
    ("Sem coords", {k: v for k, v in h(sid=sid).items() if "coords" not in k}),
    ("Minimo: content-type + sg + session", {
        "content-type": "application/json; charset=utf-8",
        "user-agent": "okhttp/4.11.0",
        "sg-signature": pt(),
        "sessionId": sid,
    }),
    ("Headers exatos do OkHttp (sem extras)", {
        "content-type": "application/json; charset=utf-8",
        "user-agent": "okhttp/4.11.0",
        "accept-encoding": "gzip",
        "sessionId": sid,
        "sg-signature": pt(),
    }),
]

for label, hdrs in combos:
    r = http.post(f"{BASE}{path}", json=test_body, headers=hdrs, timeout_seconds=10)
    print(f"  {r.status_code:3d} | {label}")

# === TESTE 6: Tentar com sessao DIFERENTE (requests.Session) ===
print("\n" + "=" * 70)
print("[6] Testar endpoints que PASSAM vs BLOQUEIAM na mesma sessao")
print("=" * 70)

print("\n  Chamando validate-selfie (deve passar)...")
r = http.post(f"{BASE}/v2/device-key/validate-selfie-and-document",
    json={
        "selfiePhotoUrl": "https://example.com/selfie.jpg",
        "frontDocumentPhotoUrl": "https://example.com/cnh_front.jpg",
        "backDocumentPhotoUrl": "https://example.com/cnh_back.jpg",
        "documentType": "cnh",
        "onlyValidation": True,
    },
    headers=h(sid=sid), timeout_seconds=10)
print(f"  validate-selfie: {r.status_code}")

print("  Cookies apos validate-selfie:")
cookies = http.cookies.get_dict()
if cookies:
    for k, v in cookies.items():
        print(f"    {k} = {v[:80]}")
else:
    print("    (nenhum)")

print("\n  Chamando send-document IMEDIATAMENTE apos validate-selfie...")
r = http.post(f"{BASE}{path}", json=test_body, headers=h(sid=sid), timeout_seconds=10)
print(f"  send-document: {r.status_code}")

# === TESTE 7: Tentar com HTTP/2 e diferentes TLS clients ===
print("\n" + "=" * 70)
print("[7] Testar com diferentes TLS client IDs")
print("=" * 70)

client_ids = [
    "okhttp4_android_13",
    "okhttp4_android_12",
    "okhttp4_android_11",
    "chrome_120",
    "safari_ios_17_0",
]

for cid in client_ids:
    try:
        http2 = tls_client.Session(client_identifier=cid, random_tls_extension_order=True)
        r = http2.post(f"{BASE}{path}", json=test_body, headers=h(sid=sid), timeout_seconds=10)
        print(f"  {r.status_code:3d} | {cid}")
    except Exception as e:
        print(f"  ERR | {cid}: {str(e)[:80]}")

# === TESTE 8: GET em /v2/persons/send-document ===
print("\n" + "=" * 70)
print("[8] Metodos HTTP diferentes em send-document")
print("=" * 70)

for method_name in ["GET", "POST", "PUT", "PATCH", "OPTIONS"]:
    try:
        r = http.execute_request(method_name, f"{BASE}{path}",
            json=test_body if method_name != "GET" else None,
            headers=h(sid=sid), timeout_seconds=10)
        print(f"  {r.status_code:3d} | {method_name}")
    except Exception as e:
        print(f"  ERR | {method_name}: {str(e)[:60]}")

# === TESTE 9: Path variations ===
print("\n" + "=" * 70)
print("[9] Path variations")
print("=" * 70)

paths = [
    "/v2/persons/send-document",
    "/v2/persons/send-document/",
    "/persons/send-document",
    "/v1/persons/send-document",
    "/v2/person/send-document",
]

for p in paths:
    r = http.post(f"{BASE}{p}", json=test_body, headers=h(sid=sid), timeout_seconds=10)
    print(f"  {r.status_code:3d} | {p}")

print("\n" + "=" * 70)
print("FIM DIAGNOSTICO")
print("=" * 70)
