"""
Fluxo COMPLETO CORRIGIDO:
- backDocumentPhotoUrl = frontDocumentPhotoUrl (CNH digital = frente e verso iguais)
- Segue ordem exata: phone → CPF → upload → device key → validate → send-document → POST /user
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


print("=" * 60)
print("FROTABANK - FLUXO FINAL CORRIGIDO")
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
    print(f"  FALHOU: {r.status_code} {r.text[:500]}")
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
    hh = h(sid)
    del hh["content-type"]
    with open(fpath, "rb") as f:
        fdata = f.read()
    ext = "pdf" if "pdf" in mime else "jpg"
    r = http.post(f"{BASE}/user/documents/upload", headers=hh,
        files={"file": (f"{dtype}.{ext}", fdata, mime)},
        data={"documentType": dtype}, timeout=60)
    if r.status_code == 200:
        url = r.json().get("url", "")
        doc_uploads.append({"url": url, "documentType": dtype})
        print(f"  {dtype}: OK")
    else:
        print(f"  {dtype}: FALHOU {r.status_code}: {r.text[:200]}")
        sys.exit(1)

selfie_url = next((d["url"] for d in doc_uploads if d["documentType"] == "SELFIE"), "")
front_doc_url = next((d["url"] for d in doc_uploads if d["documentType"] != "SELFIE"), "")
print(f"  Selfie: {selfie_url[:80]}...")
print(f"  Front:  {front_doc_url[:80]}...")

# === PASSO 4: Create device key ===
print("\n[5] Create device key (SafeGuard)...")
device_id = uuid.uuid4().hex[:16]
device_uuid = str(uuid.uuid4())
r = http2.post(f"{SAFEGUARD_API_URL}device_key",
    json={"deviceId": device_id, "isRoot": False, "userId": CPF,
          "uuid": device_uuid, "userMetadata": None, "operatingSystem": "android"},
    headers=sg_h())
if r.status_code not in (200, 201):
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
device_key = r.json().get("privateKey")
print(f"  OK - uuid: {device_uuid}, deviceId: {device_id}")

# === PASSO 5: validate-selfie-and-document (CORRIGIDO: backDocumentPhotoUrl preenchido) ===
print("\n" + "=" * 60)
print("[6] POST /v2/device-key/validate-selfie-and-document")
print("    FIX: backDocumentPhotoUrl = frontDocumentPhotoUrl")
print("=" * 60)

validate_payload = {
    "uuid": device_uuid,
    "deviceId": device_id,
    "userDocument": clean(RG),
    "userFullName": NOME,
    "userBirthdate": to_iso(BIRTHDAY),
    "selfieUrl": selfie_url,
    "frontDocumentPhotoUrl": front_doc_url,
    "backDocumentPhotoUrl": front_doc_url,
    "onlyValidation": True,
}

r = http2.post(f"{BASE}/v2/device-key/validate-selfie-and-document",
    json=validate_payload, headers=h(sid), timeout=90)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:2000]}")

if r.status_code not in (200, 201):
    print("\n  Tentando com selfie como back...")
    validate_payload["backDocumentPhotoUrl"] = selfie_url
    r = http2.post(f"{BASE}/v2/device-key/validate-selfie-and-document",
        json=validate_payload, headers=h(sid), timeout=90)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:2000]}")

if r.status_code not in (200, 201):
    print(f"\n  VALIDATE FALHOU. Tentando send-document mesmo assim...")

# === PASSO 6: send-document ===
print("\n" + "=" * 60)
print("[7] POST /v2/persons/send-document")
print("=" * 60)

doc_type_map = {
    "DIGITAL_DRIVER_LICENSE": "digitalDriverLicense",
    "SELFIE": "selfie",
}
for doc in doc_uploads:
    doc_type = doc_type_map.get(doc["documentType"], doc["documentType"])
    send_body = {"link": doc["url"], "type": doc_type}
    print(f"\n  Enviando {doc_type}...")
    r = http2.post(f"{BASE}/v2/persons/send-document", json=send_body, headers=h(sid), timeout=30)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:500]}")

# === PASSO 7: POST /user ===
print("\n" + "=" * 60)
print("[8] POST /user - CRIAR CONTA")
print("=" * 60)

print("  Buscando termos e CEP...")
r = http2.get(f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy", headers=h(sid))
terms = r.json() if r.status_code == 200 else []
terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]
print(f"  Terms: {len(terms_list)} itens")

r = http2.get(f"{BASE}/zipcode/{CEP}", headers=h(sid))
addr_data = r.json() if r.status_code == 200 else {}
print(f"  CEP: {addr_data.get('street', '?')}, {addr_data.get('city', '?')}")

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
print(f"\n  Status: {r.status_code}")
print(f"  Body: {r.text[:1000]}")

if r.status_code in (200, 201):
    print("\n  >>> CONTA CRIADA COM SUCESSO! <<<")
    user_data = r.json()
    print(f"  Dados: {json.dumps(user_data, indent=2, ensure_ascii=False)[:2000]}")

    # === PASSO 8: Login ===
    print("\n" + "=" * 60)
    print("[9] LOGIN - POST /v2/auth/multifactor-login")
    print("=" * 60)
    login_payload = {"document": CPF, "password": PASSWORD}
    r = http2.post(f"{BASE}/v2/auth/multifactor-login", json=login_payload, headers=h(sid), timeout=30)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:1000]}")

    if r.status_code == 200:
        login_data = r.json()
        token = login_data.get("token", "")
        if token:
            print(f"\n  >>> TOKEN OBTIDO! <<<")
            print(f"  Token: {token[:60]}...")

            # Testar endpoints protegidos
            print("\n[10] Testar endpoints com Bearer token...")
            auth_h = h(sid)
            auth_h["Authorization"] = f"Bearer {token}"

            for ep in ["/v2/personstatus", "/v2/persons/send-document"]:
                if "personstatus" in ep:
                    r = http2.post(f"{BASE}{ep}", json={"document": CPF}, headers=auth_h, timeout=15)
                else:
                    r = http2.post(f"{BASE}{ep}", json={"link": "test", "type": "selfie"}, headers=auth_h, timeout=15)
                print(f"    POST {ep}: {r.status_code} | {r.text[:200]}")
else:
    print(f"\n  POST /user falhou. Verificar erros acima.")

print("\n" + "=" * 60)
print("FIM DO FLUXO")
print("=" * 60)
