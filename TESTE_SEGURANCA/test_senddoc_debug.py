"""
Debug profundo do 401 em send-document:
- Testa requests vs curl_cffi
- Testa OPTIONS/HEAD
- Testa variações de URL
- Testa com/sem headers específicos
Usa sessão real do teste anterior.
"""
from curl_cffi import requests as curl_requests
import requests, uuid, json, time, jwt

BASE = "https://api.c03.frotabank.com.br"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"
CPF = "41265599904"
PHONE = "11984636182"

http_req = requests.Session()
http_req.timeout = 15
http_curl = curl_requests.Session(impersonate="chrome120", timeout=15)

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


# Primeiro, obter sessão válida
print("=" * 60)
print("DEBUG SEND-DOCUMENT 401")
print("=" * 60)

print("\n[1] Obter sessao...")
r = http_curl.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h(str(uuid.uuid4())))
print(f"  Envio: {r.status_code}")

code = input("\n>>> CODIGO: ").strip()
r = http_curl.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(str(uuid.uuid4())), timeout=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    exit(1)
print(f"  Session: {sid}")

r = http_curl.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid))
print(f"  CPF validation: {r.status_code}")

body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}
url = f"{BASE}/v2/persons/send-document"

print("\n" + "=" * 60)
print("TESTES")
print("=" * 60)

# 1. curl_cffi chrome120 (padrão)
print("\n[1] curl_cffi chrome120...")
r = http_curl.post(url, json=body, headers=h(sid), timeout=30)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}' | server: {r.headers.get('server','?')}")

# 2. requests nativo (diferente TLS fingerprint)
print("\n[2] requests nativo...")
try:
    r = http_req.post(url, json=body, headers=h(sid), timeout=30)
    print(f"  Status: {r.status_code} | Body: '{r.text[:200]}' | server: {r.headers.get('server','?')}")
except Exception as e:
    print(f"  ERRO: {e}")

# 3. curl_cffi com impersonate diferente
print("\n[3] curl_cffi safari...")
http3 = curl_requests.Session(impersonate="safari17_0", timeout=15)
r = http3.post(url, json=body, headers=h(sid), timeout=30)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}' | server: {r.headers.get('server','?')}")

# 4. OPTIONS (CORS preflight)
print("\n[4] OPTIONS...")
r = http_curl.options(url, headers=h(sid), timeout=15)
print(f"  Status: {r.status_code} | Headers: {dict(r.headers)}")

# 5. GET ao invés de POST
print("\n[5] GET /v2/persons/send-document...")
r = http_curl.get(url, headers=h(sid), timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

# 6. Sem versão: /persons/send-document
print("\n[6] POST /persons/send-document (sem /v2)...")
r = http_curl.post(f"{BASE}/persons/send-document", json=body, headers=h(sid), timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

# 7. V1: /v1/persons/send-document
print("\n[7] POST /v1/persons/send-document...")
r = http_curl.post(f"{BASE}/v1/persons/send-document", json=body, headers=h(sid), timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

# 8. Outro endpoint persons
print("\n[8] GET /v2/persons (sem send-document)...")
r = http_curl.get(f"{BASE}/v2/persons", headers=h(sid), timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

# 9. POST /v2/personstatus (outro endpoint v2/person)
print("\n[9] POST /v2/personstatus...")
r = http_curl.post(f"{BASE}/v2/personstatus", json={"document": CPF}, headers=h(sid), timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

# 10. Testar com Authorization header fake (Bearer)
print("\n[10] POST send-document com Authorization: Bearer fake...")
hh = h(sid)
hh["Authorization"] = "Bearer eyJhbGciOiJIUzI1NiJ9.fake.token"
r = http_curl.post(url, json=body, headers=hh, timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

# 11. POST /user SEM documentos (teste base)
print("\n[11] POST /user sem payload (referência)...")
r = http_curl.post(f"{BASE}/user", json={}, headers=h(sid), timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

# 12. Testar com header Origin/Referer
print("\n[12] POST send-document com Origin header...")
hh = h(sid)
hh["Origin"] = "https://api.c03.frotabank.com.br"
hh["Referer"] = "https://api.c03.frotabank.com.br/"
r = http_curl.post(url, json=body, headers=hh, timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")

print("\n" + "=" * 60)
print("FIM DEBUG")
print("=" * 60)
