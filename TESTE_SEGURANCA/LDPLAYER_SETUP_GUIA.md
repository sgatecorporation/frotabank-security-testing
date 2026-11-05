# LDPlayer + Frida + Captura do POST /user — Guia Completo

## Objetivo
Rodar o Frotabank no LDPlayer (emulador Windows), com câmera virtual funcionando, Frida ativo capturando os requests reais, especialmente o `POST /user` que a gente precisa pra descobrir o formato exato da signature.

---

## Passo 1 — Instalar LDPlayer

1. Baixa https://br.ldplayer.net/
2. Instala
3. Abre e cria uma instância Android 9 (API 28) — mais estável pra Frida
4. **Ativa Root:** Config → Advanced settings → **Root permission: ON**
5. **CPU/RAM:** 4 cores / 4GB mínimo
6. **Resolução:** 1280x720 (celular padrão)

---

## Passo 2 — Configurar Câmera Virtual

LDPlayer vem com camera virtual embutida:

1. Abre LDPlayer → Config (icone de engrenagem) → **Properties settings**
2. Em "Camera", escolhe:
   - **Webcam** (usa a câmera do seu PC)
   - OU **Local file** (aponta pra imagem de selfie/documento)

**Recomendado:** Webcam, assim o Unico Liveness detecta movimento real.

Se não tiver webcam, usa Local file apontando pra uma selfie da pessoa real do CPF (precisa match com documento).

---

## Passo 3 — Instalar APK Frotabank

```powershell
cd C:\Users\Acer\Documents\Frota
# LDPlayer tem adb proprio em: C:\LDPlayer\LDPlayer9\adb.exe
# Ou usa adb normal se tiver no PATH

# Conectar no LDPlayer (porta 5555)
adb connect 127.0.0.1:5555

# Instalar APK
adb install app.apk
```

Se tiver o APK em outro lugar, substitui o path.

---

## Passo 4 — Instalar Frida Server (x86)

LDPlayer e x86, nao arm64. Usa o `frida-server-16.0.19-android-x86` que ja esta baixado.

```powershell
cd C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\setup

# Push pro device (como root)
adb push frida-server-16.0.19-android-x86 /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"

# Rodar como root
adb shell "su -c '/data/local/tmp/frida-server &'"
```

**Validar:** `frida-ps -U` (deve listar processos do device).

Se Frida 16 nao funcionar, usa `frida-server-17.23.3-android-arm64` — nao, isso e arm. Fica no 16 x86.

---

## Passo 5 — Instalar Frida Tools no PC (se nao tiver)

```powershell
py -3.14 -m pip install frida-tools frida==16.0.19
```

---

## Passo 6 — Rodar o Capture Script

Criei um script dedicado em `scripts_frida/09_capture_post_user.js` que:
- Loga APENAS o POST `/user` (sem ruido)
- Salva num arquivo `captured_requests.log`
- Mostra method, URL, headers completos, body completo, response

Pra rodar:

```powershell
cd C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\scripts_frida
python 00_run_frida.py 09_capture_post_user.js
```

**Deixa rodando enquanto faz o fluxo no app.**

---

## Passo 7 — Fluxo no App

1. Abre Frotabank no LDPlayer
2. Faz cadastro normalmente:
   - CPF novo
   - Telefone (recebe codigo no telefone de verdade — WhatsApp/SMS)
   - Dados pessoais
   - Senha
   - Documento (CNH ou RG — pode anexar foto)
   - Selfie (camera do LDPlayer vai abrir)
3. **Enquanto faz, o Frida vai capturar tudo**

---

## Passo 8 — Analisar os Dados Capturados

Depois do fluxo, abre `captured_requests.log` e procura:

```
=== POST /user ===
HEADERS:
  Content-Type: application/json; charset=utf-8
  sessionId: <uuid>
  sg-signature: eyJhbGciOi...
  x-device-key-signature: <base64>
  x-device-key-headers: <lista>
  x-device-key-user-id: <cpf>
  ... (outros headers)
BODY: {"addresses":[...],"birthday":"...",...}
RESPONSE: 201 {...}
```

Com isso a gente compara byte por byte com o que nosso dashboard envia e descobre a diferenca.

---

## Troubleshooting

### "frida-server nao abre"
- Confere se LDPlayer tem root ativo
- Checa `adb shell "su -c 'id'"` — deve retornar uid=0(root)

### "Camera nao abre no app"
- No LDPlayer, confere Config → Camera esta WebCam ou Local file
- Reinstala o app

### "SSL Pinning falha, requests nao saem"
- Carrega o script 07_ssl_unpin_and_proxy.js JUNTO com o 09
- OU use frida-ps pra ver se ha outros processos relacionados

### "App detecta Frida e crasha"
- O Frotabank pode ter anti-Frida (via Shield)
- Usa `frida-server` renomeado:
  ```
  adb shell "mv /data/local/tmp/frida-server /data/local/tmp/fs-x86"
  adb shell "su -c '/data/local/tmp/fs-x86 -l 127.0.0.1:27043 &'"
  frida-ps -U -R
  ```

### "LDPlayer trava com Frida"
- Reduzir CPUs do emulador pra 2
- Fechar outros apps

---

## Objetivo Final

Com o `POST /user` capturado, a gente descobre:
1. O que vai EXATAMENTE no header `x-device-key-signature`
2. Como o canonical string e montado (ordem exata dos campos)
3. Que headers nao sabiamos que eram enviados
4. Se tem algum campo extra no body

Dai atualizo o backend do dashboard pra bater exatamente com isso.

---

## Resumo Rapido

```
1. Instala LDPlayer com root + camera webcam
2. adb connect 127.0.0.1:5555
3. adb install Frotabank.apk
4. adb push frida-server-16.0.19-android-x86 /data/local/tmp/frida-server
5. adb shell "su -c '/data/local/tmp/frida-server &'"
6. python 00_run_frida.py 09_capture_post_user.js
7. Faz cadastro no app
8. Analisa captured_requests.log
```
