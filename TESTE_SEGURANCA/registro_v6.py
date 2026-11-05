import requests, uuid

BASE = "https://api.c03.frotabank.com.br"
def h():
    return {
        "x-app-name": "br.com.frotabank.app", "x-app-platform": "android",
        "x-app-finger-print": "63201bd095adc55e", "x-app-build-number": "2026012801",
        "x-app-version": "18.10.18", "x-app-device-model": "google / goldfish_x86 / generic_x86_arm / ranchu",
        "content-type": "application/json", "user-agent": "okhttp/4.11.0",
        "accept": "application/json, text/plain, */*",
        "x-correlation-id": str(uuid.uuid4()),
    }

phone = input("Telefone (11984636182): ").strip()
print("Enviar por:\n  1 - WhatsApp\n  2 - SMS")
metodo = "whatsapp" if input("Escolha: ").strip() == "1" else "sms"

print(f"\n[1] Enviando codigo via {metodo}...")
headers1 = h()
r = requests.post(f"{BASE}/v2/verification-code/send",
                  json={"phone": phone, "verificationCodeType": "onboarding", "deliveryMethod": metodo}, headers=headers1)
print(f"  {r.status_code}: {r.text}")
print(f"  Headers resposta: {dict(r.headers)}")

code = input("\nCodigo recebido: ").strip()

print("\n[2] Confirmando codigo...")
headers2 = h()
# Tentar com sessionid do response anterior se existir
try:
    sid = r.json().get("sessionId") or r.headers.get("sessionid")
    if sid:
        headers2["sessionid"] = sid
        print(f"  Usando sessionId: {sid}")
except:
    pass

r2 = requests.post(f"{BASE}/phone/confirmation",
                   json={"verificationCode": code}, headers=headers2)
print(f"  {r2.status_code}: {r2.text}")
print(f"  Headers resposta: {dict(r2.headers)}")

try:
    data = r2.json()
    sid2 = data.get("sessionId")
    if sid2:
        print(f"\n*** SESSION ID: {sid2} ***")
        cpf = input("\nCPF (so numeros): ").strip()
        hh = h()
        hh["sessionid"] = sid2
        print("\n[3] Validando CPF...")
        r3 = requests.post(f"{BASE}/user/cpf-validation", json={"cpf": cpf}, headers=hh)
        print(f"  {r3.status_code}: {r3.text}")
except Exception as e:
    print(f"  erro: {e}")
