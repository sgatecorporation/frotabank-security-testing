"""
Testar criacao de conta e login para obter Bearer token REAL.
1. POST /user - ver erro EXATO
2. Login com segundo CPF (03652399846)
3. POST /v2/auth/credential
4. Se conseguir token, testar /v2/persons/*
"""
import tls_client
import uuid, json, time, jwt, re, sys

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

CPF1 = "41265599904"
CPF2 = "03652399846"
PHONE = "11984636182"
PASSWORD = "Senh@2024!"
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
print("TESTE CRIACAO DE CONTA + BEARER TOKEN")
print("=" * 60)

# TESTE 1: Login com ambos CPFs (sem sessao)
print("\n[1] Login direto com CPF1 e CPF2...")
for cpf, label in [(CPF1, "CPF1"), (CPF2, "CPF2")]:
    for pwd in [PASSWORD, "123456", "Frota@2024!", "Mudar@123"]:
        r = http.post(f"{BASE}/v2/auth/multifactor-login",
            json={"document": cpf, "password": pwd},
            headers=h(), timeout_seconds=10)
        if r.status_code != 401:
            print(f"  {label} pwd={pwd}: {r.status_code} {r.text[:200]}")
            break
    else:
        print(f"  {label}: TODAS senhas 401 invalid_credentials")

# TESTE 2: Obter sessao
print("\n[2] Obter sessao...")
r = http.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF1},
    headers=h())
print(f"  Envio codigo: {r.status_code}")

code = input("\n>>> CODIGO: ").strip()

r = http.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(), timeout_seconds=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  Session: {sid}")

# TESTE 3: POST /user - ver erro EXATO
print("\n[3] POST /user - testar erro...")

# Buscar termos e CEP
r = http.get(f"{BASE}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy", headers=h(sid=sid))
terms = r.json() if r.status_code == 200 else []
terms_list = [{"type": t["type"], "token": t["token"]} for t in terms]

r = http.get(f"{BASE}/zipcode/80420000", headers=h(sid=sid))
addr = r.json() if r.status_code == 200 else {}

device_uuid = str(uuid.uuid4())
device_id = uuid.uuid4().hex[:16]

# Criar device key
r = http.post(f"{SAFEGUARD_API_URL}device_key",
    json={"deviceId": device_id, "isRoot": False, "userId": CPF1,
          "uuid": device_uuid, "userMetadata": None, "operatingSystem": "android"},
    headers={"SG-API-KEY": SAFEGUARD_API_KEY, "Content-Type": "application/json"})
dk = r.json().get("privateKey", "") if r.status_code in (200, 201) else ""
print(f"  Device key: {'OK' if dk else 'FAIL'}")

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
    "birthday": to_iso("15/06/1962"),
    "documentNumber": CPF1,
    "email": "rikodocs@gmail.com",
    "name": "JANDIRA STUCCHI",
    "newsletterAccept": False,
    "password": PASSWORD,
    "phone": re.sub(r"\D", "", PHONE),
    "terms": terms_list,
    "isPEP": False,
    "monthlyIncome": 5000,
    "motherName": "ANA AUGUSTA STUCCHI",
    "professionId": 1,
    "type": "person",
    "partners": [],
    "deviceKeyInstallation": {"uuid": device_uuid, "deviceId": device_id},
    "rg": "39824248",
    "rgIssuingDate": to_iso("14/10/2022"),
}

r = http.post(f"{BASE}/user", json=user_payload, headers=h(sid=sid), timeout_seconds=30)
print(f"  POST /user status: {r.status_code}")
print(f"  POST /user body: {r.text[:1000]}")

# TESTE 4: POST /v2/auth/credential (endpoint de criacao de senha)
print("\n[4] POST /v2/auth/credential...")
cred_payloads = [
    {"document": CPF1, "password": PASSWORD},
    {"document": CPF1, "password": PASSWORD, "sessionId": sid},
    {"cpf": CPF1, "password": PASSWORD},
]
for i, payload in enumerate(cred_payloads):
    r = http.post(f"{BASE}/v2/auth/credential", json=payload, headers=h(sid=sid), timeout_seconds=15)
    print(f"  Variante {i+1}: {r.status_code} | {r.text[:300]}")

# TESTE 5: Outros endpoints de auth
print("\n[5] Outros endpoints de auth...")
auth_eps = [
    ("POST", "/v2/auth/credential", {"document": CPF1, "password": PASSWORD}),
    ("PUT", "/v2/auth/credential", {"document": CPF1, "password": PASSWORD}),
    ("POST", "/v2/auth/create-credential", {"document": CPF1, "password": PASSWORD}),
    ("POST", "/v2/credentials", {"document": CPF1, "password": PASSWORD}),
    ("POST", "/v2/auth/register", {"document": CPF1, "password": PASSWORD}),
]
for method, ep, payload in auth_eps:
    try:
        if method == "POST":
            r = http.post(f"{BASE}{ep}", json=payload, headers=h(sid=sid), timeout_seconds=10)
        elif method == "PUT":
            r = http.put(f"{BASE}{ep}", json=payload, headers=h(sid=sid), timeout_seconds=10)
        print(f"  {method} {ep}: {r.status_code} | {r.text[:200]}")
    except Exception as e:
        print(f"  {method} {ep}: ERRO {e}")

# Se POST /user deu 200/201, tentar login
if r.status_code in (200, 201):
    print("\n[6] Login apos criacao...")
    r = http.post(f"{BASE}/v2/auth/multifactor-login",
        json={"document": CPF1, "password": PASSWORD},
        headers=h(sid=sid), timeout_seconds=15)
    print(f"  Login: {r.status_code} {r.text[:500]}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
