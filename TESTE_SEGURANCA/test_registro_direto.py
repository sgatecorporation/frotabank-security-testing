"""
Registro DIRETO - sem send-document (que requer Bearer token)
O POST /user ja inclui os document URLs no payload.
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
DOC_TYPE = "3"
CNH_PATH = r"C:\Users\Acer\Documents\XuanZhi9\Pictures\CNH-e.pdf.pdf"
SELFIE_PATH = r"C:\Users\Acer\Documents\XuanZhi9\Pictures\WhatsApp Image 2026-09-15 at 09.11.07.jpeg"

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


def to_iso_date(val):
    parts = val.strip().split("/")
    if len(parts) == 3:
        dd, mm, yyyy = parts
        return f"{yyyy}-{mm}-{dd}T03:00:00.000Z"
    return val


def safe_json(r):
    try:
        return r.json()
    except:
        return None


print("=" * 60)
print("FROTABANK - REGISTRO DIRETO (sem send-document)")
print("=" * 60)

# 1. Enviar codigo
print("\n[1] Enviar codigo WhatsApp...")
r = http2.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h())
print(f"  Status: {r.status_code} | {r.text[:200]}")

code = input("\n>>> CODIGO WHATSAPP: ").strip()

# 2. Confirmar codigo
print("\n[2] Confirmar codigo...")
sid = None
for phone_try in [PHONE, f"({PHONE[:2]}) {PHONE[2:7]}-{PHONE[7:]}"]:
    r = http2.post(f"{BASE}/phone/confirmation",
        json={"phone": phone_try, "verificationCode": code}, headers=h(), timeout=45)
    print(f"  {phone_try}: {r.status_code} | {r.text[:200]}")
    data = safe_json(r)
    if data and data.get("sessionId"):
        sid = data["sessionId"]
        break
if not sid:
    sys.exit("Sem sessionId!")
print(f"  SESSION: {sid}")

# 3. CPF validation
print("\n[3] CPF validation...")
r = http2.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid))
print(f"  Status: {r.status_code} | {r.text[:200]}")

# 4. Termos
print("\n[4] Carregar termos...")
r = http2.get(f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy", headers=h(sid))
terms = safe_json(r) or []
terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]
print(f"  {len(terms_list)} termos")

# 5. CEP
print("\n[5] CEP...")
r = http2.get(f"{BASE}/zipcode/{CEP}", headers=h(sid))
addr_data = safe_json(r) or {}
print(f"  {addr_data.get('street', '?')}, {addr_data.get('city', '?')}")
address = {
    "zipCode": CEP, "street": addr_data.get("street", "Rua Comendador Araujo"),
    "number": NUMERO, "complement": COMPLEMENTO,
    "neighborhood": addr_data.get("neighborhood", "Centro"),
    "city": addr_data.get("city", "Curitiba"), "state": addr_data.get("state", "PR"),
}

# 6. Upload documentos
print("\n[6] Upload documentos...")
doc_files = [("DIGITAL_DRIVER_LICENSE", CNH_PATH), ("SELFIE", SELFIE_PATH)]
documents = []
for dtype, fpath in doc_files:
    print(f"  {dtype}...", end=" ")
    hh = h(sid)
    del hh["content-type"]
    with open(fpath, "rb") as f:
        img_data = f.read()
    is_pdf = fpath.lower().endswith(".pdf")
    fname = f"{dtype}.pdf" if is_pdf else f"{dtype}.jpg"
    mime = "application/pdf" if is_pdf else "image/jpeg"
    r = http.post(f"{BASE}/user/documents/upload", headers=hh,
        files={"file": (fname, img_data, mime)}, data={"documentType": dtype}, timeout=60)
    if r.status_code == 200:
        doc_url = r.json().get("url", "")
        documents.append({"url": doc_url, "documentType": dtype})
        print(f"OK ({doc_url[:60]}...)")
    else:
        print(f"FALHOU {r.status_code}: {r.text[:100]}")
print(f"  Total: {len(documents)} docs")

# 7. Device key (para incluir no payload)
print("\n[7] Device key...")
device_id = uuid.uuid4().hex[:16]
device_uuid = str(uuid.uuid4())
r = http2.post(f"{SAFEGUARD_API_URL}device_key",
    json={"deviceId": device_id, "isRoot": False, "userId": CPF,
          "uuid": device_uuid, "userMetadata": None, "operatingSystem": "android"},
    headers={"SG-API-KEY": SAFEGUARD_API_KEY, "Content-Type": "application/json"})
print(f"  Create: {r.status_code}")
device_key = None
if r.status_code in (200, 201):
    device_key = r.json().get("privateKey")
    print(f"  privateKey len: {len(device_key) if device_key else 0}")

# 8. POST /user - DIRETO (sem send-document antes!)
print("\n" + "=" * 60)
print("[8] POST /user — CRIANDO CONTA")
print("=" * 60)

birthday_iso = to_iso_date(BIRTHDAY)
phone_raw = re.sub(r"\D", "", PHONE)
rg_clean = re.sub(r"\D", "", RG)

payload = {
    "addresses": [address],
    "birthday": birthday_iso,
    "documentNumber": CPF,
    "documents": [{"url": d["url"], "documentType": d["documentType"]} for d in documents],
    "email": EMAIL,
    "name": NOME,
    "newsletterAccept": False,
    "password": PASSWORD,
    "phone": phone_raw,
    "terms": terms_list,
    "isPEP": False,
    "monthlyIncome": MONTHLY_INCOME,
    "motherName": MOTHER,
    "professionId": PROF_ID,
    "type": "person",
    "partners": [],
    "deviceKeyInstallation": {"uuid": device_uuid, "deviceId": device_id},
    "rg": rg_clean,
    "rgIssuingDate": to_iso_date(RG_DATE) if RG_DATE else None,
}

print(f"  CPF: {CPF} | Nome: {NOME} | Docs: {[d['documentType'] for d in documents]}")
print(f"  Payload keys: {list(payload.keys())}")

# Teste A: POST /user SEM device key signature (so headers padrao)
print("\n[8A] POST /user SEM device key signature...")
headers_a = h(sid)
r = http2.post(f"{BASE}/user", json=payload, headers=headers_a, timeout=60)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:500]}")
try:
    resp = r.json()
    print(f"  Keys: {list(resp.keys()) if isinstance(resp, dict) else 'N/A'}")
except:
    pass

if r.status_code in (200, 201):
    print("\n  CONTA CRIADA!")
    # Tentar login
    print("\n[9] Login...")
    r2 = http2.post(f"{BASE}/v2/auth/multifactor-login",
        json={"document": CPF, "password": PASSWORD}, headers=h(sid))
    print(f"  Status: {r2.status_code} | {r2.text[:300]}")
elif r.status_code == 401:
    # Se 401, tentar com device key signature
    print("\n[8B] POST /user COM device key signature (sem headers no canonical)...")
    if device_key:
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

        url_user = f"{BASE}/user"
        parsed = urlparse(url_user)
        domain = parsed.hostname.lower()
        path = parsed.path or "/"
        parts = ["POST", domain, path]
        body_pairs = _traverse(payload)
        body_pairs.sort()
        parts.append("\n".join(body_pairs))
        canonical = "\n".join(parts)
        print(f"  Canonical ({len(canonical)} chars), primeiras 5 linhas:")
        for i, line in enumerate(canonical.split("\n")[:5]):
            print(f"    [{i}] {line[:100]}")
        sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
        hmac_hex = hmac_module.new(device_key.encode("utf-8"), sha1_hex.encode("utf-8"), hashlib.sha256).hexdigest()
        sig = base64.b64encode(f"{SAFEGUARD_API_KEY}:{device_id}:{device_uuid}:{sha1_hex}:{hmac_hex}{sha1_hex}".encode()).decode()

        headers_b = h(sid)
        headers_b["x-device-key-signature"] = sig
        headers_b["x-device-key-user-id"] = CPF
        r = http2.post(url_user, json=payload, headers=headers_b, timeout=60)
        print(f"  Status: {r.status_code}")
        print(f"  Body: {r.text[:500]}")
    else:
        print("  Sem device key, nao pode assinar")
else:
    print(f"\n  Erro {r.status_code} - resposta completa:")
    print(f"  {r.text[:1000]}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
