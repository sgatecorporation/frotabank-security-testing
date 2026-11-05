"""
TESTE V5: CPF NOVO + userInfo completo no validate-selfie.

CORRECOES vs V4:
1. Gera CPF aleatorio valido (o CPF antigo pode estar em estado avancado no servidor)
2. Adiciona userInfo no body do validate-selfie: userDocument, userFullName, userBirthdate
3. Segue o fluxo EXATO do app: upload → validate-selfie → send-document
4. HMAC correto: config.headers vazio para send-document (app behavior)

FLUXO DO APP (onConfirmPicture):
  1. Phone verify → sessionId
  2. CPF + Terms
  3. Criar device key (SafeGuard) → privateKey (status: "created")
  4. Upload docs (multipart SEM DK) → URLs S3
  5. validate-selfie-and-document (COM DK + userInfo) → valida device key
  6. send-document para cada doc (COM DK)
  7. POST /user
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
import re
import struct
import io
import random


BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

PHONE = "11984636182"
PASSWORD = "Senh@2024!"
CORR = uuid.uuid4().hex

DEVICE_UUID = str(uuid.uuid4())
DEVICE_ID = uuid.uuid4().hex[:16]
PRIVATE_KEY = None

DEBUG = True


# ---- CPF Generator ----

def generate_cpf():
    """Gera CPF aleatorio valido (11 digitos com digitos verificadores corretos)."""
    digits = [random.randint(0, 9) for _ in range(9)]
    # Evitar CPFs com todos digitos iguais (invalidos)
    while len(set(digits)) == 1:
        digits = [random.randint(0, 9) for _ in range(9)]
    # Primeiro digito verificador
    s = sum(d * w for d, w in zip(digits, range(10, 1, -1)))
    d1 = 11 - (s % 11)
    d1 = 0 if d1 >= 10 else d1
    digits.append(d1)
    # Segundo digito verificador
    s = sum(d * w for d, w in zip(digits, range(11, 1, -1)))
    d2 = 11 - (s % 11)
    d2 = 0 if d2 >= 10 else d2
    digits.append(d2)
    return "".join(str(d) for d in digits)


# ---- JPEG minimo ----

def make_minimal_jpeg():
    buf = io.BytesIO()
    buf.write(b'\xff\xd8\xff\xe0')
    buf.write(struct.pack('>H', 16))
    buf.write(b'JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
    buf.write(b'\xff\xdb\x00\x43\x00')
    buf.write(bytes([8] * 64))
    buf.write(b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00')
    buf.write(b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01'
              b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04'
              b'\x05\x06\x07\x08\x09\x0a\x0b')
    buf.write(b'\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\x7b\x40')
    buf.write(b'\xff\xd9')
    return buf.getvalue()


# ---- Pinning ----

def pinning_token():
    return jwt.encode(
        {"iss": PINNING_ISSUER, "iat": int(time.time())},
        PINNING_SECRET,
        algorithm="HS256",
    )


# ---- Canonical string / HMAC ----

def traverse(obj, parent_keys=None, result=None):
    if parent_keys is None:
        parent_keys = []
    if result is None:
        result = []
    if obj is None:
        return result
    for key in obj:
        val = obj[key]
        if val is None:
            continue
        path = parent_keys + [str(key)]
        if isinstance(val, dict):
            traverse(val, path, result)
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    traverse(item, path + [str(i)], result)
                elif item is not None:
                    result.append(f"{'.'.join(path + [str(i)])}={item}")
        elif isinstance(val, bool):
            result.append(f"{'.'.join(path)}={'true' if val else 'false'}")
        else:
            result.append(f"{'.'.join(path)}={val}")
    return result


def generate_param_string(obj):
    entries = traverse(obj)
    entries.sort()
    return "\n".join(entries)


def generate_case_insensitive_param_string(obj):
    entries = traverse(obj)
    lowered = []
    for entry in entries:
        idx = entry.index("=")
        lowered.append(entry[:idx].lower() + entry[idx:])
    lowered.sort()
    return "\n".join(lowered)


def build_canonical_string(method, domain, path, body=None, query=None, headers=None):
    if headers:
        headers = {k: v for k, v in headers.items() if k.lower() != "sg-signature"}
    parts = [method.upper(), domain.lower(), path]
    if query and len(query) > 0:
        parts.append(generate_param_string(query))
    if body and len(body) > 0:
        parts.append(generate_param_string(body))
    if headers and len(headers) > 0:
        parts.append(generate_case_insensitive_param_string(headers))
    return "\n".join(parts)


def device_key_signature(method, path, cpf, body=None, query=None, config_headers=None):
    """Computa device key HMAC signature.

    config_headers: headers do config da request (NAO os HTTP defaults).
    Para send-document: {} (vazio) → sem headers no HMAC, sem x-device-key-headers.
    Para upload: {'Content-Type':'multipart/form-data'} → so esse header no HMAC.
    """
    if PRIVATE_KEY is None:
        return None, None, None
    domain = "api.c03.frotabank.com.br"
    canonical = build_canonical_string(method, domain, path, body, query, config_headers)
    if DEBUG:
        lines = canonical.split("\n")
        print(f"\n  [HMAC] Canonical ({len(canonical)} chars, {len(lines)} lines):")
        for i, line in enumerate(lines):
            if i < 5 or i >= len(lines) - 2:
                print(f"    {i}: {line[:120]}")
            elif i == 5:
                print(f"    ... ({len(lines)} total)")
    sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    hmac_hex = hmac_mod.new(
        PRIVATE_KEY.encode("utf-8"), sha1_hex.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    sig_raw = f"{SAFEGUARD_API_KEY}:{DEVICE_ID}:{DEVICE_UUID}:{sha1_hex}:{hmac_hex}{sha1_hex}"
    signature = base64.b64encode(sig_raw.encode("utf-8")).decode("utf-8")
    existing_header_keys = ";".join(config_headers.keys()) if config_headers else ""
    return signature, existing_header_keys, cpf


# ---- Headers ----

def base_http_headers(sid=None, bearer=None):
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


def h_simple(sid=None, bearer=None):
    hh = base_http_headers(sid, bearer)
    hh["sg-signature"] = pinning_token()
    return hh


def h_with_dk(cpf, sid=None, method=None, path=None, body=None, query=None,
              config_headers=None):
    """Headers com device key signature.

    config_headers: headers do config Axios (nao os defaults HTTP).
    O app passa config.headers = null para send-document → HMAC sem headers.
    O app passa config.headers = {'Content-Type':'multipart/form-data'} para upload.
    """
    base = base_http_headers(sid)

    if PRIVATE_KEY and method and path:
        hmac_hdrs = dict(config_headers) if config_headers else {}

        sig, hdrs, uid = device_key_signature(
            method, path, cpf, body, query, config_headers=hmac_hdrs
        )
        if sig:
            if hdrs:  # so adiciona x-device-key-headers se nao vazio
                base["x-device-key-headers"] = hdrs
            base["x-device-key-signature"] = sig
            if uid:
                base["x-device-key-user-id"] = uid

    base["sg-signature"] = pinning_token()

    if config_headers:
        for k, v in config_headers.items():
            base[k] = v

    return base


def make_multipart_body(file_data, filename="document.jpg", content_type="image/jpeg"):
    boundary = "----FormBoundary" + uuid.uuid4().hex[:16]
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.write(f"Content-Type: {content_type}\r\n".encode())
    body.write(b"\r\n")
    body.write(file_data)
    body.write(f"\r\n--{boundary}--\r\n".encode())
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"


def to_iso(val):
    dd, mm, yyyy = val.strip().split("/")
    return f"{yyyy}-{mm}-{dd}T03:00:00.000Z"


# ================ MAIN ================

http = tls_client.Session(
    client_identifier="okhttp4_android_13", random_tls_extension_order=True
)

# Gerar CPF novo ou usar um especifico
CPF = generate_cpf()
print("=" * 70)
print("TESTE V5: CPF NOVO + USERINFO COMPLETO")
print("=" * 70)
print(f"  CPF gerado: {CPF}")
print(f"  DeviceId:   {DEVICE_ID}")
print(f"  UUID:       {DEVICE_UUID}")

custom_cpf = input("\n>>> Usar CPF customizado? (Enter para usar o gerado, ou digite o CPF): ").strip()
if custom_cpf:
    CPF = re.sub(r"\D", "", custom_cpf)
    print(f"  Usando CPF: {CPF}")

NAME = "CARLOS EDUARDO SILVA"
MOTHER = "MARIA APARECIDA SILVA"
BIRTHDAY = "22/03/1990"
RG = "48571632"

# === PASSO 1: Phone verify ===
print("\n[1] Enviar codigo onboarding...")
r = http.post(
    f"{BASE}/v2/verification-code/send",
    json={
        "phone": PHONE,
        "verificationCodeType": "onboarding",
        "deliveryMethod": "whatsapp",
        "document": CPF,
    },
    headers=h_simple(),
)
print(f"  Envio: {r.status_code}")
if r.status_code != 200:
    print(f"  Resp: {r.text[:300]}")
    if r.status_code >= 400:
        print("  ERRO: nao conseguiu enviar codigo. CPF pode ser invalido no servidor.")
        sys.exit(1)

code = input("\n>>> CODIGO ONBOARDING: ").strip()
r = http.post(
    f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h_simple(),
    timeout_seconds=45,
)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:300]}")
    sys.exit(1)
print(f"  SessionId: {sid}")
t0 = time.time()

# === PASSO 2: CPF + Terms ===
print("\n[2] CPF + Terms...")
r = http.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h_simple(sid))
print(f"  CPF validation: {r.status_code} | {r.text[:200]}")

r = http.get(
    f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy",
    headers=h_simple(sid),
)
terms = r.json() if r.status_code == 200 else []
terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]
print(f"  Terms: {r.status_code} ({len(terms_list)} items)")

r = http.get(f"{BASE}/zipcode/80420000", headers=h_simple(sid))
addr = r.json() if r.status_code == 200 else {}
print(f"  Zipcode: {r.status_code}")

# === PASSO 3: Criar device key ===
print("\n[3] Criar device key (SafeGuard)...")
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
dk_data = r.json() if r.status_code in (200, 201) else {}
PRIVATE_KEY = dk_data.get("privateKey", "")
if not PRIVATE_KEY:
    print(f"  ERRO: {r.text[:300]}")
    sys.exit(1)
print(f"  OK: privateKey={PRIVATE_KEY[:40]}...")

# Check initial status
r = http.get(
    f"{SAFEGUARD_API_URL}device_key/status?uuid={DEVICE_UUID}&deviceId={DEVICE_ID}",
    headers={"SG-API-KEY": SAFEGUARD_API_KEY},
)
print(f"  Status inicial: {r.text[:100]}")

# === PASSO 4: Upload documentos (multipart SEM device key) ===
print("\n" + "=" * 70)
print("[4] UPLOAD DOCUMENTOS (multipart SEM device key)")
print("=" * 70)

jpeg_data = make_minimal_jpeg()
uploaded_urls = {}
doc_types = ["selfie", "cnhFront", "cnhBack"]

for doc_type in doc_types:
    upload_path = "/user/documents/upload"
    mp_body, mp_content_type = make_multipart_body(jpeg_data, f"{doc_type}.jpg")

    headers_up = h_simple(sid)
    headers_up["content-type"] = mp_content_type

    r = http.post(
        f"{BASE}{upload_path}",
        data=mp_body,
        headers=headers_up,
        timeout_seconds=30,
    )
    if r.status_code in (200, 201):
        resp = r.json()
        url = resp.get("url") or resp.get("downloadUrl") or resp.get("link", "")
        uploaded_urls[doc_type] = url
        print(f"  {doc_type}: OK → {url[:70]}...")
    else:
        print(f"  {doc_type}: FALHOU {r.status_code} | {r.text[:150]}")
        uploaded_urls[doc_type] = ""

selfie_url = uploaded_urls.get("selfie", "")
front_url = uploaded_urls.get("cnhFront", "")
back_url = uploaded_urls.get("cnhBack", "")
all_uploaded = selfie_url and front_url and back_url
print(f"\n  Uploads OK: {all_uploaded}")

# === PASSO 5: validate-selfie-and-document (COM userInfo!) ===
print("\n" + "=" * 70)
print("[5] validate-selfie-and-document (COM userInfo)")
print("=" * 70)

validate_path = "/v2/device-key/validate-selfie-and-document"

# Body COMPLETO conforme decompiled: Object.assign({}, deviceInfo, userInfo, {document, urls, onlyValidation})
validate_body = {
    # deviceInfo (de getDeviceKeyInstallation)
    "uuid": DEVICE_UUID,
    "deviceId": DEVICE_ID,
    # userInfo (de props)
    "userDocument": CPF,
    "userFullName": NAME,
    "userBirthdate": to_iso(BIRTHDAY),
    # campos explicitos
    "document": CPF,
    "selfieUrl": selfie_url or "https://placeholder.test/selfie.jpg",
    "frontDocumentPhotoUrl": front_url or "https://placeholder.test/front.jpg",
    "backDocumentPhotoUrl": back_url or "https://placeholder.test/back.jpg",
    "onlyValidation": True,
}

# O app usa bankingCoreHttpClient.request() que passa config sem headers explicitos
# → config.headers = null → HMAC sem headers no canonical string
# Mas o body TEM conteudo → body incluido no HMAC

print("\n  [5a] DK com config.headers vazio (app behavior)...")
headers_5a = h_with_dk(
    CPF, sid=sid, method="POST", path=validate_path, body=validate_body,
    config_headers={},
)
r = http.post(f"{BASE}{validate_path}", json=validate_body, headers=headers_5a, timeout_seconds=15)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:500] or '(vazio - 204=OK)'}")
dk_validated = r.status_code in (200, 201, 204)

if not dk_validated:
    print("\n  [5b] SEM device key headers...")
    r = http.post(f"{BASE}{validate_path}", json=validate_body, headers=h_simple(sid), timeout_seconds=15)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:500]}")
    dk_validated = r.status_code in (200, 201, 204)

# === PASSO 5c: validate-with-code (fallback) ===
if not dk_validated:
    print("\n  [5c] Fallback: validate-with-code (deviceKeyLight)...")
    r = http.post(
        f"{BASE}/v2/verification-code/send",
        json={
            "phone": PHONE,
            "verificationCodeType": "deviceKeyLight",
            "deliveryMethod": "whatsapp",
            "document": CPF,
        },
        headers=h_simple(sid),
    )
    print(f"  Envio deviceKeyLight: {r.status_code}")
    if r.status_code == 200:
        code2 = input("\n>>> CODIGO DEVICE KEY LIGHT: ").strip()
        vwc_body = {
            "uuid": DEVICE_UUID,
            "deviceId": DEVICE_ID,
            "document": CPF,
            "phone": PHONE,
            "verificationCode": code2,
        }
        vwc_path = "/v2/device-key/validate-with-code"

        # Sem DK (o endpoint pode nao precisar)
        print("  [i] validate-with-code SEM DK...")
        r = http.post(f"{BASE}{vwc_path}", json=vwc_body, headers=h_simple(sid), timeout_seconds=15)
        print(f"    Status: {r.status_code} | {r.text[:300] or '(vazio)'}")
        dk_validated = r.status_code in (200, 201, 204)

        if not dk_validated:
            # Com DK (config.headers vazio)
            print("  [ii] validate-with-code COM DK (config vazio)...")
            headers_vwc = h_with_dk(
                CPF, sid=sid, method="POST", path=vwc_path, body=vwc_body,
                config_headers={},
            )
            r = http.post(f"{BASE}{vwc_path}", json=vwc_body, headers=headers_vwc, timeout_seconds=15)
            print(f"    Status: {r.status_code} | {r.text[:300] or '(vazio)'}")
            dk_validated = r.status_code in (200, 201, 204)
    else:
        print(f"  Envio falhou: {r.text[:200]}")

# Check SafeGuard status
print("\n  [5d] SafeGuard status...")
r = http.get(
    f"{SAFEGUARD_API_URL}device_key/status?uuid={DEVICE_UUID}&deviceId={DEVICE_ID}",
    headers={"SG-API-KEY": SAFEGUARD_API_KEY},
)
sg_status = ""
try:
    sg_data = r.json()
    sg_status = sg_data.get("status", "")
    print(f"  Status: {sg_status} | Full: {json.dumps(sg_data)[:200]}")
except Exception:
    print(f"  Raw: {r.text[:200]}")
dk_validated = dk_validated or sg_status == "validated"

print(f"\n  >>> Device key validado: {dk_validated}")

# === PASSO 6: send-document ===
print("\n" + "=" * 70)
print(f"[6] send-document (dk_validated={dk_validated})")
print("=" * 70)

send_path = "/v2/persons/send-document"
send_docs = [
    {"link": selfie_url, "type": "selfie"},
    {"link": front_url, "type": "cnhFront"},
    {"link": back_url, "type": "cnhBack"},
]

for i, sd_body in enumerate(send_docs):
    if not sd_body["link"]:
        print(f"  [{i}] {sd_body['type']}: SKIP (sem URL)")
        continue
    label = chr(97 + i)

    # App behavior: config.headers = null → HMAC sem headers
    print(f"\n  [6{label}] {sd_body['type']} (DK, config vazio)...")
    headers_sd = h_with_dk(
        CPF, sid=sid, method="POST", path=send_path, body=sd_body,
        config_headers={},
    )
    r = http.post(f"{BASE}{send_path}", json=sd_body, headers=headers_sd, timeout_seconds=15)
    print(f"    Status: {r.status_code} | {r.text[:300] or '(vazio)'}")
    if r.status_code in (200, 201, 204):
        print(f"    *** SUCESSO! ***")
        continue

    # Fallback: sem DK
    print(f"  [6{label}-b] {sd_body['type']} SEM DK...")
    r = http.post(f"{BASE}{send_path}", json=sd_body, headers=h_simple(sid), timeout_seconds=15)
    print(f"    Status: {r.status_code} | {r.text[:300] or '(vazio)'}")
    if r.status_code in (200, 201, 204):
        print(f"    *** SUCESSO! ***")

# === PASSO 7: POST /user ===
print("\n" + "=" * 70)
print("[7] POST /user")
print("=" * 70)

user_payload = {
    "addresses": [
        {
            "zipCode": "80420000",
            "street": addr.get("street", "Rua Comendador Araujo"),
            "number": "252",
            "complement": "",
            "neighborhood": addr.get("neighborhood", "Centro"),
            "city": addr.get("city", "Curitiba"),
            "state": addr.get("state", "PR"),
        }
    ],
    "birthday": to_iso(BIRTHDAY),
    "documentNumber": CPF,
    "email": "testeseg" + CPF[:6] + "@gmail.com",
    "name": NAME,
    "newsletterAccept": False,
    "password": PASSWORD,
    "phone": re.sub(r"\D", "", PHONE),
    "terms": terms_list,
    "isPEP": False,
    "monthlyIncome": 5000,
    "motherName": MOTHER,
    "professionId": 1,
    "type": "person",
    "partners": [],
    "deviceKeyInstallation": {"uuid": DEVICE_UUID, "deviceId": DEVICE_ID},
    "rg": RG,
    "rgIssuingDate": to_iso("14/10/2022"),
}

user_path = "/user"
# DK com config vazio (app behavior)
headers_u = h_with_dk(
    CPF, sid=sid, method="POST", path=user_path, body=user_payload,
    config_headers={},
)
r = http.post(f"{BASE}{user_path}", json=user_payload, headers=headers_u, timeout_seconds=30)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:800]}")

if r.status_code == 401:
    print("\n  Tentando SEM DK...")
    r = http.post(f"{BASE}{user_path}", json=user_payload, headers=h_simple(sid), timeout_seconds=30)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:800]}")

user_created = r.status_code in (200, 201)
if user_created:
    print("\n  *** CONTA CRIADA! ***")
    print("\n[8] createCredential...")
    r = http.post(
        f"{BASE}/v2/verification-code/send",
        json={
            "verificationCodeType": "createCredential",
            "document": CPF,
            "phone": PHONE,
            "deliveryMethod": "whatsapp",
        },
        headers=h_simple(sid),
        timeout_seconds=15,
    )
    print(f"  Envio: {r.status_code}")
    if r.status_code == 200:
        code3 = input("\n>>> CODIGO CREDENTIAL: ").strip()
        r = http.post(
            f"{BASE}/v2/auth/credential",
            json={"document": CPF, "password": PASSWORD, "verificationCode": code3},
            headers=h_simple(sid),
            timeout_seconds=15,
        )
        print(f"  Credential: {r.status_code} | {r.text[:300]}")
        if r.status_code in (200, 201, 204):
            print("\n[9] Login...")
            r = http.post(
                f"{BASE}/v2/auth/multifactor-login",
                json={"document": CPF, "password": PASSWORD},
                headers=h_simple(sid),
                timeout_seconds=15,
            )
            print(f"  Login: {r.status_code}")
            if r.status_code == 200:
                token = r.json().get("token", "")
                if token:
                    print(f"  BEARER: {token[:80]}...")
else:
    print(f"\n  POST /user falhou ({r.status_code})")
    try:
        err = r.json()
        print(f"  Code: {err.get('error', {}).get('code', err.get('code', 'N/A'))}")
        print(f"  Msg: {err.get('error', {}).get('message', err.get('message', 'N/A'))}")
    except Exception:
        pass

elapsed = time.time() - t0
print(f"\n  Tempo total: {elapsed:.1f}s")
print("\n" + "=" * 70)
print(f"  CPF usado: {CPF}")
print(f"  Device UUID: {DEVICE_UUID}")
print(f"  Device ID: {DEVICE_ID}")
print("FIM")
print("=" * 70)
