import requests, uuid

BASE = "https://api.c03.frotabank.com.br"
SESSION = str(uuid.uuid4())
CORR = uuid.uuid4().hex

def h():
    return {
        "x-app-name": "br.com.frotabank.app", "x-app-platform": "android",
        "x-app-finger-print": "63201bd095adc55e", "x-app-build-number": "2026012801",
        "x-app-version": "18.10.18",
        "x-app-device-model": "google / goldfish_x86 / generic_x86_arm / ranchu",
        "content-type": "application/json", "user-agent": "okhttp/4.11.0",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip",
        "x-correlation-id": CORR,
        "sessionid": SESSION,
    }

print(f"SessionID: {SESSION}")

phone = input("Telefone (11984636182): ").strip()
print("Enviar por:\n  1 - WhatsApp\n  2 - SMS")
metodo = "whatsapp" if input("Escolha: ").strip() == "1" else "sms"

print("\n[0] Registrando sessao...")
r = requests.get(f"{BASE}/v2/application/time", headers=h())
print(f"  {r.status_code}: {r.text}")

print(f"\n[1] Enviando codigo via {metodo}...")
r = requests.post(f"{BASE}/v2/verification-code/send",
    json={"phone": phone, "verificationCodeType": "onboarding", "deliveryMethod": metodo}, headers=h())
print(f"  {r.status_code}: {r.text}")

if r.status_code != 200:
    print("Falhou"); exit()

code = input("\nCodigo recebido: ").strip()
print("\n[2] Confirmando codigo...")
r = requests.post(f"{BASE}/phone/confirmation",
    json={"phone": phone, "verificationCode": code}, headers=h())
print(f"  {r.status_code}: {r.text}")

try:
    data = r.json()
    sid = data.get("sessionId")
    if sid:
        print(f"\n*** SESSION ID DO SERVIDOR: {sid} ***")
        cpf = input("\nCPF: ").strip()
        hh = h()
        hh["sessionid"] = sid
        print("\n[3] Validando CPF...")
        r = requests.post(f"{BASE}/user/cpf-validation", json={"cpf": cpf}, headers=hh)
        print(f"  {r.status_code}: {r.text}")
except Exception as e:
    print(f"  erro: {e}")
