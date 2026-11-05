"""
TESTE: Fluxo RAPIDO de registro - todos passos em sequencia rapida.
Hipotese: POST /user falhou antes por session expired, nao por falta de send-document.
Se POST /user funcionar -> createCredential -> login -> Bearer -> testar /v2/persons/*

Fluxo:
1. Verificacao telefone -> sessionId
2. CPF validation
3. Terms + Zipcode
4. Device key (SafeGuard)
5. Validate selfie and document
6. POST /user (SEM send-document)
7. Se 200/201 -> enviar createCredential code -> POST /v2/auth/credential
8. Login -> Bearer -> testar /v2/persons/*
"""
import tls_client
import uuid, json, time, jwt, re, sys

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


def to_iso(val):
    dd, mm, yyyy = val.strip().split("/")
    return f"{yyyy}-{mm}-{dd}T03:00:00.000Z"


http = tls_client.Session(client_identifier="okhttp4_android_13", random_tls_extension_order=True)

print("=" * 60)
print("TESTE: FLUXO RAPIDO (sem send-document)")
print("=" * 60)

# === PASSO 1: Verificacao telefone ===
print("\n[1] Enviar codigo de verificacao...")
r = http.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h())
print(f"  Envio: {r.status_code}")

code = input("\n>>> CODIGO (WhatsApp): ").strip()

r = http.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(), timeout_seconds=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  SessionId: {sid}")
t0 = time.time()

# === PASSO 2: CPF validation (RAPIDO) ===
print("\n[2] CPF validation...")
r = http.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid=sid))
print(f"  CPF: {r.status_code} | {r.text[:100]}")

# === PASSO 3: Terms + Zipcode ===
print("\n[3] Terms + Zipcode...")
r = http.get(f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy", headers=h(sid=sid))
terms = r.json() if r.status_code == 200 else []
terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]
print(f"  Terms: {r.status_code} ({len(terms_list)} termos)")

r = http.get(f"{BASE}/zipcode/80420000", headers=h(sid=sid))
addr = r.json() if r.status_code == 200 else {}
print(f"  Zipcode: {r.status_code}")

# === PASSO 4: Device key (SafeGuard) ===
print("\n[4] Device key...")
device_uuid = str(uuid.uuid4())
device_id = uuid.uuid4().hex[:16]

r = http.post(f"{SAFEGUARD_API_URL}device_key",
    json={"deviceId": device_id, "isRoot": False, "userId": CPF,
          "uuid": device_uuid, "userMetadata": None, "operatingSystem": "android"},
    headers={"SG-API-KEY": SAFEGUARD_API_KEY, "Content-Type": "application/json"})
dk_data = r.json() if r.status_code in (200, 201) else {}
dk = dk_data.get("privateKey", "")
print(f"  Device key: {r.status_code} | key={'OK' if dk else 'FAIL'}")

# === PASSO 5: Validate selfie and document ===
print("\n[5] Validate selfie and document...")
validate_payload = {
    "selfiePhotoUrl": "https://example.com/selfie.jpg",
    "frontDocumentPhotoUrl": "https://example.com/cnh_front.jpg",
    "backDocumentPhotoUrl": "https://example.com/cnh_back.jpg",
    "documentType": "cnh",
    "onlyValidation": True,
}
r = http.post(f"{BASE}/v2/device-key/validate-selfie-and-document",
    json=validate_payload, headers=h(sid=sid), timeout_seconds=15)
print(f"  Validate: {r.status_code} | {r.text[:200] or '(vazio - 204 = OK)'}")

# === PASSO 6: POST /user (SEM send-document) ===
elapsed = time.time() - t0
print(f"\n[6] POST /user (tempo desde sessao: {elapsed:.1f}s)...")

user_payload = {
    "addresses": [{
        "zipCode": "80420000",
        "street": addr.get("street", "Rua Comendador Araujo"),
        "number": "252",
        "complement": "",
        "neighborhood": addr.get("neighborhood", "Centro"),
        "city": addr.get("city", "Curitiba"),
        "state": addr.get("state", "PR"),
    }],
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
    "deviceKeyInstallation": {"uuid": device_uuid, "deviceId": device_id},
    "rg": RG,
    "rgIssuingDate": to_iso("14/10/2022"),
}

r = http.post(f"{BASE}/user", json=user_payload, headers=h(sid=sid), timeout_seconds=30)
print(f"  POST /user: {r.status_code}")
print(f"  Body: {r.text[:1000]}")

user_created = r.status_code in (200, 201)

# Se deu 400, ver se eh erro de validacao (significa que aceitou mas dados errados)
if r.status_code == 400:
    print("\n  [!] 400 = endpoint acessivel, possivelmente erro de validacao")
    try:
        err = r.json()
        print(f"  Erro code: {err.get('code', 'N/A')}")
        print(f"  Erro msg: {err.get('message', 'N/A')}")
        if "errors" in err:
            for e in err["errors"][:5]:
                print(f"    - {e}")
    except:
        pass

# === PASSO 7: Se conta criada, criar credenciais ===
if user_created:
    print("\n" + "=" * 60)
    print("[7] CONTA CRIADA! Enviando codigo createCredential...")
    print("=" * 60)

    r = http.post(f"{BASE}/v2/verification-code/send",
        json={"verificationCodeType": "createCredential",
              "document": CPF, "phone": PHONE, "deliveryMethod": "whatsapp"},
        headers=h(sid=sid), timeout_seconds=15)
    print(f"  Envio createCredential: {r.status_code}")

    code2 = input("\n>>> CODIGO CREDENTIAL (WhatsApp): ").strip()

    r = http.post(f"{BASE}/v2/auth/credential",
        json={"document": CPF, "password": PASSWORD, "verificationCode": code2},
        headers=h(sid=sid), timeout_seconds=15)
    print(f"  POST /v2/auth/credential: {r.status_code}")
    print(f"  Body: {r.text[:500]}")

    if r.status_code in (200, 201, 204):
        print("\n  *** CREDENCIAIS CRIADAS! ***")

        # Login
        print("\n[8] Login...")
        r = http.post(f"{BASE}/v2/auth/multifactor-login",
            json={"document": CPF, "password": PASSWORD},
            headers=h(), timeout_seconds=15)
        print(f"  Login: {r.status_code}")
        print(f"  Body: {r.text[:500]}")

        if r.status_code == 200:
            token = r.json().get("token", "")
            if token:
                print(f"\n  *** BEARER TOKEN: {token[:80]}... ***")

                # Testar /v2/persons/*
                print("\n[9] Testar /v2/persons/* com Bearer...")
                for method, ep in [("GET", "/v2/personstatus"),
                                   ("GET", "/v2/persons/documents-upload-lock"),
                                   ("POST", "/v2/persons/send-document")]:
                    body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"} if "send" in ep else None
                    if method == "GET":
                        r = http.get(f"{BASE}{ep}", headers=h(bearer=token), timeout_seconds=15)
                    else:
                        r = http.post(f"{BASE}{ep}", json=body, headers=h(bearer=token), timeout_seconds=15)
                    print(f"  {method} {ep}: {r.status_code} | {r.text[:200] or '(vazio)'}")
else:
    # Mesmo sem criar conta, tentar POST /user com variantes
    print("\n" + "=" * 60)
    print("[7] POST /user falhou - testando variantes...")
    print("=" * 60)

    # 7a: Sem deviceKeyInstallation
    print("\n  7a: Sem deviceKeyInstallation...")
    payload2 = {k: v for k, v in user_payload.items() if k != "deviceKeyInstallation"}
    r = http.post(f"{BASE}/user", json=payload2, headers=h(sid=sid), timeout_seconds=30)
    print(f"    Status: {r.status_code} | {r.text[:300]}")

    # 7b: Sem rg e rgIssuingDate
    print("\n  7b: Sem RG...")
    payload3 = {k: v for k, v in user_payload.items() if k not in ("rg", "rgIssuingDate")}
    r = http.post(f"{BASE}/user", json=payload3, headers=h(sid=sid), timeout_seconds=30)
    print(f"    Status: {r.status_code} | {r.text[:300]}")

    # 7c: Payload minimo
    print("\n  7c: Payload minimo...")
    payload4 = {
        "birthday": to_iso(BIRTHDAY),
        "documentNumber": CPF,
        "email": "rikodocs@gmail.com",
        "name": NAME,
        "password": PASSWORD,
        "phone": re.sub(r"\D", "", PHONE),
        "terms": terms_list,
        "motherName": MOTHER,
        "type": "person",
    }
    r = http.post(f"{BASE}/user", json=payload4, headers=h(sid=sid), timeout_seconds=30)
    print(f"    Status: {r.status_code} | {r.text[:300]}")

print(f"\n  Tempo total: {time.time() - t0:.1f}s")
print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
