"""Envia codigo de verificacao por SMS para usar no app"""
import requests, uuid, time, jwt, sys

BASE = "https://api.c03.frotabank.com.br"
CORR = uuid.uuid4().hex
PINNING_SECRET = "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf"
PINNING_ISSUER = "frotabank"

def pinning_token():
    return jwt.encode({"iss": PINNING_ISSUER, "iat": int(time.time())}, PINNING_SECRET, algorithm="HS256")

def h():
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
        "sessionId": str(uuid.uuid4()),
        "sg-signature": pinning_token(),
    }

phone = sys.argv[1] if len(sys.argv) > 1 else "11922056147"
cpf = sys.argv[2] if len(sys.argv) > 2 else "03652399846"

http = requests.Session()
http.timeout = 15

print(f"Enviando codigo SMS para {phone} (CPF {cpf})...\n")

for code_type in ["onboarding", "login", "password_recovery", "passwordCreation", "createPassword"]:
    for ph in [f"({phone[:2]}) {phone[2:7]}-{phone[7:]}", phone]:
        body = {"phone": ph, "verificationCodeType": code_type,
                "deliveryMethod": "phone", "document": cpf}
        r = http.post(f"{BASE}/v2/verification-code/send", json=body, headers=h())
        fmt = "fmt" if "(" in ph else "raw"
        if r.status_code == 200:
            print(f"  OK! tipo={code_type} phone={fmt} -> {r.text[:100]}")
            print(f"\n>>> Codigo enviado por SMS! Use no app.")
            sys.exit(0)
        else:
            print(f"  {code_type}/{fmt}: {r.status_code} | {r.text[:100]}")

print("\nNenhum tipo funcionou por SMS. Tentando WhatsApp...")
for code_type in ["onboarding", "login"]:
    body = {"phone": phone, "verificationCodeType": code_type,
            "deliveryMethod": "whatsapp", "document": cpf}
    r = http.post(f"{BASE}/v2/verification-code/send", json=body, headers=h())
    if r.status_code == 200:
        print(f"  OK via WhatsApp! tipo={code_type}")
        break
