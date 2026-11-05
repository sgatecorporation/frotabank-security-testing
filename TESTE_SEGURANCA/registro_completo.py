import requests, uuid

BASE = "https://api.c03.frotabank.com.br"

def h(sid, corr):
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
        "x-correlation-id": corr,
        "sessionid": sid,
    }

phone = input("Telefone: ").strip()
metodo = "whatsapp"
sid = str(uuid.uuid4())
corr = uuid.uuid4().hex

# Step 1: credentials/exists
print("\n[1] credentials/exists")
r = requests.post(f"{BASE}/v2/credentials/exists", json={"document": "41265599904"}, headers=h(sid, corr))
print(f"  {r.status_code}: {r.text[:200]}")

# Step 2: whitelist
print("\n[2] whitelist")
r = requests.get(f"{BASE}/v2/whitelist/validate-document/41265599904", headers=h(sid, corr))
print(f"  {r.status_code}: {r.text[:200]}")

# Step 3: send code
print("\n[3] send verification code")
r = requests.post(f"{BASE}/v2/verification-code/send", json={
    "verificationCodeType": "onboarding", "phone": phone, "deliveryMethod": metodo
}, headers=h(sid, corr))
print(f"  {r.status_code}: {r.text[:200]}")

code = input("\nCodigo: ").strip()

# Step 4: confirm phone
print("\n[4] phone/confirmation")
r = requests.post(f"{BASE}/phone/confirmation", json={
    "phone": phone, "verificationCode": code
}, headers=h(sid, corr))
print(f"  {r.status_code}: {r.text[:200]}")
data = r.json()
new_sid = data.get("sessionId", sid)
print(f"  Nova sessao: {new_sid}")

# Step 5: cpf validation
print("\n[5] cpf-validation")
r = requests.post(f"{BASE}/user/cpf-validation", json={"cpf": "41265599904"}, headers=h(new_sid, corr))
print(f"  {r.status_code}: {r.text[:200]}")

# Step 6: upload selfie
print("\n[6] selfie upload")
hh = h(new_sid, corr)
del hh["content-type"]
img = r"C:\Users\Acer\AppData\Local\Temp\claude\C--Users-Acer-Documents-Frota\d74a258b-2478-41ad-8c0e-554cc53b8db0\images\42.jpg"
with open(img, "rb") as f:
    r = requests.post(f"{BASE}/user/documents/upload", headers=hh,
        files={"file": ("selfie.jpg", f, "image/jpeg")})
print(f"  {r.status_code}: {r.text[:300]}")

# Step 7: POST /user
print("\n[7] POST /user (criar conta)")
r = requests.post(f"{BASE}/user", json={
    "cpf": "41265599904",
    "name": "Maria Silva Santos",
    "phone": phone,
    "email": "teste@teste.com",
    "password": "Senh@2024!",
    "birthDate": "1990-05-15",
    "motherName": "Ana Silva",
    "professionId": 11,
    "address": {
        "zipCode": "80420000",
        "street": "Rua Comendador Araujo",
        "number": "100",
        "complement": "",
        "neighborhood": "Centro",
        "city": "Curitiba",
        "state": "PR"
    },
    "termsTokens": [
        "fa34f05d-928b-4738-b430-c3571acefd9c",
        "933fa7e1-28da-436e-b767-d568f07b2bcb"
    ]
}, headers=h(new_sid, corr))
print(f"  {r.status_code}: {r.text[:500]}")
