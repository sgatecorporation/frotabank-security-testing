import requests, uuid

BASE = "https://api.c03.frotabank.com.br"
def h():
    return {
        "x-app-name": "br.com.frotabank.app", "x-app-platform": "android",
        "x-app-finger-print": "63201bd095adc55e", "x-app-build-number": "2026012801",
        "x-app-version": "1.15.0", "x-app-device-model": "SM-G998B",
        "content-type": "application/json", "user-agent": "okhttp/4.11.0",
        "accept": "application/json, text/plain, */*",
        "x-correlation-id": str(uuid.uuid4()),
    }

phone = input("Telefone (11984636182): ").strip()
print("Enviar por:")
print("  1 - WhatsApp")
print("  2 - SMS")
metodo = "whatsapp" if input("Escolha (1 ou 2): ").strip() == "1" else "sms"

print(f"\n[1] Enviando codigo via {metodo}...")
r = requests.post(f"{BASE}/v2/verification-code/send",
                  json={"phone": phone, "verificationCodeType": "onboarding", "deliveryMethod": metodo}, headers=h())
print(f"  {r.status_code}: {r.text}")

if r.status_code == 200:
    code = input("\nCodigo recebido: ").strip()
    print("\n[2] Confirmando codigo...")
    r = requests.post(f"{BASE}/phone/confirmation",
                      json={"phone": phone, "code": code}, headers=h())
    print(f"  {r.status_code}: {r.text}")
    try:
        data = r.json()
        sid = data.get("sessionId")
        if sid:
            print(f"\n*** SESSION ID: {sid} ***")
            cpf = input("\nCPF (so numeros): ").strip()
            hh = h()
            hh["sessionid"] = sid
            print("\n[3] Validando CPF...")
            r = requests.post(f"{BASE}/user/cpf-validation", json={"cpf": cpf}, headers=hh)
            print(f"  {r.status_code}: {r.text}")
    except:
        print("  erro ao parsear resposta")
