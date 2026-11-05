"""
Teste isolado: criar device key, validar, e testar assinatura no send-document
"""
import requests, uuid, json, hashlib, hmac as hmac_module, base64, time, jwt
from urllib.parse import urlparse

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"
CPF = "41265599904"

http = requests.Session()
http.timeout = 15

def pinning_token():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")

def sg_h():
    return {"SG-API-KEY": SAFEGUARD_API_KEY, "Content-Type": "application/json"}

# 1) Criar device key
device_id = uuid.uuid4().hex[:16]
device_uuid = str(uuid.uuid4())
print(f"[1] Criar device key: deviceId={device_id}, uuid={device_uuid}")

r = http.post(f"{SAFEGUARD_API_URL}device_key",
    json={"deviceId": device_id, "isRoot": False, "userId": CPF,
          "uuid": device_uuid, "userMetadata": None, "operatingSystem": "android"},
    headers=sg_h())
print(f"  POST /device_key: {r.status_code}")
print(f"  Response: {r.text[:500]}")

if r.status_code not in (200, 201):
    print("FALHOU - saindo")
    exit(1)

data = r.json()
device_key = data.get("privateKey")
print(f"  privateKey len: {len(device_key) if device_key else 'NONE'}")

# 2) Validar device key
print(f"\n[2] Validar device key...")
r = http.post(f"{SAFEGUARD_API_URL}device_key/validate",
    json={"uuid": device_uuid, "deviceId": device_id},
    headers=sg_h())
print(f"  POST /device_key/validate: {r.status_code}")
print(f"  Response: {r.text[:500]}")

# 3) Checar status
print(f"\n[3] Checar status do device key...")
r = http.get(f"{SAFEGUARD_API_URL}device_key/status",
    params={"uuid": device_uuid, "deviceId": device_id},
    headers=sg_h())
print(f"  GET /device_key/status: {r.status_code}")
print(f"  Response: {r.text[:500]}")

# 4) Gerar assinatura e testar send-document
print(f"\n[4] Testar assinatura no send-document...")

SESSION = str(uuid.uuid4())
CORR = uuid.uuid4().hex

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

def _traverse(obj, parent_keys=None, result=None):
    if parent_keys is None: parent_keys = []
    if result is None: result = []
    items = obj.items() if isinstance(obj, dict) else enumerate(obj) if isinstance(obj, list) else []
    for key, value in items:
        key_path = parent_keys + [str(key)]
        if value is not None and isinstance(value, (dict, list)) and len(value) > 0:
            _traverse(value, key_path, result)
        else:
            v_str = "null" if value is None else ("true" if value is True else ("false" if value is False else str(value)))
            result.append(".".join(key_path) + "=" + v_str)
    return result

def generate_signature(method, url, headers, body=None):
    parsed = urlparse(url)
    domain = parsed.hostname.lower()
    path = parsed.path or "/"
    skip = {"sg-signature", "x-device-key-headers", "x-device-key-signature", "x-device-key-user-id"}
    clean_headers = {k: v for k, v in headers.items() if k.lower() not in skip}
    parts = [method.upper(), domain, path]
    if body and len(body) > 0:
        pairs = _traverse(body)
        pairs.sort()
        parts.append("\n".join(pairs))
    if clean_headers and len(clean_headers) > 0:
        pairs = _traverse(clean_headers)
        lowered = []
        for pair in pairs:
            eq_idx = pair.index("=")
            lowered.append(pair[:eq_idx].lower() + pair[eq_idx:])
        lowered.sort()
        parts.append("\n".join(lowered))
    canonical = "\n".join(parts)
    print(f"\n  === CANONICAL STRING ===")
    for i, line in enumerate(canonical.split("\n")):
        print(f"  [{i}] {line[:120]}")
    print(f"  === END ({len(canonical)} chars) ===\n")
    sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    hmac_hex = hmac_module.new(
        device_key.encode("utf-8"), sha1_hex.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    sig_plain = f"{SAFEGUARD_API_KEY}:{device_id}:{device_uuid}:{sha1_hex}:{hmac_hex}{sha1_hex}"
    return base64.b64encode(sig_plain.encode("utf-8")).decode("utf-8")

send_body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}
send_url = f"{BASE}/v2/persons/send-document"
send_headers = h()
header_keys = ";".join(send_headers.keys())
sig = generate_signature("POST", send_url, send_headers, body=send_body)
send_headers["x-device-key-headers"] = header_keys
send_headers["x-device-key-signature"] = sig
send_headers["x-device-key-user-id"] = CPF

from curl_cffi import requests as curl_requests
http2 = curl_requests.Session(impersonate="chrome120", timeout=15)

r = http2.post(send_url, json=send_body, headers=send_headers, timeout=30)
print(f"  send-document: {r.status_code}")
print(f"  Response: {r.text[:500]}")
print(f"  Response headers: {dict(r.headers)}")
