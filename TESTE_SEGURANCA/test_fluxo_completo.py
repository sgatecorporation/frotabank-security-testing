"""
Fluxo COMPLETO de registro seguindo a ordem EXATA do app:
1. Phone verification → sessionId
2. CPF validation
3. Upload documentos → URLs
4. Create device key (SafeGuard)
5. POST /v2/device-key/validate-selfie-and-document  ← ETAPA QUE FALTAVA!
6. POST /v2/persons/send-document (para cada doc)
7. POST /user
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
EMAIL = "rikodocs@gmail.com"
RG = "39824248"
RG_DATE = "14/10/2022"
NOME = "JANDIRA STUCCHI"
BIRTHDAY = "15/06/1962"
MOTHER = "ANA AUGUSTA STUCCHI"
CEP = "80420000"
NUMERO = "252"
COMPLEMENTO = ""
PROF_ID = 1
MONTHLY_INCOME = 5000
PASSWORD = "Senh@2024!"
CNH_PATH = r"C:\Users\Acer\Documents\XuanZhi9\Pictures\CNH-e.pdf.pdf"
SELFIE_PATH = r"C:\Users\Acer\Documents\XuanZhi9\Pictures\WhatsApp Image 2026-09-15 at 09.11.07.jpeg"

http = requests.Session()
http.timeout = 30
http2 = curl_requests.Session(impersonate="chrome120", timeout=30)
CORR = uuid.uuid4().hex


def pt():
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
        "sg-signature": pt(),
        "x-device-coords-latitude": "-25.4284",
        "x-device-coords-longitude": "-49.2733",
        "x-device-coords-altitude": "0",
        "x-device-coords-speed": "0",
    }


def to_iso(val):
    dd, mm, yyyy = val.strip().split("/")
    return f"{yyyy}-{mm}-{dd}T03:00:00.000Z"


def clean(v):
    return re.sub(r"\D", "", v)


def sg_h():
    return {"SG-API-KEY": SAFEGUARD_API_KEY, "Content-Type": "application/json"}


def _traverse(obj, parent_keys=None, result=None):
    if parent_keys is None: parent_keys = []
    if result is None: result = []
    items = obj.items() if isinstance(obj, dict) else enumerate(obj) if isinstance(obj, list) else []
    for key, value in items:
        key_path = parent_keys + [str(key)]
        if value is not None and isinstance(value, (dict, list)) and len(value) > 0:
            _traverse(value, key_path, result)
        else:
            v = "null" if value is None else ("true" if value is True else ("false" if value is False else str(value)))
            result.append(".".join(key_path) + "=" + v)
    return result


def gen_sig(device_key, device_id, device_uuid, method, url, body=None, headers_dict=None):
    parsed = urlparse(url)
    domain = parsed.hostname.lower()
    path = parsed.path or "/"
    parts = [method.upper(), domain, path]
    if body and len(body) > 0:
        pairs = _traverse(body)
        pairs.sort()
        parts.append("\n".join(pairs))
    if headers_dict and len(headers_dict) > 0:
        skip = {"sg-signature", "x-device-key-headers", "x-device-key-signature", "x-device-key-user-id"}
        clean_h = {k: v for k, v in headers_dict.items() if k.lower() not in skip}
        if clean_h:
            pairs = _traverse(clean_h)
            lowered = []
            for pair in pairs:
                eq_idx = pair.index("=")
                lowered.append(pair[:eq_idx].lower() + pair[eq_idx:])
            lowered.sort()
            parts.append("\n".join(lowered))
    canonical = "\n".join(parts)
    sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    hmac_hex = hmac_module.new(device_key.encode("utf-8"), sha1_hex.encode("utf-8"), hashlib.sha256).hexdigest()
    return base64.b64encode(f"{SAFEGUARD_API_KEY}:{device_id}:{device_uuid}:{sha1_hex}:{hmac_hex}{sha1_hex}".encode()).decode()


print("=" * 60)
print("FROTABANK - FLUXO COMPLETO DE REGISTRO")
print("=" * 60)

# === PASSO 1: Phone verification ===
print("\n[1] Enviar codigo WhatsApp...")
r = http2.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h())
print(f"  Status: {r.status_code}")

code = input("\n>>> CODIGO WHATSAPP: ").strip()

print("\n[2] Confirmar codigo...")
r = http2.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code}, headers=h(), timeout=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  SESSION: {sid}")

# === PASSO 2: CPF validation ===
print("\n[3] CPF validation...")
r = http2.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid))
print(f"  Status: {r.status_code} | {r.text[:200]}")

# === PASSO 3: Upload documentos ===
print("\n[4] Upload documentos...")
doc_uploads = []
for dtype, fpath, mime in [
    ("DIGITAL_DRIVER_LICENSE", CNH_PATH, "application/pdf"),
    ("SELFIE", SELFIE_PATH, "image/jpeg"),
]:
    print(f"  {dtype}...", end=" ")
    hh = h(sid)
    del hh["content-type"]
    with open(fpath, "rb") as f:
        data = f.read()
    ext = "pdf" if "pdf" in mime else "jpg"
    r = http.post(f"{BASE}/user/documents/upload", headers=hh,
        files={"file": (f"{dtype}.{ext}", data, mime)},
        data={"documentType": dtype}, timeout=60)
    if r.status_code == 200:
        url = r.json().get("url", "")
        doc_uploads.append({"url": url, "downloadUrl": url, "documentType": dtype})
        print(f"OK")
    else:
        print(f"FALHOU {r.status_code}: {r.text[:100]}")
        doc_uploads.append({"url": "https://example.com/test", "downloadUrl": "https://example.com/test", "documentType": dtype})
print(f"  Uploads: {len(doc_uploads)}")

selfie_url = next((d["url"] for d in doc_uploads if d["documentType"] == "SELFIE"), "")
front_doc_url = next((d["url"] for d in doc_uploads if d["documentType"] != "SELFIE"), "")
print(f"  Selfie URL: {selfie_url[:60]}...")
print(f"  Front Doc URL: {front_doc_url[:60]}...")

# === PASSO 4: Create device key ===
print("\n[5] Create device key (SafeGuard)...")
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
    print(f"  privateKey: {len(device_key)} chars")
    print(f"  uuid: {device_uuid}")
    print(f"  deviceId: {device_id}")
else:
    print(f"  FALHOU: {r.text[:200]}")
    sys.exit(1)

# === PASSO 5: POST /v2/device-key/validate-selfie-and-document ===
# ESTA É A ETAPA QUE FALTAVA!
# O app chama authorizeWithSelfieAndDocument → validateWithSelfieAndDocument
# que envia POST /v2/device-key/validate-selfie-and-document
print("\n" + "=" * 60)
print("[6] POST /v2/device-key/validate-selfie-and-document")
print("    (ETAPA CRITICA - validação do device key)")
print("=" * 60)

validate_payload = {
    "uuid": device_uuid,
    "deviceId": device_id,
    "userDocument": clean(RG),
    "userFullName": NOME,
    "userBirthdate": to_iso(BIRTHDAY),
    "selfieUrl": selfie_url,
    "frontDocumentPhotoUrl": front_doc_url,
    "backDocumentPhotoUrl": None,
    "onlyValidation": True,
}
print(f"  Payload: {json.dumps(validate_payload, indent=2, default=str)[:500]}")

r = http2.post(f"{BASE}/v2/device-key/validate-selfie-and-document",
    json=validate_payload, headers=h(sid), timeout=60)
print(f"\n  Status: {r.status_code}")
print(f"  Body: {r.text[:500]}")
print(f"  Headers: {dict(r.headers)}")

if r.status_code == 401:
    print("\n  TAMBEM retornou 401! Testando variações...")

    # Teste B: com device key signature
    if device_key:
        print("\n  [6B] Com device key signature...")
        url_validate = f"{BASE}/v2/device-key/validate-selfie-and-document"
        sig = gen_sig(device_key, device_id, device_uuid, "POST", url_validate, body=validate_payload)
        hh = h(sid)
        hh["x-device-key-signature"] = sig
        hh["x-device-key-user-id"] = CPF
        r = http2.post(url_validate, json=validate_payload, headers=hh, timeout=60)
        print(f"  Status: {r.status_code} | Body: {r.text[:300]}")

    # Teste C: testar OUTROS endpoints /v2/ para ver se TODOS dão 401
    print("\n  [6C] Testando outros endpoints /v2/...")
    for ep in ["/v2/terms?types[]=TermsOfUse", "/v2/personstatus", "/v2/persons"]:
        method = "get" if "terms" in ep else "post"
        body_ep = {"document": CPF} if "personstatus" in ep else None
        if method == "get":
            r = http2.get(f"{BASE}{ep}", headers=h(sid), timeout=15)
        else:
            r = http2.post(f"{BASE}{ep}", json=body_ep, headers=h(sid), timeout=15)
        print(f"    {method.upper()} {ep}: {r.status_code} | {r.text[:100]}")

elif r.status_code in (200, 201):
    print("\n  VALIDACAO OK! Continuando...")

    # === PASSO 6: POST /v2/persons/send-document ===
    print("\n[7] POST /v2/persons/send-document...")
    for doc in doc_uploads:
        print(f"  Enviando {doc['documentType']}...")
        doc_type_camel = {
            "DIGITAL_DRIVER_LICENSE": "digitalDriverLicense",
            "SELFIE": "selfie",
            "IDENTITY_FRONT": "identityFront",
            "IDENTITY_BACK": "identityBack",
        }.get(doc["documentType"], doc["documentType"])

        send_body = {"link": doc["downloadUrl"], "type": doc_type_camel}
        r = http2.post(f"{BASE}/v2/persons/send-document", json=send_body, headers=h(sid), timeout=30)
        print(f"    Status: {r.status_code} | Body: {r.text[:200]}")

    # === PASSO 7: POST /user ===
    print("\n[8] POST /user - CRIANDO CONTA...")
    r = http2.get(f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy", headers=h(sid))
    terms = r.json() if r.status_code == 200 else []
    terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]

    r = http2.get(f"{BASE}/zipcode/{CEP}", headers=h(sid))
    addr_data = r.json() if r.status_code == 200 else {}

    user_payload = {
        "addresses": [{
            "zipCode": CEP, "street": addr_data.get("street", "Rua Comendador Araujo"),
            "number": NUMERO, "complement": COMPLEMENTO,
            "neighborhood": addr_data.get("neighborhood", "Centro"),
            "city": addr_data.get("city", "Curitiba"), "state": addr_data.get("state", "PR"),
        }],
        "birthday": to_iso(BIRTHDAY),
        "documentNumber": CPF,
        "email": EMAIL,
        "name": NOME,
        "newsletterAccept": False,
        "password": PASSWORD,
        "phone": clean(PHONE),
        "terms": terms_list,
        "isPEP": False,
        "monthlyIncome": MONTHLY_INCOME,
        "motherName": MOTHER,
        "professionId": PROF_ID,
        "type": "person",
        "partners": [],
        "deviceKeyInstallation": {"uuid": device_uuid, "deviceId": device_id},
        "rg": clean(RG),
        "rgIssuingDate": to_iso(RG_DATE),
    }

    r = http2.post(f"{BASE}/user", json=user_payload, headers=h(sid), timeout=60)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:500]}")
else:
    print(f"\n  Resposta inesperada: {r.status_code}")
    print(f"  Body completo: {r.text[:1000]}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
