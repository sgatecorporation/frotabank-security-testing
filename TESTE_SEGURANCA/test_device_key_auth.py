"""
TESTE: Registro completo com Device Key Signature.
Descoberto via RE profunda do decompiled.js:

CAUSA DO 401 NO SEND-DOCUMENT:
O BankingCoreHttpClient adiciona 3 headers obrigatorios via setDeviceKeySignatureHeader():
  1. x-device-key-signature: base64(API_KEY:DEVICE_ID:UUID:SHA1(canonical):HMAC_SHA256(SHA1,privkey))
  2. x-device-key-headers: lista de headers separados por ;
  3. x-device-key-user-id: CPF

Sem esses headers, o nginx/WAF rejeita com 401.

ALGORITMO DA ASSINATURA:
1. Canonical string = httpVerb\ndomain\npath\n[body_params sorted]\n[headers sorted lowercase]
2. SHA1(canonical) -> sha1_hex
3. HMAC-SHA256(sha1_hex, privateKey) -> hmac_hex
4. Concat: apiKey:deviceId:uuid:sha1_hex:hmac_hex
5. base64(concat) -> signature
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

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

CPF = "41265599904"
PHONE = "11984636182"
PASSWORD = "Senh@2024!"
NAME = "JANDIRA STUCCHI"
MOTHER = "ANA AUGUSTA STUCCHI"
BIRTHDAY = "15/06/1962"
RG = "39824248"
CORR = uuid.uuid4().hex

DEVICE_UUID = str(uuid.uuid4())
DEVICE_ID = uuid.uuid4().hex[:16]
PRIVATE_KEY = None


def pinning_token():
    return jwt.encode(
        {"iss": PINNING_ISSUER, "iat": int(time.time())},
        PINNING_SECRET,
        algorithm="HS256",
    )


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


def device_key_signature(method, path, body=None, query=None, config_headers=None):
    if PRIVATE_KEY is None:
        return None, None, None
    domain = "api.c03.frotabank.com.br"
    canonical = build_canonical_string(method, domain, path, body, query, config_headers)
    sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    hmac_hex = hmac_mod.new(
        PRIVATE_KEY.encode("utf-8"), sha1_hex.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    sig_raw = f"{SAFEGUARD_API_KEY}:{DEVICE_ID}:{DEVICE_UUID}:{sha1_hex}:{hmac_hex}{sha1_hex}"
    signature = base64.b64encode(sig_raw.encode("utf-8")).decode("utf-8")
    existing_headers = ";".join(config_headers.keys()) if config_headers else ""
    return signature, existing_headers, CPF


def h(sid=None, bearer=None, method=None, path=None, body=None, query=None):
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
    if bearer:
        hh["Authorization"] = f"Bearer {bearer}"
    if method and path and PRIVATE_KEY:
        sig, hdrs, uid = device_key_signature(method, path, body, query, config_headers=None)
        if sig:
            hh["x-device-key-signature"] = sig
            hh["x-device-key-headers"] = hdrs
            hh["x-device-key-user-id"] = uid
    return hh


def to_iso(val):
    dd, mm, yyyy = val.strip().split("/")
    return f"{yyyy}-{mm}-{dd}T03:00:00.000Z"


http = tls_client.Session(
    client_identifier="okhttp4_android_13", random_tls_extension_order=True
)

print("=" * 70)
print("TESTE: REGISTRO COMPLETO COM DEVICE KEY SIGNATURE")
print("=" * 70)

# === PASSO 1: Verificacao telefone ===
print("\n[1] Enviar codigo de verificacao...")
r = http.post(
    f"{BASE}/v2/verification-code/send",
    json={
        "phone": PHONE,
        "verificationCodeType": "onboarding",
        "deliveryMethod": "whatsapp",
        "document": CPF,
    },
    headers=h(),
)
print(f"  Envio: {r.status_code}")

code = input("\n>>> CODIGO (WhatsApp): ").strip()

r = http.post(
    f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(),
    timeout_seconds=45,
)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  SessionId: {sid}")
t0 = time.time()

# === PASSO 2: CPF validation ===
print("\n[2] CPF validation...")
r = http.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid=sid))
print(f"  CPF: {r.status_code} | {r.text[:100]}")

# === PASSO 3: Terms + Zipcode ===
print("\n[3] Terms + Zipcode...")
r = http.get(
    f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy", headers=h(sid=sid)
)
terms = r.json() if r.status_code == 200 else []
terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]
print(f"  Terms: {r.status_code} ({len(terms_list)} termos)")

r = http.get(f"{BASE}/zipcode/80420000", headers=h(sid=sid))
addr = r.json() if r.status_code == 200 else {}
print(f"  Zipcode: {r.status_code}")

# === PASSO 4: Device key (SafeGuard) ===
print("\n[4] Device key (SafeGuard API)...")
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
print(f"  Device key: {r.status_code} | key={'OK' if PRIVATE_KEY else 'FAIL'}")
if PRIVATE_KEY:
    print(f"  PrivateKey: {PRIVATE_KEY[:40]}...")
    print(f"  DeviceId: {DEVICE_ID}")
    print(f"  UUID: {DEVICE_UUID}")

# === PASSO 5: Testar signature ===
print("\n[5] Testar device key signature...")
if PRIVATE_KEY:
    test_body = {
        "link": "https://example.com/selfie.jpg",
        "type": "selfie",
    }
    sig, hdrs, uid = device_key_signature("POST", "/v2/persons/send-document", test_body)
    canonical_test = build_canonical_string(
        "POST", "api.c03.frotabank.com.br", "/v2/persons/send-document", test_body
    )
    print(f"  Canonical string:\n    {repr(canonical_test)}")
    print(f"  Signature: {sig[:60]}...")
    print(f"  Headers list: '{hdrs}'")
    print(f"  User ID: {uid}")

# === PASSO 6: Validate selfie and document COM device key ===
print("\n[6] Validate selfie and document COM device key signature...")
validate_body = {
    "selfiePhotoUrl": "https://example.com/selfie.jpg",
    "frontDocumentPhotoUrl": "https://example.com/cnh_front.jpg",
    "backDocumentPhotoUrl": "https://example.com/cnh_back.jpg",
    "documentType": "cnh",
    "onlyValidation": True,
}
validate_path = "/v2/device-key/validate-selfie-and-document"

headers_validate = h(
    sid=sid, method="POST", path=validate_path, body=validate_body
)
r = http.post(
    f"{BASE}{validate_path}",
    json=validate_body,
    headers=headers_validate,
    timeout_seconds=15,
)
print(f"  Validate: {r.status_code} | {r.text[:200] or '(vazio - 204=OK)'}")

# === PASSO 7: send-document COM device key ===
print("\n" + "=" * 70)
print("[7] POST /v2/persons/send-document COM device key signature")
print("=" * 70)

send_bodies = [
    {"link": "https://example.com/selfie.jpg", "type": "selfie"},
    {"link": "https://example.com/cnh_front.jpg", "type": "digitalDriverLicense"},
]

for i, body in enumerate(send_bodies):
    send_path = "/v2/persons/send-document"
    headers_send = h(sid=sid, method="POST", path=send_path, body=body)
    print(f"\n  7{chr(97+i)}: Enviando {body['type']}...")
    print(f"    Body: {json.dumps(body)}")
    has_dk = "x-device-key-signature" in headers_send
    print(f"    Device key headers: {'SIM' if has_dk else 'NAO'}")
    if has_dk:
        print(f"    Signature: {headers_send['x-device-key-signature'][:60]}...")

    r = http.post(
        f"{BASE}{send_path}",
        json=body,
        headers=headers_send,
        timeout_seconds=15,
    )
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:300] or '(vazio)'}")

    if r.status_code == 401:
        print(f"\n    [!] Ainda 401! Tentando SEM body na canonical string...")
        sig2, _, _ = device_key_signature("POST", send_path, body=None)
        headers_send2 = h(sid=sid)
        if sig2:
            headers_send2["x-device-key-signature"] = sig2
            headers_send2["x-device-key-headers"] = ""
            headers_send2["x-device-key-user-id"] = CPF
        r2 = http.post(
            f"{BASE}{send_path}",
            json=body,
            headers=headers_send2,
            timeout_seconds=15,
        )
        print(f"    Sem body na canonical: {r2.status_code} | {r2.text[:200]}")

# === PASSO 8: POST /user ===
print("\n" + "=" * 70)
print("[8] POST /user")
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
    "email": "rikodocs@gmail.com",
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
headers_user = h(sid=sid, method="POST", path=user_path, body=user_payload)
r = http.post(
    f"{BASE}{user_path}",
    json=user_payload,
    headers=headers_user,
    timeout_seconds=30,
)
print(f"  POST /user: {r.status_code}")
print(f"  Body: {r.text[:1000]}")

user_created = r.status_code in (200, 201)

# === PASSO 9: Se conta criada, criar credenciais ===
if user_created:
    print("\n" + "=" * 70)
    print("[9] CONTA CRIADA! Enviando createCredential...")
    print("=" * 70)

    cred_code_body = {
        "verificationCodeType": "createCredential",
        "document": CPF,
        "phone": PHONE,
        "deliveryMethod": "whatsapp",
    }
    cred_path = "/v2/verification-code/send"
    headers_cred = h(sid=sid, method="POST", path=cred_path, body=cred_code_body)
    r = http.post(
        f"{BASE}{cred_path}",
        json=cred_code_body,
        headers=headers_cred,
        timeout_seconds=15,
    )
    print(f"  Envio createCredential: {r.status_code}")

    if r.status_code == 200:
        code2 = input("\n>>> CODIGO CREDENTIAL (WhatsApp): ").strip()

        auth_body = {
            "document": CPF,
            "password": PASSWORD,
            "verificationCode": code2,
        }
        auth_path = "/v2/auth/credential"
        headers_auth = h(sid=sid, method="POST", path=auth_path, body=auth_body)
        r = http.post(
            f"{BASE}{auth_path}",
            json=auth_body,
            headers=headers_auth,
            timeout_seconds=15,
        )
        print(f"  POST /v2/auth/credential: {r.status_code}")
        print(f"  Body: {r.text[:500]}")

        if r.status_code in (200, 201, 204):
            print("\n  *** CREDENCIAIS CRIADAS! ***")

            # Login
            print("\n[10] Login...")
            login_body = {"document": CPF, "password": PASSWORD}
            login_path = "/v2/auth/multifactor-login"
            headers_login = h(
                sid=sid, method="POST", path=login_path, body=login_body
            )
            r = http.post(
                f"{BASE}{login_path}",
                json=login_body,
                headers=headers_login,
                timeout_seconds=15,
            )
            print(f"  Login: {r.status_code}")
            print(f"  Body: {r.text[:500]}")

            if r.status_code == 200:
                token = r.json().get("token", "")
                if token:
                    print(f"\n  *** BEARER TOKEN: {token[:80]}... ***")
else:
    print(f"\n  POST /user falhou ({r.status_code})")
    if r.status_code == 400:
        try:
            err = r.json()
            print(f"  Erro code: {err.get('code', 'N/A')}")
            print(f"  Erro msg: {err.get('message', 'N/A')}")
        except Exception:
            pass

elapsed = time.time() - t0
print(f"\n  Tempo total: {elapsed:.1f}s")
print("\n" + "=" * 70)
print("FIM")
print("=" * 70)
