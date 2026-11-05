"""
Teste com tls_client (suporta OkHttp TLS fingerprint REAL).
Testa POST /v2/persons/send-document com fingerprint OkHttp nativo.
"""
import tls_client
import uuid, json, time, jwt, sys

BASE = "https://api.c03.frotabank.com.br"
SAFEGUARD_API_KEY = "624ec48b-4ad7-4367-afd9-294a7f7e8c53"
SAFEGUARD_API_URL = "https://id.c03.frotabank.com.br/"
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"
CPF = "41265599904"
PHONE = "11984636182"
CORR = uuid.uuid4().hex


def pt():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")


def h(sid):
    return {
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
        "sessionId": sid,
        "sg-signature": pt(),
        "x-device-coords-latitude": "-25.4284",
        "x-device-coords-longitude": "-49.2733",
        "x-device-coords-altitude": "0",
        "x-device-coords-speed": "0",
    }


print("=" * 60)
print("TESTE TLS_CLIENT - OKHTTP FINGERPRINT REAL")
print("=" * 60)

# PASSO 1: Obter sessao usando okhttp4_android_13
print("\n[1] Obter sessao com okhttp4_android_13...")
http = tls_client.Session(client_identifier="okhttp4_android_13", random_tls_extension_order=True)

r = http.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h(str(uuid.uuid4())))
print(f"  Envio codigo: {r.status_code}")

if r.status_code != 200:
    print(f"  Tentando sem randomizar TLS extensions...")
    http = tls_client.Session(client_identifier="okhttp4_android_13")
    r = http.post(f"{BASE}/v2/verification-code/send",
        json={"phone": PHONE, "verificationCodeType": "onboarding",
              "deliveryMethod": "whatsapp", "document": CPF},
        headers=h(str(uuid.uuid4())))
    print(f"  Envio codigo: {r.status_code}")

code = input("\n>>> CODIGO: ").strip()

r = http.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(str(uuid.uuid4())), timeout_seconds=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  Session: {sid}")

# CPF validation
r = http.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid))
print(f"  CPF validation: {r.status_code}")

body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}
url = f"{BASE}/v2/persons/send-document"

# PASSO 2: Testar TODOS os fingerprints OkHttp
print("\n" + "=" * 60)
print("TESTE FINGERPRINTS OKHTTP (tls_client)")
print("=" * 60)

okhttp_ids = [
    "okhttp4_android_7",
    "okhttp4_android_8",
    "okhttp4_android_9",
    "okhttp4_android_10",
    "okhttp4_android_11",
    "okhttp4_android_12",
    "okhttp4_android_13",
]

for ident in okhttp_ids:
    try:
        s = tls_client.Session(client_identifier=ident, random_tls_extension_order=True)
        r = s.post(url, json=body, headers=h(sid), timeout_seconds=15)
        tag = ">>>OK<<<" if r.status_code != 401 else "401"
        print(f"  {ident:30s} => {tag} | body={r.text[:80] or '(vazio)'}")
    except Exception as e:
        print(f"  {ident:30s} => ERRO: {str(e)[:60]}")

# PASSO 3: Testar com HTTP/2 forçado
print("\n" + "=" * 60)
print("TESTE HTTP/2 FORCADO")
print("=" * 60)

for ident in ["okhttp4_android_13", "okhttp4_android_12"]:
    try:
        s = tls_client.Session(
            client_identifier=ident,
            random_tls_extension_order=True,
            force_http1=False,
        )
        r = s.post(url, json=body, headers=h(sid), timeout_seconds=15)
        tag = ">>>OK<<<" if r.status_code != 401 else "401"
        print(f"  {ident} + H2: {tag} | {r.text[:80] or '(vazio)'}")
    except Exception as e:
        print(f"  {ident} + H2: ERRO: {str(e)[:60]}")

# PASSO 4: Testar GET /v2/personstatus (outro endpoint bloqueado)
print("\n" + "=" * 60)
print("TESTE GET /v2/personstatus")
print("=" * 60)

s = tls_client.Session(client_identifier="okhttp4_android_13", random_tls_extension_order=True)
r = s.get(f"{BASE}/v2/personstatus", headers=h(sid), timeout_seconds=15)
print(f"  GET /v2/personstatus: {r.status_code} | {r.text[:100] or '(vazio)'}")

# PASSO 5: Testar endpoint que funciona, pra confirmar que tls_client ta OK
print("\n" + "=" * 60)
print("CONTROLE: endpoint que funciona")
print("=" * 60)

r = s.post(f"{BASE}/user/cpf-validation", json={"cpf": CPF}, headers=h(sid), timeout_seconds=15)
print(f"  POST /user/cpf-validation: {r.status_code} | {r.text[:100]}")

r = s.get(f"{BASE}/professions", headers=h(sid), timeout_seconds=15)
print(f"  GET /professions: {r.status_code} | (lista de profissoes)")

# PASSO 6: Testar com header_order explícito (OkHttp envia headers em ordem específica)
print("\n" + "=" * 60)
print("TESTE COM HEADER ORDER EXPLICITO")
print("=" * 60)

s = tls_client.Session(
    client_identifier="okhttp4_android_13",
    random_tls_extension_order=True,
    header_order=[
        "x-app-name",
        "x-app-platform",
        "x-app-finger-print",
        "x-app-build-number",
        "x-app-version",
        "x-app-device-model",
        "content-type",
        "content-length",
        "host",
        "connection",
        "accept",
        "user-agent",
        "accept-encoding",
        "x-correlation-id",
        "sessionId",
        "sg-signature",
        "x-device-coords-latitude",
        "x-device-coords-longitude",
        "x-device-coords-altitude",
        "x-device-coords-speed",
    ]
)
r = s.post(url, json=body, headers=h(sid), timeout_seconds=15)
tag = ">>>OK<<<" if r.status_code != 401 else "401"
print(f"  okhttp4_android_13 + header_order: {tag} | {r.text[:100] or '(vazio)'}")

# PASSO 7: Testar sem sg-signature
print("\n  Sem sg-signature...")
hh = h(sid)
del hh["sg-signature"]
r = s.post(url, json=body, headers=hh, timeout_seconds=15)
print(f"  Sem sg-sig: {r.status_code} | {r.text[:80] or '(vazio)'}")

# PASSO 8: Response headers completos
print("\n  Response headers do 401:")
r = s.post(url, json=body, headers=h(sid), timeout_seconds=15)
for k, v in r.headers.items():
    print(f"    {k}: {v}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
