"""
Teste 2: device key validate com curl_cffi e headers mais completos
"""
import uuid, json, hashlib, hmac as hmac_module, base64, time, jwt
from curl_cffi import requests as curl_requests

SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br"
CPF = "41265599904"

http = curl_requests.Session(impersonate="chrome120", timeout=15)

def sg_h():
    return {
        "SG-API-KEY": SAFEGUARD_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "okhttp/4.11.0",
        "Accept": "application/json",
    }

# 1) Criar device key
device_id = uuid.uuid4().hex[:16]
device_uuid = str(uuid.uuid4())
print(f"[1] Criar device key: deviceId={device_id}, uuid={device_uuid}")

body = {"deviceId": device_id, "isRoot": False, "userId": CPF,
        "uuid": device_uuid, "userMetadata": None, "operatingSystem": "android"}
r = http.post(f"{SAFEGUARD_API_URL}/device_key", json=body, headers=sg_h())
print(f"  POST /device_key: {r.status_code}")
print(f"  Response: {r.text[:500]}")

if r.status_code not in (200, 201):
    print("FALHOU")
    exit(1)

data = r.json()
device_key = data.get("privateKey")
print(f"  privateKey: {device_key[:20]}...")

# 2) Tentar validate com varias combinacoes
print(f"\n[2a] Validate - body={'{uuid, deviceId}'}")
body_v = {"uuid": device_uuid, "deviceId": device_id}
r = http.post(f"{SAFEGUARD_API_URL}/device_key/validate", json=body_v, headers=sg_h())
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

print(f"\n[2b] Validate - com userId tambem")
body_v2 = {"uuid": device_uuid, "deviceId": device_id, "userId": CPF}
r = http.post(f"{SAFEGUARD_API_URL}/device_key/validate", json=body_v2, headers=sg_h())
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

print(f"\n[2c] Validate - com privateKey")
body_v3 = {"uuid": device_uuid, "deviceId": device_id, "privateKey": device_key}
r = http.post(f"{SAFEGUARD_API_URL}/device_key/validate", json=body_v3, headers=sg_h())
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# 3) Status
print(f"\n[3] Status...")
r = http.get(f"{SAFEGUARD_API_URL}/device_key/status",
    params={"uuid": device_uuid, "deviceId": device_id}, headers=sg_h())
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# 4) Tentar PUT ao inves de POST para validate
print(f"\n[4] PUT /device_key/validate")
r = http.put(f"{SAFEGUARD_API_URL}/device_key/validate", json=body_v, headers=sg_h())
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# 5) Tentar PATCH /device_key
print(f"\n[5] PATCH /device_key")
r = http.patch(f"{SAFEGUARD_API_URL}/device_key", json=body_v, headers=sg_h())
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# 6) Verificar outros endpoints
print(f"\n[6] GET /device_key (listar)")
r = http.get(f"{SAFEGUARD_API_URL}/device_key",
    params={"uuid": device_uuid, "deviceId": device_id}, headers=sg_h())
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# 7) Testar send-document COM device key status=created (sem validar)
print(f"\n[7] Testar send-document mesmo com status=created")
import requests as req_lib
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"
BASE = "https://api.c03.frotabank.com.br"
SESSION = str(uuid.uuid4())
CORR = uuid.uuid4().hex

def pinning_token():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")

def h(sid=None):
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
        "sessionId": sid or SESSION,
        "sg-signature": pinning_token(),
        "x-device-coords-latitude": "-25.4284",
        "x-device-coords-longitude": "-49.2733",
        "x-device-coords-altitude": "0",
        "x-device-coords-speed": "0",
    }

# Testar sem nenhum device key header
print(f"\n[7a] send-document SEM device key headers")
send_body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}
send_url = f"{BASE}/v2/persons/send-document"
r = http.post(send_url, json=send_body, headers=h(), timeout=30)
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# Testar com sg-signature somente
print(f"\n[7b] send-document com sg-signature mas SEM device key")
r = http.post(send_url, json=send_body, headers=h(), timeout=30)
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")
