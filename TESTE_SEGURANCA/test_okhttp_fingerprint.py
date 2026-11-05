"""
Testar se o 401 é causado por JA3/TLS fingerprint.
curl_cffi suporta impersonação de OkHttp - testar todas variantes.
"""
from curl_cffi import requests as curl_requests
import uuid, json, time, jwt, sys

BASE = "https://api.c03.frotabank.com.br"
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
        "content-type": "application/json",
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


# Listar impersonações disponíveis no curl_cffi
print("=" * 60)
print("TESTE JA3/TLS FINGERPRINT - OKHTTP IMPERSONATION")
print("=" * 60)

# Obter sessão com chrome120 (que funciona pra outros endpoints)
print("\n[1] Obtendo sessao...")
http_chrome = curl_requests.Session(impersonate="chrome120", timeout=15)
r = http_chrome.post(f"{BASE}/v2/verification-code/send",
    json={"phone": PHONE, "verificationCodeType": "onboarding",
          "deliveryMethod": "whatsapp", "document": CPF},
    headers=h(str(uuid.uuid4())))
print(f"  Envio: {r.status_code}")

code = input("\n>>> CODIGO: ").strip()
r = http_chrome.post(f"{BASE}/phone/confirmation",
    json={"phone": PHONE, "verificationCode": code},
    headers=h(str(uuid.uuid4())), timeout=45)
data = r.json() if r.status_code == 200 else {}
sid = data.get("sessionId", "")
if not sid:
    print(f"  FALHOU: {r.status_code} {r.text[:200]}")
    sys.exit(1)
print(f"  Session: {sid}")

body = {"link": "https://example.com/test.pdf", "type": "digitalDriverLicense"}
url = f"{BASE}/v2/persons/send-document"

# Testar todas as impersonações OkHttp disponíveis
impersonations = [
    "okhttp3_9",
    "okhttp3_11",
    "okhttp3_13",
    "okhttp3_14",
    "okhttp4_9",
    "okhttp4_10",
    "chrome99_android",
    "chrome120",
    "safari17_0",
    "edge101",
]

print("\n" + "=" * 60)
print("TESTES DE IMPERSONATION")
print("=" * 60)

for imp in impersonations:
    try:
        s = curl_requests.Session(impersonate=imp, timeout=15)
        r = s.post(url, json=body, headers=h(sid), timeout=15)
        status = ">>OK<<" if r.status_code != 401 else "401"
        print(f"  {imp:25s} => {status} | body={r.text[:80] or '(vazio)'}")
    except Exception as e:
        print(f"  {imp:25s} => ERRO: {str(e)[:60]}")

# Testar também com HTTP/2 explícito e sem
print("\n" + "=" * 60)
print("TESTES HTTP/1.1 vs HTTP/2")
print("=" * 60)

for imp in ["okhttp4_10", "chrome120"]:
    for http_ver in [None, 2]:
        try:
            kwargs = {"impersonate": imp, "timeout": 15}
            if http_ver:
                kwargs["http_version"] = http_ver
            s = curl_requests.Session(**kwargs)
            r = s.post(url, json=body, headers=h(sid), timeout=15)
            ver_str = f"HTTP/{http_ver}" if http_ver else "default"
            status = ">>OK<<" if r.status_code != 401 else "401"
            print(f"  {imp} + {ver_str:10s} => {status}")
        except Exception as e:
            print(f"  {imp} + {ver_str:10s} => ERRO: {str(e)[:60]}")

# Teste com headers EXATOS do OkHttp (ordem importa)
print("\n" + "=" * 60)
print("TESTE COM HEADERS NA ORDEM EXATA DO OKHTTP")
print("=" * 60)

# OkHttp envia headers nesta ordem específica
okhttp_ordered_headers = [
    ("x-app-name", "br.com.frotabank.app"),
    ("x-app-platform", "android"),
    ("x-app-finger-print", "63201bd095adc55e"),
    ("x-app-build-number", "2026012801"),
    ("x-app-version", "18.10.18"),
    ("x-app-device-model", "google / goldfish_x86 / generic_x86_arm / ranchu"),
    ("content-type", "application/json; charset=utf-8"),
    ("user-agent", "okhttp/4.11.0"),
    ("accept", "application/json, text/plain, */*"),
    ("accept-encoding", "gzip"),
    ("x-correlation-id", CORR),
    ("sessionId", sid),
    ("sg-signature", pt()),
    ("x-device-coords-latitude", "-25.4284"),
    ("x-device-coords-longitude", "-49.2733"),
    ("x-device-coords-altitude", "0"),
    ("x-device-coords-speed", "0"),
]

# curl_cffi com okhttp4 e charset no content-type
for imp in ["okhttp4_10", "okhttp3_14"]:
    try:
        s = curl_requests.Session(impersonate=imp, timeout=15)
        hh = dict(okhttp_ordered_headers)
        r = s.post(url, json=body, headers=hh, timeout=15)
        status = ">>OK<<" if r.status_code != 401 else "401"
        print(f"  {imp} + charset=utf-8: {status} | {r.text[:80] or '(vazio)'}")
    except Exception as e:
        print(f"  {imp} + charset=utf-8: ERRO: {str(e)[:60]}")

# Teste sem sg-signature (talvez o nginx rejeite o sg-signature inválido?)
print("\n  Teste sem sg-signature...")
hh_nosig = dict(okhttp_ordered_headers)
del hh_nosig["sg-signature"]
try:
    s = curl_requests.Session(impersonate="okhttp4_10", timeout=15)
    r = s.post(url, json=body, headers=hh_nosig, timeout=15)
    print(f"  okhttp4_10 sem sg-sig: {r.status_code} | {r.text[:80] or '(vazio)'}")
except Exception as e:
    print(f"  ERRO: {str(e)[:60]}")

print("\n" + "=" * 60)
print("FIM")
print("=" * 60)
