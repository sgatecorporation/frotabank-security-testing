import requests

BASE = "https://api.c03.frotabank.com.br"
SESSION = "36d9a3bc-8f35-4210-820b-be3c90419ea2"
CORR = "87390d4f416cd6d39aae9a730e97c81b"

headers = {
    "x-app-name": "br.com.frotabank.app",
    "x-app-platform": "android",
    "x-app-finger-print": "63201bd095adc55e",
    "x-app-build-number": "2026012801",
    "x-app-version": "18.10.18",
    "x-app-device-model": "google / goldfish_x86 / generic_x86_arm / ranchu",
    "sessionid": SESSION,
    "x-correlation-id": CORR,
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip",
    "user-agent": "okhttp/4.11.0",
    "content-type": "application/json",
}

import json

# Teste 1: enviar selfie validation com score forjado
r1 = requests.post(f"{BASE}/user/selfie-validation", headers=headers,
    json={"score": 0.95, "validated": True, "approved": True})
print("selfie-validation:", r1.status_code, r1.text[:500])

# Teste 2: variação do endpoint
r2 = requests.post(f"{BASE}/user/documents/selfie", headers=headers,
    json={"score": 0.95, "validated": True})
print("documents/selfie:", r2.status_code, r2.text[:500])

# Teste 3: status do onboarding pra ver onde estamos
r3 = requests.get(f"{BASE}/user/onboarding-status", headers=headers)
print("onboarding-status:", r3.status_code, r3.text[:500])

# Teste 4: registration status
r4 = requests.get(f"{BASE}/user/registration-status", headers=headers)
print("registration-status:", r4.status_code, r4.text[:500])
