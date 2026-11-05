"""
Frotabank Registration Flow - FLUXO CORRETO (ordem exata do app)
Ordem: CPF whitelist → phone → CPF validation → dados → docs → selfie → POST /user
"""
import requests, uuid, json, re, hashlib, hmac as hmac_module, base64, time, jwt, random, sys
from urllib.parse import urlparse
from curl_cffi import requests as curl_requests

BASE = "https://api.c03.frotabank.com.br"
SESSION = str(uuid.uuid4())
CORR = uuid.uuid4().hex

SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

# ===== DADOS PRE-PREENCHIDOS =====
CPF_FIXO = "41265599904"
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
DOC_TYPE = "3"    # 1=RG, 2=CNH, 3=CNH digital
CNH_PATH = r"C:\Users\Acer\Documents\XuanZhi9\Pictures\CNH-e.pdf.pdf"
SELFIE_PATH = r"C:\Users\Acer\Documents\XuanZhi9\Pictures\WhatsApp Image 2026-09-15 at 09.11.07.jpeg"
DELIVERY_METHOD = "whatsapp"  # "phone"=SMS, "whatsapp"=WhatsApp, "phone-call"=ligacao

http = requests.Session()
http.timeout = 15
http2 = curl_requests.Session(impersonate="chrome120", timeout=15)


def gerar_cpf():
    digits = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        val = sum((len(digits) + 1 - i) * v for i, v in enumerate(digits))
        rest = val % 11
        digits.append(0 if rest < 2 else 11 - rest)
    return "".join(str(d) for d in digits)


def fmt_cpf(c):
    d = re.sub(r"\D", "", c)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return d


def fmt_phone(p):
    d = re.sub(r"\D", "", p)
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    return d


def to_iso_date(val):
    val = val.strip()
    parts = val.split("/")
    if len(parts) == 3:
        dd, mm, yyyy = parts
        return f"{yyyy}-{mm}-{dd}T03:00:00.000Z"
    d = re.sub(r"\D", "", val)
    if len(d) == 8:
        return f"{d[4:8]}-{d[2:4]}-{d[0:2]}T03:00:00.000Z"
    return val


def safe_json(r):
    try:
        return r.json()
    except Exception:
        return None


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


class SafeGuard:
    def __init__(self):
        self.api_key = SAFEGUARD_API_KEY
        self.api_url = SAFEGUARD_API_URL
        self.device_key = None
        self.device_id = None
        self.device_uuid = None
        self.user_id = None

    def _sg_headers(self):
        return {"SG-API-KEY": self.api_key, "Content-Type": "application/json"}

    def create_device_key(self, cpf):
        self.device_id = uuid.uuid4().hex[:16]
        self.device_uuid = str(uuid.uuid4())
        self.user_id = cpf
        resp = http.post(
            f"{self.api_url}device_key",
            json={"deviceId": self.device_id, "isRoot": False, "userId": cpf,
                  "uuid": self.device_uuid, "userMetadata": None, "operatingSystem": "android"},
            headers=self._sg_headers(),
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            self.device_key = data.get("privateKey")
            if self.device_key:
                print(f"  Device key criado (len={len(self.device_key)})")
                self.validate_device_key()
                return True
        print(f"  Device key FALHOU: {resp.status_code} {resp.text[:200]}")
        return False

    def validate_device_key(self):
        resp = http.post(
            f"{self.api_url}device_key/validate",
            json={"uuid": self.device_uuid, "deviceId": self.device_id},
            headers=self._sg_headers(),
        )
        print(f"  Device key validate: {resp.status_code} {resp.text[:200]}")

    def check_device_key_status(self):
        resp = http.get(
            f"{self.api_url}device_key/status",
            params={"uuid": self.device_uuid, "deviceId": self.device_id},
            headers=self._sg_headers(),
        )
        print(f"  Device key status: {resp.status_code} {resp.text[:200]}")
        return resp

    def _traverse(self, obj, parent_keys=None, result=None):
        if parent_keys is None: parent_keys = []
        if result is None: result = []
        items = obj.items() if isinstance(obj, dict) else enumerate(obj) if isinstance(obj, list) else []
        for key, value in items:
            key_path = parent_keys + [str(key)]
            if value is not None and isinstance(value, (dict, list)) and len(value) > 0:
                self._traverse(value, key_path, result)
            else:
                result.append(".".join(key_path) + "=" + self._js_str(value))
        return result

    @staticmethod
    def _js_str(value):
        if value is None: return "null"
        if isinstance(value, bool): return "true" if value else "false"
        return str(value)

    def generate_signature(self, method, url, headers, body=None):
        parsed = urlparse(url)
        domain = parsed.hostname.lower()
        path = parsed.path or "/"
        skip = {"sg-signature", "x-device-key-headers", "x-device-key-signature", "x-device-key-user-id"}
        clean_headers = {k: v for k, v in headers.items() if k.lower() not in skip}
        parts = [method.upper(), domain, path]
        if body and len(body) > 0:
            pairs = self._traverse(body)
            pairs.sort()
            parts.append("\n".join(pairs))
        if clean_headers and len(clean_headers) > 0:
            pairs = self._traverse(clean_headers)
            lowered = []
            for pair in pairs:
                eq_idx = pair.index("=")
                lowered.append(pair[:eq_idx].lower() + pair[eq_idx:])
            lowered.sort()
            parts.append("\n".join(lowered))
        canonical = "\n".join(parts)
        sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
        hmac_hex = hmac_module.new(
            self.device_key.encode("utf-8"), sha1_hex.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        sig_plain = f"{self.api_key}:{self.device_id}:{self.device_uuid}:{sha1_hex}:{hmac_hex}{sha1_hex}"
        return base64.b64encode(sig_plain.encode("utf-8")).decode("utf-8")


safeguard = SafeGuard()
phone_raw = re.sub(r"\D", "", PHONE)
phone_fmt = fmt_phone(phone_raw)
birthday = to_iso_date(BIRTHDAY)

print("=" * 60)
print("FROTABANK - FLUXO DE REGISTRO (AUTO)")
print("=" * 60)

# ===== PASSO 1: CPF =====
cpf_raw = CPF_FIXO
cpf_fmt = fmt_cpf(cpf_raw)
print(f"\n[1] CPF: {cpf_raw} ({cpf_fmt})")

# ===== PASSO 1.1: Whitelist =====
print(f"\n[1.1] GET /v2/whitelist/validate-document/{cpf_raw}...")
r = http2.get(f"{BASE}/v2/whitelist/validate-document/{cpf_raw}", headers=h(), timeout=15)
print(f"  Status: {r.status_code} | Body: '{r.text[:200]}'")
wl_data = safe_json(r)
if r.status_code == 200 and wl_data and isinstance(wl_data, dict) and wl_data.get("isRegistered"):
    print("  CPF JA REGISTRADO!"); sys.exit(1)

# ===== PASSO 1.2: Onboarding status =====
try:
    r = http2.post(f"{BASE}/v2/onboarding/status", json={"document": cpf_raw}, headers=h(), timeout=15)
    print(f"[1.2] Onboarding: {r.status_code} | {r.text[:200]}")
except Exception as e:
    print(f"[1.2] Onboarding: TIMEOUT/ERRO ({e}) - continuando...")

# ===== PASSO 2: Telefone =====
print(f"\n[2] Phone: {phone_fmt}")
sent_ok = False
for method in [DELIVERY_METHOD, "whatsapp"]:
    for phone_try in [phone_fmt, phone_raw]:
        if sent_ok:
            break
        send_body = {"phone": phone_try, "verificationCodeType": "onboarding",
                     "deliveryMethod": method, "document": cpf_raw}
        r = http2.post(f"{BASE}/v2/verification-code/send", json=send_body, headers=h())
        fmt_label = "fmt" if "(" in phone_try else "raw"
        print(f"  Send ({method}/{fmt_label}): {r.status_code} | {r.text[:120]}")
        if r.status_code == 200:
            sent_ok = True
            print(f"  >>> Codigo enviado via {method.upper()}!")
    if sent_ok:
        break
if not sent_ok:
    print("  ERRO: Nenhum metodo de envio funcionou!")

# ===== PASSO 3: Codigo (UNICO INPUT MANUAL) =====
code = input("\n>>> CODIGO SMS/WHATSAPP: ").strip()
data = None
for phone_try in [phone_fmt, phone_raw]:
    if data and data.get("sessionId"):
        break
    fmt_label = "fmt" if "(" in phone_try else "raw"
    print(f"  Confirmando ({fmt_label})...", end=" ", flush=True)
    try:
        r = http2.post(f"{BASE}/phone/confirmation",
            json={"phone": phone_try, "verificationCode": code}, headers=h(), timeout=45)
        print(f"{r.status_code} | {r.text[:200]}")
        data = safe_json(r)
    except Exception as e:
        print(f"ERRO: {e}")
sid = data.get("sessionId") if data else None
if not sid:
    sys.exit("Sem sessionId!")
print(f"  SESSION: {sid}")

# ===== PASSO 4-5: Email + CPF validation =====
print(f"\n[4] Email: {EMAIL}")
r = http2.post(f"{BASE}/user/cpf-validation", json={"cpf": cpf_raw}, headers=h(sid), timeout=30)
print(f"[5] CPF validation (raw): {r.status_code} | {r.text[:100]}")
if r.status_code != 200:
    r = http2.post(f"{BASE}/user/cpf-validation", json={"cpf": cpf_fmt}, headers=h(sid), timeout=30)
    print(f"    Retry (fmt): {r.status_code} | {r.text[:100]}")

# ===== PASSO 6-10: Dados pessoais (tudo auto) =====
print(f"\n[6] RG: {'(nao enviado)' if not RG else RG}")
print(f"[7] Nome: {NOME}")
print(f"[8] Nascimento: {BIRTHDAY} -> {birthday}")
print(f"[9] Mae: {MOTHER}")
print(f"[10] PEP: Nao")

# ===== PASSO 11: CEP =====
r = http2.get(f"{BASE}/zipcode/{CEP}", headers=h(sid), timeout=15)
addr_data = safe_json(r) or {}
print(f"[11] CEP {CEP}: {r.status_code} | {addr_data.get('street', '?')}, {addr_data.get('city', '?')}")
address = {
    "zipCode": CEP,
    "street": addr_data.get("street", "Rua Comendador Araujo"),
    "number": NUMERO,
    "complement": COMPLEMENTO,
    "neighborhood": addr_data.get("neighborhood", "Centro"),
    "city": addr_data.get("city", "Curitiba"),
    "state": addr_data.get("state", "PR"),
}

# ===== PASSO 12: Profissao =====
r = http2.get(f"{BASE}/professions", headers=h(sid), timeout=15)
print(f"[12] Profissoes: {r.status_code} | professionId={PROF_ID}")

# ===== PASSO 14: Termos =====
r = http2.get(f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy", headers=h(sid), timeout=15)
terms = safe_json(r) or []
terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]
print(f"[14] Termos: {len(terms_list)} termos carregados")

# ===== PASSO 15: Upload documentos (auto com paths fixos) =====
print(f"\n[15] Upload documentos (tipo={DOC_TYPE})...")

if DOC_TYPE == "2":
    doc_files = [("DRIVER_LICENSE_FRONT", CNH_PATH), ("DRIVER_LICENSE_VERSE", CNH_PATH), ("SELFIE", SELFIE_PATH)]
elif DOC_TYPE == "3":
    doc_files = [("DIGITAL_DRIVER_LICENSE", CNH_PATH), ("SELFIE", SELFIE_PATH)]
else:
    doc_files = [("IDENTITY_CARD_FRONT", CNH_PATH), ("IDENTITY_CARD_VERSE", CNH_PATH), ("SELFIE", SELFIE_PATH)]

documents = []
for dtype, fpath in doc_files:
    print(f"  Upload {dtype}...", end=" ")
    hh = h(sid); del hh["content-type"]
    with open(fpath, "rb") as f:
        img_data = f.read()
    is_pdf = fpath.lower().endswith(".pdf")
    fname = f"{dtype}.pdf" if is_pdf else f"{dtype}.jpg"
    mime = "application/pdf" if is_pdf else "image/jpeg"
    r = http.post(f"{BASE}/user/documents/upload", headers=hh,
        files={"file": (fname, img_data, mime)}, data={"documentType": dtype}, timeout=60)
    if r.status_code == 200:
        resp_data = r.json()
        doc_url = resp_data.get("url", "")
        documents.append({"url": doc_url, "documentType": dtype})
        print(f"OK")
    else:
        print(f"FALHOU {r.status_code}: {r.text[:100]}")

print(f"  Total: {len(documents)} docs")

# ===== PASSO 15.5: Device key (ANTES do send-document!) =====
print(f"\n[15.5] Device key...")
safeguard.create_device_key(cpf_raw)
safeguard.check_device_key_status()

# ===== PASSO 15.6: Send documents ao banco (PASSO CRUCIAL!) =====
def to_camel(s):
    parts = s.lower().split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])

print(f"\n[15.6] POST /v2/persons/send-document (cada doc)...")
for doc in documents:
    camel_type = to_camel(doc["documentType"])
    send_body = {"link": doc["url"], "type": camel_type}
    send_url = f"{BASE}/v2/persons/send-document"
    send_headers = h(sid)
    header_keys = ";".join(send_headers.keys())
    sig_sd = safeguard.generate_signature("POST", send_url, send_headers, body=send_body)
    send_headers["x-device-key-headers"] = header_keys
    send_headers["x-device-key-signature"] = sig_sd
    send_headers["x-device-key-user-id"] = safeguard.user_id
    r_send = http2.post(send_url, json=send_body, headers=send_headers, timeout=30)
    print(f"  {doc['documentType']} -> {camel_type}: {r_send.status_code} | {r_send.text[:300]}")

# ===== PASSO 16: Validate selfie =====

selfie_url = front_url = back_url = ""
for doc in documents:
    dt = doc["documentType"]
    if dt == "SELFIE": selfie_url = doc["url"]
    elif dt in ("IDENTITY_CARD_FRONT", "DRIVER_LICENSE_FRONT", "DIGITAL_DRIVER_LICENSE"): front_url = doc["url"]
    elif dt in ("IDENTITY_CARD_VERSE", "DRIVER_LICENSE_VERSE"): back_url = doc["url"]
if not back_url: back_url = front_url

validate_body = {
    "uuid": safeguard.device_uuid, "deviceId": safeguard.device_id,
    "userDocument": cpf_raw, "userFullName": NOME, "userBirthdate": birthday,
    "selfieUrl": selfie_url, "frontDocumentPhotoUrl": front_url,
    "backDocumentPhotoUrl": back_url, "onlyValidation": True,
}
validate_url = f"{BASE}/v2/device-key/validate-selfie-and-document"
validate_headers = h(sid)
sig = safeguard.generate_signature("POST", validate_url, {}, body=validate_body)
validate_headers["x-device-key-signature"] = sig
validate_headers["x-device-key-user-id"] = safeguard.user_id
r = http2.post(validate_url, json=validate_body, headers=validate_headers, timeout=30)
print(f"  Validate selfie: {r.status_code}")

# ===== PASSO 17: POST /user =====
print("\n" + "=" * 60)
print("[17] POST /user — CRIANDO CONTA")
print("=" * 60)

payload = {
    "addresses": [address],
    "birthday": birthday,
    "documentNumber": cpf_raw,
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
    "deviceKeyInstallation": {
        "uuid": safeguard.device_uuid or str(uuid.uuid4()),
        "deviceId": safeguard.device_id or uuid.uuid4().hex[:16],
    },
}

if RG:
    rg_clean = re.sub(r"\D", "", RG)
    payload["rg"] = rg_clean
    payload["rgIssuingDate"] = to_iso_date(RG_DATE) if RG_DATE else None
    print(f"  RG: {rg_clean} | rgIssuingDate: {payload.get('rgIssuingDate')}")

print(f"  CPF: {cpf_raw} | Phone: {phone_raw} | Birthday: {birthday}")
print(f"  Docs: {[d['documentType'] for d in documents]}")
print(f"  Keys: {list(payload.keys())}")
print(f"\n  === PAYLOAD JSON (debug) ===")
payload_json = json.dumps(payload, ensure_ascii=False)
print(f"  {payload_json[:2000]}")
print(f"  === FIM PAYLOAD ({len(payload_json)} bytes) ===\n")

url17 = f"{BASE}/user"
headers17 = h(sid)
sig17 = safeguard.generate_signature("POST", url17, {}, body=payload)
headers17["x-device-key-signature"] = sig17
headers17["x-device-key-user-id"] = safeguard.user_id

print("  Enviando...")
r = http2.post(url17, json=payload, headers=headers17)
print(f"\n  >>> STATUS: {r.status_code}")
print(f"  >>> BODY: {r.text[:1000]}")

if r.status_code in (200, 201):
    print("\n  USUARIO CRIADO COM SUCESSO!")
    try:
        resp = r.json()
        print(f"  Keys: {list(resp.keys())}")
        if resp.get("documentsCreationReport"):
            print(f"  documentsCreationReport: {json.dumps(resp['documentsCreationReport'], indent=2)}")
    except: pass

    print("\n[18] Login...")
    r2 = http2.post(f"{BASE}/v2/auth/multifactor-login",
        json={"document": cpf_raw, "password": PASSWORD}, headers=h(sid))
    print(f"  Login: {r2.status_code} | {r2.text[:300]}")
    if r2.status_code == 200:
        login_data = r2.json()
        token = login_data.get("token") or login_data.get("accessToken")
        if token:
            print(f"  TOKEN: {token[:60]}...")
else:
    print(f"\n  ERRO: {r.status_code}")
    try:
        print(f"  {json.dumps(r.json(), indent=2)}")
    except: pass

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
