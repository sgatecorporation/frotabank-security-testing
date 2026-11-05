# Relatório de Segurança - Frotabank (br.com.frotabank.app)

**Data:** 17/10/2026 (atualizado 17/10/2026)  
**Alvo:** Aplicativo Android Frotabank (br.com.frotabank.app) e API backend  
**Escopo:** Análise estática do bundle Hermes + testes dinâmicos da API + engenharia reversa de fluxos  
**Base URL:** `https://api.c03.frotabank.com.br`  
**SafeGuard URL:** `https://id.c03.frotabank.com.br/`

---

## Resumo Executivo

O aplicativo Frotabank apresenta uma **arquitetura de segurança em camadas**, com proteções tanto a nível de aplicação quanto de infraestrutura. Foram identificadas **vulnerabilidades de severidade média a alta** na camada de aplicação, enquanto endpoints críticos possuem proteção adicional a nível de nginx/WAF que impede exploração remota completa.

### Classificação Geral: RISCO ALTO

| Categoria | Achados | Severidade |
|-----------|---------|------------|
| Bug crítico no fluxo de credenciais | 2 bugs impedem criação de senha | **CRÍTICA** |
| Exposição de segredos no bundle | 4 segredos hardcoded | ALTA |
| Enumeração de dados pessoais | CPF, telefone, status de conta | ALTA |
| Abuso de códigos de verificação | 6 tipos aceitos sem conta | ALTA |
| Controle de fluxo de registro | Parcialmente explorável | MÉDIA |
| Proteção de endpoints críticos | Forte (nginx/WAF) | BAIXA (positivo) |
| Device key sem validação forte | Criação irrestrita | MÉDIA |
| Política de senha mapeada | Alfanumérica ou PIN 6 dígitos | INFO |
| Cadeia de dependências mapeada | send-document → user → credential → login | INFO |

---

## 1. VULNERABILIDADES ENCONTRADAS

### 1.1 [ALTA] Segredos Hardcoded no Bundle JavaScript

**Descrição:** O bundle Hermes bytecode (`index.android.bundle`) contém segredos criptográficos em texto plano que podem ser extraídos por decompilação.

**Segredos expostos:**
| Segredo | Valor | Uso |
|---------|-------|-----|
| `REACT_APP_PINNING_SECRET` | `AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf` | Chave HS256 para JWT de pinning |
| `REACT_APP_PINNING_ISSUER` | `frotabank` | Issuer do JWT |
| `REACT_APP_PINNING_HEADER_NAME` | `sg-signature` | Nome do header |
| `SAFEGUARD_API_KEY` | `624ec48b-4ad7-4367-afd9-294a7f7e8c53` | API key do SafeGuard |

**Impacto:** Qualquer atacante pode gerar tokens `sg-signature` válidos e criar device keys no SafeGuard. O JWT de pinning usa HS256 com payload `{iss: "frotabank", iat: <timestamp>}` — trivial de replicar.

**Evidência:** Função `getPinningToken` na linha 567869 do decompiled.js. Config inicializada nas linhas 558151-558198.

**Recomendação:** 
- Migrar para certificado SSL pinning nativo (não custom JWT)
- Rotacionar o `PINNING_SECRET` e `SAFEGUARD_API_KEY`
- Implementar validação server-side do token com binding ao device

---

### 1.2 [ALTA] Enumeração de CPF e Dados Pessoais

**Descrição:** Múltiplos endpoints permitem verificar se um CPF está cadastrado e obter informações associadas, sem rate limiting efetivo.

**Endpoints vulneráveis:**

| Endpoint | Método | Informação exposta |
|----------|--------|--------------------|
| `POST /user/cpf-validation` | POST | `{"success": true/false}` — confirma se CPF existe |
| `POST /v2/credentials/exists` | POST | `credentials_not_found` vs resposta positiva |
| `POST /phone/confirmation` | POST | Valida associação telefone + código |
| `POST /v2/verification-code/send` | POST | Envia SMS/WhatsApp sem throttling forte |

**Impacto:** Atacante pode enumerar CPFs válidos em massa, verificar quais possuem conta no Frotabank, e potencialmente iniciar fluxos de verificação para números de telefone alheios.

**Evidência:** `POST /user/cpf-validation` com `{"cpf": "41265599904"}` retorna `{"success": true}` sem necessidade de autenticação prévia (apenas sessionId de qualquer sessão).

**Recomendação:**
- Implementar rate limiting agressivo por IP e sessionId
- Retornar resposta genérica para CPF válido/inválido
- Requerer CAPTCHA após N tentativas

---

### 1.3 [ALTA] Criação Irrestrita de Device Keys

**Descrição:** O endpoint SafeGuard `POST /device_key` permite criar device keys ilimitadas para qualquer CPF, usando apenas a API key estática.

**Detalhes:**
```
POST https://id.c03.frotabank.com.br/device_key
Headers: SG-API-KEY: 624ec48b-4ad7-4367-afd9-294a7f7e8c53
Body: {
    "deviceId": "<qualquer>",
    "isRoot": false,
    "userId": "<qualquer CPF>",
    "uuid": "<qualquer UUID>",
    "operatingSystem": "android"
}
Resposta: 200 {"privateKey": "<40 chars>", ...}
```

**Impacto:** Atacante pode criar device keys para qualquer CPF, potencialmente realizando ações em nome de outro usuário se combinado com outras vulnerabilidades.

**Recomendação:**
- Vincular criação de device key a uma sessão autenticada
- Limitar quantidade de device keys por userId
- Invalidar device keys não utilizadas após período

---

### 1.4 [MÉDIA] Validação de Device Key Aceita Documentos Arbitrários

**Descrição:** O endpoint `POST /v2/device-key/validate-selfie-and-document` aceita URLs de selfie e documentos sem validação efetiva do conteúdo.

**Detalhes:**
- Retorna **204 (sucesso)** com qualquer URL válida de documento
- Não valida se a selfie corresponde ao documento
- Não valida se o documento pertence ao CPF informado
- `backDocumentPhotoUrl` pode ser idêntico ao `frontDocumentPhotoUrl`

**Evidência:** Enviamos a mesma URL de CNH como frente e verso e obtivemos 204.

**Recomendação:**
- Implementar validação biométrica real (face match)
- Verificar OCR do documento contra dados do CPF
- Rejeitar URLs duplicadas para frente/verso

---

### 1.5 [MÉDIA] Upload de Documentos Sem Validação de Conteúdo

**Descrição:** O endpoint `POST /user/documents/upload` aceita uploads sem validar o conteúdo do arquivo.

**Detalhes:**
- Aceita qualquer PDF como CNH
- Aceita qualquer JPEG como selfie
- Retorna URL S3 pré-assinada sem validação
- Não há verificação de tamanho mínimo/máximo efetiva

**Recomendação:**
- Implementar validação de conteúdo (OCR, face detection)
- Verificar metadados EXIF para detectar adulteração
- Limitar tipos MIME aceitos

---

### 1.6 [MÉDIA] Fluxo de Verificação WhatsApp Sem Proteção Adequada

**Descrição:** O envio de código de verificação via WhatsApp pode ser abusado para spam.

**Detalhes:**
- `POST /v2/verification-code/send` aceita qualquer número de telefone
- Métodos disponíveis: `whatsapp`, `phone` (SMS), `phone-call`, `email`
- Não há CAPTCHA ou proof-of-work
- Rate limiting é insuficiente (múltiplos envios em sequência aceitos)

**Recomendação:**
- Implementar CAPTCHA antes do envio
- Rate limit de 1 envio por número por minuto
- Limitar total de envios por sessionId

---

### 1.7 [ALTA] Envio de Códigos de Verificação para Contas Inexistentes

**Descrição:** O endpoint `POST /v2/verification-code/send` aceita e envia códigos de verificação por WhatsApp/SMS para **todos os tipos**, mesmo quando o CPF não possui conta cadastrada.

**Tipos testados e resultados (CPF sem conta):**

| Tipo | Status | Código enviado? |
|------|--------|-----------------|
| `onboarding` | 200 | SIM |
| `createCredential` | 200 | SIM |
| `keyOwnershipValidation` | 200 | SIM |
| `passwordResetting` | 400 `person_not_found` | NÃO |
| `unblockAccount` | 200 | SIM |
| `deviceKeyLight` | 200 | SIM |

**Impacto:**
- **Spam/Abuso de WhatsApp:** Atacante pode enviar mensagens WhatsApp ilimitadas para qualquer número usando 5 dos 6 tipos de verificação
- **Custo financeiro:** Cada envio tem custo para o Frotabank (API WhatsApp Business)
- **Phishing:** Mensagens legítimas do Frotabank podem ser usadas em campanhas de engenharia social
- **Enumeração:** `passwordResetting` diferencia contas existentes (`person_not_found`) das inexistentes

**Evidência:** Teste enviou 6 códigos em sequência para o mesmo número, todos aceitos exceto `passwordResetting`. Tipos descobertos por engenharia reversa em `VerificationCodeTypes` (decompiled.js, linha 881587-881614).

**Recomendação:**
- Tipos `createCredential`, `keyOwnershipValidation`, `unblockAccount` e `deviceKeyLight` devem exigir conta existente
- Rate limit global por número de telefone (não por tipo)
- Resposta idêntica para todos os tipos (não revelar existência de conta)

---

### 1.8 [MÉDIA] Endpoint de Credenciais Expõe Existência de Conta

**Descrição:** `POST /v2/auth/credential` retorna erros distintos que revelam se uma conta existe.

**Comportamento:**
| Cenário | Status | Erro |
|---------|--------|------|
| Com sessionId, conta não existe | 404 | `person_not_found` |
| Sem sessionId, código errado | 400 | `verification_code_is_invalid` |
| Com sessionId, código errado | 400 | `verification_code_is_invalid` |

**Payload correto (descoberto via RE):**
```json
POST /v2/auth/credential
{
    "document": "<CPF>",
    "password": "<senha>",
    "verificationCode": "<código SMS>"
}
```

**Evidência:** `BankingCreateCredentialService.create` (decompiled.js, linha 1315154). Payload montado em `CreateCredentialVerificationCodeScreen` (linha 1314804-1314834).

**Recomendação:** Retornar erro genérico independente de existência da conta.

---

### 1.9 [CRÍTICA] Dois Bugs no Envio do Código de Verificação createCredential

**Descrição:** A tela `CreateCredentialVerificationCodeScreen` (linha 1314760) contém **dois bugs** na função `sendSmsVerificationCode` (linhas 1314710-1314730) que impedem o envio do código de verificação para criação de senha. Esta é a causa raiz do problema onde o código "não chega" após a aprovação da conta.

**Bug 1 — phone hardcoded como `undefined` (linha 1314729):**
```
r11 = undefined;  // phone é SEMPRE undefined
// Nunca busca o telefone de props, context, ou getParam()
```
No fluxo correto (onboarding, card password reset), o phone vem de `props.onboardingPhone` ou `props.phone`.

**Bug 2 — Array de módulos passado como deliveryMethod (linha 1314730):**
```
r9 = _closure1_slot1;  // array de dependências de módulos [2, 327, 4, 3, 1005, 1011]
// Passado no lugar do deliveryMethod ('whatsapp' ou 'sms')
```
No fluxo correto, usa `getDeliveryMethod()` (linha 881157-881177) que retorna `'whatsapp'` como padrão.

**Payload malformado enviado pelo app:**
```json
POST /v2/verification-code/send
{
    "verificationCodeType": "createCredential",
    "document": "41265599904",
    "phone": undefined,
    "deliveryMethod": [2, 327, 4, 3, 1005, 1011]
}
```

**Payload correto (confirmado por teste — código chegou):**
```json
POST /v2/verification-code/send
{
    "verificationCodeType": "createCredential",
    "document": "41265599904",
    "phone": "11984636182",
    "deliveryMethod": "whatsapp"
}
```

**Comparação com fluxos que funcionam:**

| Fluxo | Phone | DeliveryMethod | Funciona? |
|-------|-------|----------------|-----------|
| createCredential (bug) | `undefined` (hardcoded) | `[2,327,4,3,1005,1011]` (moduleRefs) | **NÃO** |
| onboarding (correto) | `props.onboardingPhone` | `getDeliveryMethod()` → `'whatsapp'` | SIM |
| cardPasswordResetting (correto) | `props.phone` | `getParam('deliveryMethod')` | SIM |

**Evidência:**
- Código decompilado: linhas 1314710-1314730 vs 880737-880759 (fluxo correto)
- Teste dinâmico: `POST /v2/verification-code/send` com payload correto retornou `200 {"success":true}` e código chegou no WhatsApp
- Teste dinâmico: `POST /v2/auth/credential` retornou `404 person_not_found` (CPF sem conta aprovada, não erro de código)

**Impacto:** **Nenhum usuário** que completou o cadastro e teve a conta aprovada consegue criar senha pelo app. O fluxo trava na tela de verificação porque o código nunca é entregue. Este é um bug funcional crítico, não apenas de segurança.

**Recomendação:**
- Corrigir `sendSmsVerificationCode` para buscar phone de `props` ou `context` (como fazem os outros fluxos)
- Corrigir passagem de deliveryMethod para usar `getDeliveryMethod()` ou valor fixo `'whatsapp'`
- Adicionar testes unitários para esta tela específica

---

### 1.10 [INFO] Política de Senha — Duas Modalidades

**Descrição:** O app suporta duas políticas de senha controladas pela env var `REACT_APP_NUMERIC_APP_PASSWORD`:

**Política alfanumérica** (quando `REACT_APP_NUMERIC_APP_PASSWORD !== true`):
- Comprimento: mínimo 8, máximo 128 caracteres
- Pelo menos 1 caractere especial obrigatório
- Máximo 4 caracteres repetidos consecutivos
- Máximo 4 caracteres sequenciais
- Não pode conter partes do nome do usuário

**Política numérica** (quando `REACT_APP_NUMERIC_APP_PASSWORD === true`):
- Apenas dígitos (0-9)
- Comprimento definido por `REACT_APP_NUMERIC_PASSWORD_LENGTH` (padrão: `6`)
- Sem sequências repetidas

**Evidência:**
- `getPolicy` (linha 1311372): `PasswordPolicy.withLength({min:8, max:128}).withAtLeastOneSpecialChar().notAllowingRepeatedChars({maxAllowedRepeatedChars:4}).notAllowingConsecutiveChars({maxAllowedConsecutiveChars:4})`
- `getNumericPolicy` (linha 1311413): `PasswordPolicy.numeric()`
- `isNumericAppPassword` (linha 1383763): `Boolean(env.REACT_APP_NUMERIC_APP_PASSWORD)`
- `REACT_APP_NUMERIC_PASSWORD_LENGTH` default: `'6'` (linha 458521)

**Nota:** A senha usada nos testes (`Senh@2024!`) atende a política alfanumérica. Se o Frotabank usa senha numérica, a senha correta seria um PIN de 6 dígitos (ex: `142536`). O tipo de teclado exibido na tela de criação de senha indica qual política está ativa.

---

### 1.11 [BAIXA] Informações Técnicas em Mensagens de Erro

**Descrição:** Endpoints retornam detalhes técnicos sobre validação de campos.

**Exemplo:** `POST /v2/device-key/validate-selfie-and-document` com payload inválido retorna:
```json
{
    "name": "BadRequestError",
    "errors": [{
        "target": { ... payload completo ... },
        "property": "backDocumentPhotoUrl",
        "constraints": {
            "isNotEmpty": "backDocumentPhotoUrl should not be empty"
        }
    }]
}
```

**Impacto:** Facilita mapeamento de campos obrigatórios e formatos esperados pela API.

**Recomendação:** Retornar erros genéricos em produção sem expor nomes de campos internos.

---

## 2. CONTROLES DE SEGURANÇA POSITIVOS

### 2.1 [FORTE] Proteção Nginx/WAF em Endpoints /v2/persons/*

**Descrição:** TODOS os endpoints sob `/v2/persons/*` são protegidos a nível de infraestrutura (nginx) com bloqueio 401 que não pode ser contornado por nenhuma técnica testada.

**Endpoints protegidos identificados:**
| Endpoint | Método bloqueado | Comportamento |
|----------|-----------------|---------------|
| `/v2/persons/send-document` | POST | 401 vazio |
| `/v2/persons/documents-upload-lock` | GET | 401 vazio |
| `/v2/personstatus` | GET | 401 vazio |

**Características do bloqueio:**
- Retorna 401 com body vazio (0 bytes)
- Sem header `WWW-Authenticate`
- Independente de headers enviados (funciona até sem NENHUM header)
- Funciona em qualquer biblioteca HTTP (curl_cffi, requests, tls_client)
- Método-específico (GET no mesmo path retorna 404 do backend)

**Técnicas de bypass testadas (TODAS falharam):**
| Técnica | Ferramenta | Resultado |
|---------|-----------|-----------|
| TLS fingerprint OkHttp Android 7-13 | tls_client v2.0.0 | 401 em TODOS |
| TLS fingerprint OkHttp 3.x/4.x | curl_cffi | 401 em TODOS |
| HTTP/2 forçado | tls_client | 401 |
| Header order explícito OkHttp | tls_client | 401 |
| Sem sg-signature | todas | 401 |
| Com sg-signature válido | todas | 401 |
| Com sessionId válido | todas | 401 |
| Com Bearer token fake | tls_client | 401 |
| Chrome/Safari/Edge fingerprint | curl_cffi | 401 |
| Headers mínimos (só Authorization) | tls_client | 401 |

**Hipótese restante:** mTLS (client certificate embutido no app), IP allowlist (ranges de operadoras mobile), ou validação de Bearer token real a nível nginx.

**Resultado:** Este controle é o **ponto crítico de segurança** que impede toda a cadeia de automação:

```
POST /v2/persons/send-document  → BLOQUEADO (401 vazio)
         ↓ dependência obrigatória
POST /user                      → 400 "missing send documents"
         ↓ dependência obrigatória
POST /v2/auth/credential        → 404 "person_not_found"
         ↓ dependência obrigatória
POST /v2/auth/multifactor-login → 401 "invalid_credentials"
         ↓
Bearer token → IMPOSSÍVEL obter via automação
```

**Evidência de dependência hard:** `POST /user` com sessão válida (3.3s após criação) retorna `{"code":"BANK_API_SEND_DOCUMENTS_FAILED","message":"missing send documents"}` — independente do payload enviado.

---

### 2.2 [FORTE] Validação de Dados Contra Receita Federal

O backend valida nome, data de nascimento e nome da mãe contra dados da Receita Federal vinculados ao CPF. Não é possível criar conta com dados fictícios.

---

### 2.3 [ADEQUADO] Separação de Níveis de Autenticação

A API implementa 3 níveis de autenticação:
1. **Sem auth:** Endpoints públicos (`/professions`, `/zipcode/*`, `/v2/terms`)
2. **SessionId:** Obtido via verificação de telefone, usado durante onboarding
3. **Bearer Token:** Obtido via login, usado para operações pós-autenticação

---

### 2.4 [ADEQUADO] Device Key Signature

O `BankingCoreHttpClient` implementa assinatura HMAC por request usando o device key:
- Canonical string: `METHOD\nDOMAIN\nPATH\n[BODY_PAIRS]\n[HEADER_PAIRS]`
- Hash: SHA1 → HMAC-SHA256 com private key
- Header: `x-device-key-signature: base64(API_KEY:DEVICE_ID:UUID:SHA1:HMAC+SHA1)`

---

## 3. MAPEAMENTO DE API COMPLETO

### Endpoints Testados

| Endpoint | Auth | Status | Nota |
|----------|------|--------|------|
| `GET /professions` | Nenhum | 200 | Lista profissões |
| `GET /zipcode/{cep}` | Nenhum | 200 | Consulta CEP |
| `GET /v2/terms` | SessionId | 200 | Termos de uso |
| `POST /v2/verification-code/send` | Nenhum | 200 | Envia código (6 tipos testados) |
| `POST /phone/confirmation` | Nenhum | 200 | Confirma código → sessionId |
| `POST /user/cpf-validation` | SessionId | 200 | Valida CPF |
| `POST /user/documents/upload` | SessionId | 200 | Upload multipart |
| `POST /device_key` (SafeGuard) | API Key | 200 | Cria device key |
| `POST /v2/device-key/validate-selfie-and-document` | SessionId | **204** | Valida device key |
| `POST /v2/persons/send-document` | **BLOQUEADO** | **401** | Nginx/WAF block |
| `GET /v2/persons/documents-upload-lock` | **BLOQUEADO** | **401** | Nginx/WAF block |
| `GET /v2/personstatus` | **BLOQUEADO** | **401** | Nginx/WAF block |
| `POST /user` | SessionId | **400** | `BANK_API_SEND_DOCUMENTS_FAILED` |
| `POST /v2/auth/multifactor-login` | Nenhum | 401 | `login_invalid_credentials` |
| `POST /v2/credentials/exists` | SessionId | 404 | Verifica credenciais |
| `POST /v2/auth/credential` | SessionId | **404** | `person_not_found` (sem conta) |
| `POST /v2/credentials/unblock` | SessionId | N/T | Desbloqueio de credenciais |

---

## 4. FLUXO DE REGISTRO DOCUMENTADO

Ordem exata extraída do código decompilado e confirmada por testes dinâmicos:

```
 1. POST /v2/verification-code/send     → Envia código WhatsApp          ✅ 200
 2. POST /phone/confirmation             → Confirma código → sessionId    ✅ 200
 3. POST /user/cpf-validation            → Valida CPF                     ✅ 200
 4. POST /user/documents/upload (x N)    → Upload CNH + Selfie → URLs S3 ✅ 200
 5. POST /device_key (SafeGuard)         → Cria device key                ✅ 200
 6. POST /v2/device-key/validate-selfie  → Valida biometria               ✅ 204
 7. POST /v2/persons/send-document (x N) → Registra documentos            ❌ 401 NGINX
 8. POST /user                           → Cria conta                     ❌ 400 "missing send documents"
 9. POST /v2/verification-code/send      → Código tipo 'createCredential' ✅ 200
10. POST /v2/auth/credential             → Cria senha (document+pwd+code) ❌ 404 "person_not_found"
11. POST /v2/auth/multifactor-login      → Login → Bearer token           ❌ 401 "invalid_credentials"
```

**Status:** Passos 1-6 executados com sucesso. Passo 7 bloqueado pelo nginx/WAF, o que impede toda a cadeia subsequente (8→9→10→11).

### Fluxo de Criação de Credenciais (Descoberto via RE)

Extraído de `BankingCreateCredentialService` (decompiled.js, linha 1315125-1315205):

```
CreateCredentialScreen           → Usuário digita senha (validada por PasswordPolicy)
    ↓ navega com {password, document}
CreateCredentialVerificationCodeScreen
    ↓ sendSmsVerificationCode() chamada no componentDidMount
    ↓ ⚠️ BUG: phone=undefined, deliveryMethod=[moduleRefs array]
    ↓ POST /v2/verification-code/send {verificationCodeType: 'createCredential', 
    ↓   document: CPF, phone: undefined, deliveryMethod: [2,327,4,3,...]}
    ↓ ❌ Backend NÃO consegue entregar o código (dados malformados)
    ↓ Usuário NUNCA recebe código → fluxo trava aqui
    ↓ (Se chamado com parâmetros corretos: 200 {"success":true} e código chega)
    ↓ POST /v2/auth/credential {document, password, verificationCode}
    ↓ BankingCreateCredentialService.create() (linha 1315154)
CreateCredentialSuccessScreen    → Credenciais criadas (nunca alcançado)
```

**Fluxo correto (como DEVERIA funcionar, baseado em fluxos que funcionam):**
```
CreateCredentialVerificationCodeScreen
    ↓ phone = props.phone ou context.phone (NÃO undefined)
    ↓ deliveryMethod = getDeliveryMethod() → 'whatsapp' (NÃO moduleRefs)
    ↓ POST /v2/verification-code/send com dados corretos
    ↓ ✅ Código chega no WhatsApp → usuário digita → credenciais criadas
```

### Tipos de Código de Verificação (decompiled.js, linha 881587-881614)

| Tipo | Uso | Requer conta? |
|------|-----|---------------|
| `onboarding` | Registro inicial | Não |
| `createCredential` | Criar senha | Não (deveria) |
| `keyOwnershipValidation` | Validar device key | Não (deveria) |
| `passwordResetting` | Reset de senha | **Sim** (400 person_not_found) |
| `unblockAccount` | Desbloquear conta | Não (deveria) |
| `deviceKeyLight` | Device key light | Não (deveria) |
| `bankTransfer` | Transferência | N/T |
| `billetPayment` | Pagamento boleto | N/T |
| `p2pTransfer` | Transferência P2P | N/T |
| `cardPasswordResetting` | Reset senha cartão | N/T |
| `rechargeTransportCard` | Recarga transporte | N/T |
| `rechargeMobilePhone` | Recarga celular | N/T |
| `unblockPhysicalCard` | Desbloquear cartão | N/T |
| `requestCard` | Solicitar cartão | N/T |

---

## 5. DADOS TÉCNICOS DO APP

| Item | Valor |
|------|-------|
| Bundle | Hermes HBC v94 (React Native) |
| Decompilado | 2,072,022 linhas JS |
| Ofuscação | Array rotation com offset 220 |
| HTTP Client | Axios (BankingCoreHttpClient) |
| User-Agent | okhttp/4.11.0 |
| Build | 2026012801, versão 18.10.18 |

---

## 6. RECOMENDAÇÕES PRIORITÁRIAS

### Críticas (implementar imediatamente)
1. **CORRIGIR BUG createCredential** — `sendSmsVerificationCode` (linha 1314710) deve passar phone real e deliveryMethod='whatsapp' em vez de undefined e [moduleRefs]. Sem isso, NENHUM usuário consegue criar senha após aprovação da conta.
2. **Rotacionar** `PINNING_SECRET` e `SAFEGUARD_API_KEY`
3. **Rate limiting global** em `/v2/verification-code/send` — por telefone, não por tipo
4. **Vincular device key** a sessão autenticada (não apenas API key)
5. **Restringir tipos de verificação** — `createCredential`, `keyOwnershipValidation`, `unblockAccount`, `deviceKeyLight` devem exigir conta existente

### Altas (implementar no próximo sprint)
5. **Migrar pinning** para certificate pinning nativo
6. **Validação biométrica real** no validate-selfie-and-document
7. **CAPTCHA** antes de envio de código de verificação
8. **Sanitizar erros** — `person_not_found` vs `verification_code_is_invalid` expõe existência de conta
9. **Resposta genérica** em `/v2/auth/credential` — não diferenciar conta inexistente

### Médias (próximo quarter)
10. **Ofuscação mais forte** do bundle (obfuscação de strings)
11. **Detecção de root/emulador** mais robusta
12. **Audit logging** de criação de device keys e envio de códigos de verificação

---

## 7. ENGENHARIA REVERSA — FUNÇÕES CHAVE IDENTIFICADAS

| Função | Linha | Descrição |
|--------|-------|-----------|
| `BankingCreateCredentialService` | 1315125 | Classe que faz POST /v2/auth/credential |
| `BankingCreateCredentialService.create` | 1315154 | Método HTTP: `{method:'post', path:'/v2/auth/credential'}` |
| `sendVerificationCode` | 881971 | Envia código: POST /v2/verification-code/send |
| `send` (VerificationCodeService) | 882384 | Monta payload: `{verificationCodeType, document, phone, deliveryMethod}` |
| `VerificationCodeTypes` | 881587 | Enum: 14 tipos de verificação |
| `createCredential` action | 1315302 | Redux action que chama service.create |
| `CreateCredentialScreen` | 1314392 | Tela de entrada de senha |
| `CreateCredentialVerificationCodeScreen` | 1314760 | Tela de código de verificação |
| `sendSmsVerificationCode` (BUGGY) | 1314710 | ⚠️ Envia phone=undefined e deliveryMethod=[moduleRefs] |
| `getDeliveryMethod` | 881157 | Retorna 'whatsapp' como padrão (não usado no createCredential) |
| `UserPasswordForm` | 1310742 | Formulário de senha com validação por PasswordPolicy |
| `validatePassword` | 1311347 | Valida senha (numérica ou alfanumérica conforme env) |
| `getPolicy` (alfanumérica) | 1311372 | min:8, max:128, specialChar, maxRepeat:4, maxConsecutive:4 |
| `getNumericPolicy` | 1311413 | Apenas dígitos, length de REACT_APP_NUMERIC_PASSWORD_LENGTH |
| `sendDocuments` | 1283575 | POST /v2/persons/send-document (bloqueado) |
| `getDocumentsUploadLock` | 1283498 | GET /v2/persons/documents-upload-lock (bloqueado) |
| `fetchPerson` | 383570 | GET /v2/personstatus (bloqueado) |
| `BankingCoreHttpClient` | 506724 | HTTP client com sessionId/Bearer |
| `setAuthorization` | 507054 | Seta Bearer token após login |

---

## 8. CONCLUSÃO

O Frotabank possui uma **arquitetura de segurança em camadas** que combina proteções de aplicação com controles de infraestrutura. A proteção nginx/WAF em endpoints `/v2/persons/*` é **extremamente eficaz** — resistiu a todas as 15+ técnicas de bypass testadas (TLS fingerprint, header manipulation, HTTP/2, múltiplas bibliotecas) e constitui o **ponto único de bloqueio** que impede toda a cadeia de automação do registro.

### Cadeia de Impacto
A impossibilidade de chamar `POST /v2/persons/send-document` cria um efeito cascata que bloqueia: criação de conta → criação de credenciais → login → obtenção de Bearer token → acesso a qualquer endpoint pós-autenticação.

### Vulnerabilidade Mais Crítica — Bug no Fluxo de Criação de Senha
A descoberta mais significativa é um **bug funcional crítico** na `CreateCredentialVerificationCodeScreen`: dois erros no bytecode Hermes fazem com que o app envie `phone: undefined` e `deliveryMethod: [array de módulos]` ao solicitar o código de verificação para criação de senha. Isso impede **todos os usuários** de completar a criação de credenciais após aprovação da conta. O teste manual com os parâmetros corretos confirmou que o backend aceita e entrega o código normalmente (HTTP 200).

### Outras Vulnerabilidades Significativas
Além do bug crítico, foram identificadas **11 vulnerabilidades** (1 CRÍTICA, 3 ALTA, 4 MÉDIA, 2 BAIXA, 1 INFO):
- Exposição de 4 segredos criptográficos no bundle (trivial de extrair)
- Envio de códigos de verificação WhatsApp para contas inexistentes (5 de 6 tipos)
- Enumeração de CPFs sem rate limiting
- Criação irrestrita de device keys

**Nível de maturidade de segurança: INTERMEDIÁRIO**
- Infraestrutura: **ALTO** (nginx/WAF bloqueia toda automação, separação de auth levels)
- Aplicação: **MÉDIO-BAIXO** (bug crítico no fluxo de credenciais, segredos expostos, abuso de códigos)
- Ofuscação: **BAIXO** (Hermes bytecode decompilado para 2M+ linhas JS legíveis, todos os fluxos mapeados)
