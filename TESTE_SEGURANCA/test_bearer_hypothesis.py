"""
HIPOTESE: send-document requer Bearer token (post-login), nao apenas sessionId.
Testar:
1. Tentar login direto com o CPF (conta pode ja existir)
2. Se login funcionar -> Bearer token -> tentar send-document
3. Se nao -> tentar POST /user primeiro -> login -> Bearer -> send-document
4. Testar GET /v2/persons/documents-upload-lock (tambem /v2/persons/*)
"""
import tls_client
import uuid, json, time, jwt, sys

BASE = "https://api.c03.frotabank.com.br"
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
print("HIPOTESE: send-document requer Bearer token")
print("=" * 60)

# TESTE 1: Login direto (sem sessao)
print("\n[1] Tentar login direto...")
r = http.post(f"{BASE}/v2/auth/multifactor-login",
    json={"document": CPF, "password": PASSWORD},
    headers=h(), timeout_seconds=15)
print(f"  Login: {r.status_code}")
print(f"  Body: {r.text[:500]}")

token = None
if r.status_code == 200:
    data = r.json()
    token = data.get("token", "")
    print(f"  Token: {token[:60]}..." if token else "  SEM TOKEN")

# TESTE 2: Obter sessao e tentar login com sessao
print("\n[2] Obter sessao...")
r = http.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h())
print(f"  Envio codigo: {r.status_code}")

code = input("\n>>> CODIGO: ").strip()

r = http.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(), timeout_seconds=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  Session: {sid}")

# TESTE 3: Login COM sessao
print("\n[3] Login com sessao...")
r = http.post(f"{BASE}/v2/auth/multifactor-login",
    json={"document": CPF, "password": PASSWORD},
    headers=h(sid=sid), timeout_seconds=15)
print(f"  Login: {r.status_code}")
print(f"  Body: {r.text[:500]}")

if r.status_code == 200:
    data = r.json()
    token = data.get("token", "")
    if token:
        print(f"  TOKEN OBTIDO: {token[:60]}...")

# TESTE 4: Se temos token, testar send-document COM Bearer
if token:
    print("\n" + "=" * 60)
    print("[4] send-document COM Bearer token")
    print("=" * 60)

    body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}
    url = f"{BASE}/v2/persons/send-document"

    # 4a: Bearer + sessionId
    print("\n  4a: Bearer + sessionId...")
    r = http.post(url, json=body, headers=h(sid=sid, bearer=token), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

    # 4b: Apenas Bearer (sem sessionId)
    print("  4b: Apenas Bearer...")
    r = http.post(url, json=body, headers=h(bearer=token), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

    # 4c: GET /v2/personstatus com Bearer
    print("  4c: GET /v2/personstatus com Bearer...")
    r = http.get(f"{BASE}/v2/personstatus", headers=h(sid=sid, bearer=token), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

    # 4d: GET /v2/persons/documents-upload-lock com Bearer
    print("  4d: GET /v2/persons/documents-upload-lock com Bearer...")
    r = http.get(f"{BASE}/v2/persons/documents-upload-lock", headers=h(sid=sid, bearer=token), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

else:
    # Sem token - testar com sessionId apenas para comparar
    print("\n" + "=" * 60)
    print("[4] SEM Bearer - testar com sessionId apenas")
    print("=" * 60)

    # 4a: send-document com sessionId
    body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}
    url = f"{BASE}/v2/persons/send-document"
    print("\n  4a: send-document com sessionId...")
    r = http.post(url, json=body, headers=h(sid=sid), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

    # 4b: GET /v2/persons/documents-upload-lock com sessionId
    print("  4b: GET /v2/persons/documents-upload-lock com sessionId...")
    r = http.get(f"{BASE}/v2/persons/documents-upload-lock", headers=h(sid=sid), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

    # 4c: GET /v2/personstatus com sessionId
    print("  4c: GET /v2/personstatus com sessionId...")
    r = http.get(f"{BASE}/v2/personstatus", headers=h(sid=sid), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

    # 4d: Testar com Bearer fake pra ver se nginx muda resposta
    print("\n  4d: send-document com Bearer FAKE...")
    r = http.post(url, json=body, headers=h(sid=sid, bearer="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.fake"), timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

    # 4e: Testar APENAS com Authorization header (nada mais)
    print("  4e: APENAS Authorization header...")
    minimal = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.fake", "content-type": "application/json"}
    r = http.post(url, json=body, headers=minimal, timeout_seconds=15)
    print(f"    Status: {r.status_code} | Body: {r.text[:200] or '(vazio)'}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
