import requests, uuid

BASE = "https://api.c03.frotabank.com.br"
H = {
    "x-app-name": "frotabank", "x-app-platform": "android",
    "x-app-finger-print": "a1b2c3d4e5f6", "x-app-build-number": "87",
    "x-app-version": "1.15.0", "x-app-device-model": "SM-G998B",
    "content-type": "application/json", "user-agent": "okhttp/4.11.0",
    "x-correlation-id": str(uuid.uuid4()),
}

phone = input("Telefone (11984636182): ").strip()
phone = "+55" + phone

tentativas = [
    "phone_sms", "phone_whatsapp", "registration_sms", "registration_whatsapp",
    "register_sms", "register_whatsapp", "signup_sms", "signup_whatsapp",
    "onboarding_sms", "onboarding_whatsapp",
    "phone-sms", "phone-whatsapp",
    "PHONE_SMS", "PHONE_WHATSAPP",
    "phoneVerification", "phoneWhatsapp",
]

for t in tentativas:
    H["x-correlation-id"] = str(uuid.uuid4())
    r = requests.post(f"{BASE}/v2/verification-code/send",
                      json={"phone": phone, "verificationCodeType": t}, headers=H)
    status = "OK!" if r.status_code == 200 else str(r.status_code)
    print(f"  {t:30s} -> {status}")
    if r.status_code == 200:
        print(f"\n*** FUNCIONOU: {t} ***")
        print(r.text)
        break
