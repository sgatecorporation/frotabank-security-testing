"""
Fix validate-selfie-and-document: ver erro completo e testar variações do payload.
O endpoint retornou 400 (não 401!) - precisa corrigir formato.
"""
import requests, uuid, json, re, time, jwt, sys
from curl_cffi import requests as curl_requests

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

CPF = "41265599904"
PHONE = "11984636182"
RG = "39824248"
NOME = "JANDIRA STUCCHI"
BIRTHDAY = "15/06/1962"

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
print("FIX VALIDATE-SELFIE-AND-DOCUMENT")
print("=" * 60)

# 1. Obter sessão
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

# 2. CPF validation
print("\n[3] CPF validation...")
r = http2.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid))
print(f"  Status: {r.status_code}")

# 3. Upload documentos
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
        print(f"  {dtype}: FALHOU {r.status_code}")
        sys.exit(1)

selfie_url = next((d["url"] for d in doc_uploads if d["documentType"] == "SELFIE"), "")
front_doc_url = next((d["url"] for d in doc_uploads if d["documentType"] != "SELFIE"), "")

# 4. Create device key
print("\n[5] Create device key...")
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

# 5. TESTAR variações do payload
print("\n" + "=" * 60)
print("TESTES VALIDATE-SELFIE-AND-DOCUMENT")
print("=" * 60)

url = f"{BASE}/v2/device-key/validate-selfie-and-document"

# Teste A: payload original (como antes, com backDocumentPhotoUrl: null)
print("\n[A] Payload original (backDocumentPhotoUrl=null)...")
payload_a = {
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
r = http2.post(url, json=payload_a, headers=h(sid), timeout=60)
print(f"  Status: {r.status_code}")
print(f"  FULL ERROR:")
try:
    err = r.json()
    print(json.dumps(err, indent=2, ensure_ascii=False)[:5000])
except:
    print(f"  {r.text[:3000]}")

# Teste B: SEM backDocumentPhotoUrl (omitir campo)
print("\n\n[B] Sem backDocumentPhotoUrl...")
payload_b = {
    "uuid": device_uuid,
    "deviceId": device_id,
    "userDocument": clean(RG),
    "userFullName": NOME,
    "userBirthdate": to_iso(BIRTHDAY),
    "selfieUrl": selfie_url,
    "frontDocumentPhotoUrl": front_doc_url,
    "onlyValidation": True,
}
r = http2.post(url, json=payload_b, headers=h(sid), timeout=60)
print(f"  Status: {r.status_code}")
try:
    err = r.json()
    print(json.dumps(err, indent=2, ensure_ascii=False)[:5000])
except:
    print(f"  {r.text[:3000]}")

# Teste C: Com document=CPF adicionado
print("\n\n[C] Com document=CPF...")
payload_c = {
    "uuid": device_uuid,
    "deviceId": device_id,
    "userDocument": clean(RG),
    "userFullName": NOME,
    "userBirthdate": to_iso(BIRTHDAY),
    "selfieUrl": selfie_url,
    "frontDocumentPhotoUrl": front_doc_url,
    "onlyValidation": True,
    "document": CPF,
}
r = http2.post(url, json=payload_c, headers=h(sid), timeout=60)
print(f"  Status: {r.status_code}")
try:
    err = r.json()
    print(json.dumps(err, indent=2, ensure_ascii=False)[:5000])
except:
    print(f"  {r.text[:3000]}")

# Teste D: userDocument=CPF em vez de RG
print("\n\n[D] userDocument=CPF...")
payload_d = {
    "uuid": device_uuid,
    "deviceId": device_id,
    "userDocument": CPF,
    "userFullName": NOME,
    "userBirthdate": to_iso(BIRTHDAY),
    "selfieUrl": selfie_url,
    "frontDocumentPhotoUrl": front_doc_url,
    "onlyValidation": True,
}
r = http2.post(url, json=payload_d, headers=h(sid), timeout=60)
print(f"  Status: {r.status_code}")
try:
    err = r.json()
    print(json.dumps(err, indent=2, ensure_ascii=False)[:5000])
except:
    print(f"  {r.text[:3000]}")

# Teste E: birthdate em formato diferente (DD/MM/YYYY string)
print("\n\n[E] userBirthdate como string DD/MM/YYYY...")
payload_e = {
    "uuid": device_uuid,
    "deviceId": device_id,
    "userDocument": clean(RG),
    "userFullName": NOME,
    "userBirthdate": BIRTHDAY,
    "selfieUrl": selfie_url,
    "frontDocumentPhotoUrl": front_doc_url,
    "onlyValidation": True,
}
r = http2.post(url, json=payload_e, headers=h(sid), timeout=60)
print(f"  Status: {r.status_code}")
try:
    err = r.json()
    print(json.dumps(err, indent=2, ensure_ascii=False)[:5000])
except:
    print(f"  {r.text[:3000]}")

# Teste F: Payload minimalista - apenas campos obrigatórios básicos
print("\n\n[F] Payload minimal...")
payload_f = {
    "uuid": device_uuid,
    "deviceId": device_id,
    "selfieUrl": selfie_url,
    "frontDocumentPhotoUrl": front_doc_url,
    "onlyValidation": True,
}
r = http2.post(url, json=payload_f, headers=h(sid), timeout=60)
print(f"  Status: {r.status_code}")
try:
    err = r.json()
    print(json.dumps(err, indent=2, ensure_ascii=False)[:5000])
except:
    print(f"  {r.text[:3000]}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
