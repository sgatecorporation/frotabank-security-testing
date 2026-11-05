import requests

BASE = "https://api.c03.frotabank.com.br"
CORR = "c640c437d8bff45059b526752a8dc633"

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
        "sessionid": sid,
    }

payload = {
    "cpf": "41265599904",
    "name": "Maria Silva Santos",
    "phone": "11984636182",
    "email": "teste@teste.com",
    "password": "Senh@2024!",
    "birthDate": "1990-05-15",
    "motherName": "Ana Silva",
}

# Teste com sessao antiga da sessao anterior
print("=== Sessao antiga (36d9a3bc) ===")
r = requests.post(f"{BASE}/user", json=payload, headers=h("36d9a3bc-8f35-4210-820b-be3c90419ea2"))
print(f"  {r.status_code}: {r.text[:400]}")

# Teste com sessao atual
print("\n=== Sessao atual (678bdf37) ===")
r = requests.post(f"{BASE}/user", json=payload, headers=h("678bdf37-c6ac-4b5f-9548-e4890af7876c"))
print(f"  {r.status_code}: {r.text[:400]}")

# Teste sem password pra ver se da erro diferente
print("\n=== Sem password ===")
p2 = {k:v for k,v in payload.items() if k != "password"}
r = requests.post(f"{BASE}/user", json=p2, headers=h("678bdf37-c6ac-4b5f-9548-e4890af7876c"))
print(f"  {r.status_code}: {r.text[:400]}")

# Teste sem sessionid
print("\n=== Sem sessionid ===")
hh = h("678bdf37-c6ac-4b5f-9548-e4890af7876c")
del hh["sessionid"]
r = requests.post(f"{BASE}/user", json=payload, headers=hh)
print(f"  {r.status_code}: {r.text[:400]}")

# Teste com body vazio e password valida
print("\n=== Minimo: so cpf+phone+password ===")
r = requests.post(f"{BASE}/user", json={
    "cpf": "41265599904",
    "phone": "11984636182",
    "password": "Senh@2024!",
}, headers=h("678bdf37-c6ac-4b5f-9548-e4890af7876c"))
print(f"  {r.status_code}: {r.text[:400]}")
