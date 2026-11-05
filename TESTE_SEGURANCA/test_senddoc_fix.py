"""
Teste corrigido do send-document:
- Assinatura calculada SEM headers (como o app real faz)
- x-device-key-headers NAO setado (config nao tem headers)
- Testa com e sem device key headers
"""
import requests, uuid, json, re, hashlib, hmac as hmac_module, base64, time, jwt, sys
from urllib.parse import urlparse
from curl_cffi import requests as curl_requests

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

CPF = "41265599904"
PHONE = "11984636182"

http = requests.Session()
http.timeout = 15
http2 = curl_requests.Session(impersonate="chrome120", timeout=15)

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
        "sessionId": sid or str(uuid.uuid4()),
        "sg-signature": pinning_token(),
        "x-device-coords-latitude": "-25.4284",
        "x-device-coords-longitude": "-49.2733",
        "x-device-coords-altitude": "0",
        "x-device-coords-speed": "0",
    }


def sg_h():
    return {"SG-API-KEY": SAFEGUARD_API_KEY, "Content-Type": "application/json"}


def _traverse(obj, parent_keys=None, result=None):
    if parent_keys is None:
        parent_keys = []
    if result is None:
        result = []
    items = obj.items() if isinstance(obj, dict) else enumerate(obj) if isinstance(obj, list) else []
    for key, value in items:
        key_path = parent_keys + [str(key)]
        if value is not None and isinstance(value, (dict, list)) and len(value) > 0:
            _traverse(value, key_path, result)
        else:
            v_str = "null" if value is None else ("true" if value is True else ("false" if value is False else str(value)))
            result.append(".".join(key_path) + "=" + v_str)
    return result


def generate_signature_v2(device_key, device_id, device_uuid, method, url, body=None, headers=None):
    """Gera assinatura CORRIGIDA - headers opcionais (o app real nao passa headers para send-document)"""
    parsed = urlparse(url)
    domain = parsed.hostname.lower()
    path = parsed.path or "/"

    parts = [method.upper(), domain, path]

    if body and len(body) > 0:
        pairs = _traverse(body)
        pairs.sort()
        parts.append("\n".join(pairs))

    if headers and len(headers) > 0:
        skip = {"sg-signature", "x-device-key-headers", "x-device-key-signature", "x-device-key-user-id"}
        clean = {k: v for k, v in headers.items() if k.lower() not in skip}
        if clean:
            pairs = _traverse(clean)
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


# ===== 1. Obter sessao real via phone verification =====
print("=" * 60)
print("TESTE SEND-DOCUMENT CORRIGIDO")
print("=" * 60)

print("\n[1] Enviar codigo de verificacao...")
send_body = {"phone": PHONE, "verificationCodeType": "onboarding",
             "deliveryMethod": "whatsapp", "document": CPF}
r = http2.post(f"{BASE}/v2/verification-code/send", json=send_body, headers=h())
print(f"  Status: {r.status_code} | {r.text[:200]}")

if r.status_code != 200:
    print("  Tentando formato diferente...")
    send_body["phone"] = f"({PHONE[:2]}) {PHONE[2:7]}-{PHONE[7:]}"
    r = http2.post(f"{BASE}/v2/verification-code/send", json=send_body, headers=h())
    print(f"  Status: {r.status_code} | {r.text[:200]}")

code = input("\n>>> CODIGO WHATSAPP: ").strip()

print("\n[2] Confirmar codigo...")
sid = None
for phone_try in [PHONE, f"({PHONE[:2]}) {PHONE[2:7]}-{PHONE[7:]}"]:
    r = http2.post(f"{BASE}/phone/confirmation",
        json={"phone": phone_try, "verificationCode": code}, headers=h(), timeout=45)
    print(f"  phone={phone_try}: {r.status_code} | {r.text[:200]}")
    try:
        data = r.json()
        if data.get("sessionId"):
            sid = data["sessionId"]
            break
    except:
        pass

if not sid:
    sys.exit("Sem sessionId!")
print(f"  SESSION: {sid}")

# ===== 2. CPF validation =====
print("\n[3] CPF validation...")
r = http2.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid), timeout=30)
print(f"  Status: {r.status_code} | {r.text[:200]}")

# ===== 3. Upload de documento de teste =====
print("\n[4] Upload documento...")
CNH_PATH = r"C:\Users\Acer\Documents\XuanZhi9\Pictures\CNH-e.pdf.pdf"
hh = h(sid)
del hh["content-type"]
try:
    with open(CNH_PATH, "rb") as f:
        img_data = f.read()
    r = http.post(f"{BASE}/user/documents/upload", headers=hh,
        files={"file": ("DIGITAL_DRIVER_LICENSE.pdf", img_data, "application/pdf")},
        data={"documentType": "DIGITAL_DRIVER_LICENSE"}, timeout=60)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        doc_url = r.json().get("url", "")
        print(f"  URL: {doc_url[:80]}...")
    else:
        print(f"  Body: {r.text[:200]}")
        doc_url = "https://example.com/test.pdf"
except Exception as e:
    print(f"  ERRO: {e}")
    doc_url = "https://example.com/test.pdf"

# ===== 4. Criar device key =====
print("\n[5] Criar device key...")
device_id = uuid.uuid4().hex[:16]
device_uuid = str(uuid.uuid4())
r = http2.post(f"{SAFEGUARD_API_URL}device_key",
    json={"deviceId": device_id, "isRoot": False, "userId": CPF,
          "uuid": device_uuid, "userMetadata": None, "operatingSystem": "android"},
    headers=sg_h())
print(f"  Status: {r.status_code}")
device_key = None
if r.status_code in (200, 201):
    device_key = r.json().get("privateKey")
    print(f"  privateKey len: {len(device_key) if device_key else 'NONE'}")

    # Tentar validar (pode falhar com 403, tudo bem)
    r = http2.post(f"{SAFEGUARD_API_URL}device_key/validate",
        json={"uuid": device_uuid, "deviceId": device_id},
        headers=sg_h())
    print(f"  Validate: {r.status_code} | {r.text[:100]}")

# ===== 5. Testar send-document com VARIAS abordagens =====
send_url = f"{BASE}/v2/persons/send-document"
send_body = {"link": doc_url, "type": "digitalDriverLicense"}

print("\n" + "=" * 60)
print("TESTES DE SEND-DOCUMENT")
print("=" * 60)

# Teste A: SEM device key headers (como se o device key nao existisse/nao validado)
print("\n[A] SEM device key headers...")
headers_a = h(sid)
r = http2.post(send_url, json=send_body, headers=headers_a, timeout=30)
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")
print(f"  Response headers: {dict(r.headers)}")

# Teste B: COM device key headers, assinatura SEM headers (CORRETO - como o app faz)
if device_key:
    print("\n[B] COM device key, assinatura SEM headers (CORRIGIDO)...")
    sig = generate_signature_v2(device_key, device_id, device_uuid, "POST", send_url, body=send_body, headers=None)
    headers_b = h(sid)
    headers_b["x-device-key-signature"] = sig
    headers_b["x-device-key-user-id"] = CPF
    # NAO seta x-device-key-headers (porque config nao tinha headers no app real)
    r = http2.post(send_url, json=send_body, headers=headers_b, timeout=30)
    print(f"  Status: {r.status_code} | Body: {r.text[:300]}")
    print(f"  Response headers: {dict(r.headers)}")

    # Teste C: COM device key headers E x-device-key-headers vazio (edge case)
    print("\n[C] COM device key + x-device-key-headers vazio...")
    headers_c = h(sid)
    sig = generate_signature_v2(device_key, device_id, device_uuid, "POST", send_url, body=send_body, headers=None)
    headers_c["x-device-key-signature"] = sig
    headers_c["x-device-key-user-id"] = CPF
    headers_c["x-device-key-headers"] = ""
    r = http2.post(send_url, json=send_body, headers=headers_c, timeout=30)
    print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

    # Teste D: Assinatura com TODOS headers (abordagem antiga - para comparar)
    print("\n[D] Assinatura com TODOS headers (antiga)...")
    headers_d = h(sid)
    sig_old = generate_signature_v2(device_key, device_id, device_uuid, "POST", send_url, body=send_body, headers=headers_d)
    header_keys = ";".join(headers_d.keys())
    headers_d["x-device-key-headers"] = header_keys
    headers_d["x-device-key-signature"] = sig_old
    headers_d["x-device-key-user-id"] = CPF
    r = http2.post(send_url, json=send_body, headers=headers_d, timeout=30)
    print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# Teste E: Apenas com sg-signature mas sem NENHUM outro header especial
print("\n[E] Headers minimos (so app headers + session + sg-signature)...")
headers_e = {
    "x-app-name": "br.com.frotabank.app",
    "x-app-platform": "android",
    "x-app-version": "18.10.18",
    "content-type": "application/json",
    "user-agent": "okhttp/4.11.0",
    "sessionId": sid,
    "sg-signature": pinning_token(),
}
r = http2.post(send_url, json=send_body, headers=headers_e, timeout=30)
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

# Teste F: Sem sg-signature (para ver se a 401 e do pinning)
print("\n[F] Sem sg-signature (testar se 401 vem do pinning)...")
headers_f = h(sid)
del headers_f["sg-signature"]
r = http2.post(send_url, json=send_body, headers=headers_f, timeout=30)
print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

print("\n" + "=" * 60)
print("FIM DOS TESTES")
print("=" * 60)
