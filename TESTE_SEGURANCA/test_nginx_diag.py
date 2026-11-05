"""
Diagnóstico do 401 nginx em /v2/persons/*:
- Captura headers completos da resposta 401
- Testa múltiplos endpoints /v2/persons/* para confirmar padrão
- Testa com mínimo de headers (nginx puro)
- Testa outros /v2/ que NÃO são /persons/ pra comparar
- Verifica cookies da sessão
"""
from curl_cffi import requests as curl_requests
import requests, uuid, json, time, jwt, sys

BASE = "https://api.c03.frotabank.com.br"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"
CPF = "41265599904"
PHONE = "11984636182"

http2 = curl_requests.Session(impersonate="chrome120", timeout=15)
CORR = uuid.uuid4().hex


def pt():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")


def h(sid):
    return {
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
        "sessionId": sid,
        "sg-signature": pt(),
        "x-device-coords-latitude": "-25.4284",
        "x-device-coords-longitude": "-49.2733",
        "x-device-coords-altitude": "0",
        "x-device-coords-speed": "0",
    }


print("=" * 60)
print("DIAGNOSTICO NGINX 401")
print("=" * 60)

# Obter sessão
print("\n[1] Obter sessao...")
r = http2.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h(str(uuid.uuid4())))
print(f"  Envio: {r.status_code}")

code = input("\n>>> CODIGO: ").strip()
r = http2.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(str(uuid.uuid4())), timeout=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  Session: {sid}")

# Verificar cookies da sessão
print(f"\n  Cookies: {dict(http2.cookies)}")

r = http2.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid))
print(f"  CPF: {r.status_code}")
print(f"  Cookies pos-CPF: {dict(http2.cookies)}")

body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}

print("\n" + "=" * 60)
print("TESTE 1: Headers completos do 401")
print("=" * 60)
r = http2.post(f"{BASE}/v2/persons/send-document", json=body, headers=h(sid), timeout=15)
print(f"  Status: {r.status_code}")
print(f"  Body repr: {repr(r.text)}")
print(f"  Content-Length: {r.headers.get('content-length', '?')}")
print(f"  WWW-Authenticate: {r.headers.get('www-authenticate', 'NAO PRESENTE')}")
print(f"  HEADERS COMPLETOS:")
for k, v in r.headers.items():
    print(f"    {k}: {v}")

print("\n" + "=" * 60)
print("TESTE 2: Todos /v2/persons/* endpoints")
print("=" * 60)
persons_eps = [
    ("POST", "/v2/persons/send-document", body),
    ("GET", "/v2/persons", None),
    ("POST", "/v2/persons", {"document": CPF}),
    ("GET", "/v2/persons/send-document", None),
    ("POST", "/v2/personstatus", {"document": CPF}),
    ("GET", "/v2/personstatus", None),
    ("POST", "/v2/persons/identification", {"documentNumber": CPF}),
]
for method, ep, payload in persons_eps:
    if method == "GET":
        r = http2.get(f"{BASE}{ep}", headers=h(sid), timeout=10)
    else:
        r = http2.post(f"{BASE}{ep}", json=payload, headers=h(sid), timeout=10)
    status_emoji = "OK" if r.status_code != 401 else "BLOCKED"
    print(f"  {status_emoji} {method} {ep}: {r.status_code} | body={r.text[:100] or '(vazio)'} | server={r.headers.get('server','?')}")

print("\n" + "=" * 60)
print("TESTE 3: Outros /v2/ (NÃO persons)")
print("=" * 60)
other_eps = [
    ("GET", "/v2/terms?types[]=TermsOfUse", None),
    ("POST", "/v2/verification-code/send", {"phone": PHONE, "verificationCodeType": "onboarding", "deliveryMethod": "whatsapp", "document": CPF}),
    ("POST", "/v2/device-key/validate-selfie-and-document", {"uuid": "test", "deviceId": "test"}),
    ("POST", "/v2/auth/multifactor-login", {"document": CPF, "password": "test"}),
    ("POST", "/v2/credentials/exists", {"document": CPF}),
]
for method, ep, payload in other_eps:
    if method == "GET":
        r = http2.get(f"{BASE}{ep}", headers=h(sid), timeout=10)
    else:
        r = http2.post(f"{BASE}{ep}", json=payload, headers=h(sid), timeout=10)
    status_emoji = "OK" if r.status_code != 401 else "BLOCKED"
    print(f"  {status_emoji} {method} {ep}: {r.status_code} | body={r.text[:100] or '(vazio)'}")

print("\n" + "=" * 60)
print("TESTE 4: send-document com MINIMO de headers")
print("=" * 60)
minimal = {
    "content-type": "application/json",
    "sessionId": sid,
}
r = http2.post(f"{BASE}/v2/persons/send-document", json=body, headers=minimal, timeout=10)
print(f"  Minimal: {r.status_code} | {r.text[:100] or '(vazio)'}")

# Sem sessionId
r = http2.post(f"{BASE}/v2/persons/send-document", json=body,
    headers={"content-type": "application/json"}, timeout=10)
print(f"  Sem sessionId: {r.status_code} | {r.text[:100] or '(vazio)'}")

# Sem NENHUM header (nem content-type)
r = http2.post(f"{BASE}/v2/persons/send-document", data=json.dumps(body), timeout=10)
print(f"  Sem headers: {r.status_code} | {r.text[:100] or '(vazio)'}")

# requests nativo (TLS diferente)
print("\n  requests nativo...")
http_native = requests.Session()
r = http_native.post(f"{BASE}/v2/persons/send-document", json=body,
    headers=h(sid), timeout=15)
print(f"  requests nativo: {r.status_code} | {r.text[:100] or '(vazio)'}")
print(f"  Response headers:")
for k, v in r.headers.items():
    print(f"    {k}: {v}")

print("\n" + "=" * 60)
print("FIM DIAGNOSTICO")
print("=" * 60)
