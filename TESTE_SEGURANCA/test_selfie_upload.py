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
}

img = r"C:\Users\Acer\AppData\Local\Temp\claude\C--Users-Acer-Documents-Frota\d74a258b-2478-41ad-8c0e-554cc53b8db0\images\42.jpg"

with open(img, "rb") as f:
    r = requests.post(f"{BASE}/user/documents/upload", headers=headers,
                      files={"file": ("selfie.jpg", f, "image/jpeg")})

print("Status:", r.status_code)
print("Body:", r.text[:2000])
