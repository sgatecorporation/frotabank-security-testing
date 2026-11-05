# Fluxo Completo Capturado - Frotabank Onboarding

Captura via mitmproxy do fluxo real do app `br.com.frotabank.app` executado no LDPlayer.

Inclui: CPF -> Telefone -> Codigo -> Upload CNH -> Upload Selfie -> Device Key -> POST /user -> Login

**Device/Sessao desta captura:**
- CPF: `91042461015`
- device_id (x-app-finger-print): `30f4a86b945e79c8`
- device_uuid: `81476739-bf8b-401c-9e31-f264cc6c0f3b`
- sessionid: `799ab073-28a3-4ef2-898d-f722bd38fbca`
- privateKey (SafeGuard): `ccb5028159091d24d9ee6d58f4a60d428570194e`
- correlation-id: `28cff8f92e3dd195f3010d875ce47eb3`

---

## Resumo da Autenticacao

### Headers HTTP padrao (todos os requests api.c03)
```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: <device_id - 16 hex>
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
x-correlation-id: <hex 32>
content-type: application/json
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

**IMPORTANTE:**
- `sessionid` (minusculo!) adicionado apos `/phone/confirmation`
- **NAO existe** header `sg-signature` (pinning JWT) - app real nao envia
- **NAO existem** headers `x-device-coords-*`
- `x-app-finger-print` == `deviceId` (nao sao valores diferentes)

### Device Key Signature (x-device-key-signature)

Adicionado em requests APOS a chamada `POST /device_key` ao SafeGuard. Formato:

```
base64( "{sg_api_key}:{device_id}:{device_uuid}:{sha1_canonical}:{hmac_sha256}" )
```

Onde:
- `sg_api_key` = `624ec48b-4ad7-4367-afd9-294a7f7e8c53`
- `sha1_canonical` = SHA1 hex do canonical string
- `hmac_sha256` = HMAC-SHA256(key=privateKey, msg=sha1_hex)

**Canonical string:**
```
METHOD
api.c03.frotabank.com.br
PATH
key=value          <- body params linearizados (nested com dot: addresses.0.city=SP)
key=value          <- headers config (se houver), case-insensitive
```

Linhas unidas por `\n`. Parts com `[]`/`{}` sao linearizadas (traverse recursivo). Boolean -> `true`/`false`. Headers e body sao SORTED alfabeticamente. Headers tem keys em lowercase antes do sort.

### Headers adicionais apos device_key
Requests que usam device key signature tambem incluem:
```
x-device-key-signature: <base64 descrito acima>
x-device-key-user-id: <CPF>
```

### SafeGuard device_key (unico endpoint em id.c03.frotabank.com.br)

Diferentes headers:
```
accept: application/json, text/plain, */*
sg-api-key: 624ec48b-4ad7-4367-afd9-294a7f7e8c53
content-type: application/json;charset=utf-8
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

Body minimo:
```json
{
  "deviceId": "<16 hex>",
  "isRoot": false,
  "userId": "<CPF>",
  "uuid": "<UUID v4>",
  "operatingSystem": "Android"
}
```

Resposta: `{"success":true,"privateKey":"<40 hex>"}`

### Upload de documentos (POST /user/documents/upload)

**Dois formatos diferentes:**

1. **CNH (PDF)**: `content-type: multipart/form-data; boundary=<uuid>` com arquivo binario direto
2. **Selfie**: `content-type: application/json` com body `{"file":{"encrypted":"eyJ...JWT..."}}`
   - JWT HS256 com secret vazio: `{"iss":"unico-sdk-android","capture":{"image":"<base64 da imagem>"}}`

### POST /user (criacao da conta)

Precisa de:
- `sessionid` (de phone/confirmation)
- `x-device-key-signature` + `x-device-key-user-id` (apos SafeGuard)

Body inclui `documents` array (preenchido com URLs dos uploads):
```json
"documents": [
  {"url": "https://...pdf", "documentType": "DIGITAL_DRIVER_LICENSE"},
  {"url": {"base64Url": "...", "encryptedUrl": "..."}, "documentType": "SELFIE"}
]
```

---

## 1. GET /v2/application/versions

**URL completa:** `https://api.c03.frotabank.com.br/v2/application/versions`  
**Status:** `304`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: a079b04c-9474-438e-b81c-427a6637b900
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
if-none-match: W/"4d-dGeHpM46HuMcxMNgTB6FZpEMWH0"
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:24:32 GMT
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"4d-dGeHpM46HuMcxMNgTB6FZpEMWH0"
```

### Response Body

`(empty)`

---

## 2. GET /v2/application/time

**URL completa:** `https://api.c03.frotabank.com.br/v2/application/time`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: a079b04c-9474-438e-b81c-427a6637b900
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:24:32 GMT
content-type: application/json; charset=utf-8
content-length: 34
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
cache-control: no-store
etag: W/"22-bpMY67bvcHuGqLERlO5ufViCVeg"
```

### Response Body (34 chars)

```json
{"now":"2026-10-20T01:24:32.455Z"}
```

---

## 3. POST /v2/credentials/exists

**URL completa:** `https://api.c03.frotabank.com.br/v2/credentials/exists`  
**Status:** `404`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: a079b04c-9474-438e-b81c-427a6637b900
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 26
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (26 chars)

```json
{"document":"91042461015"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:24:44 GMT
content-type: application/json; charset=utf-8
content-length: 80
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"50-0Jnfxznlomb9qu0vBU+aZB9jzKc"
```

### Response Body (80 chars)

```json
{"code":"credentials_not_found","message":"Credentials for this user not found"}
```

---

## 4. GET /v2/whitelist/validate-document/91042461015

**URL completa:** `https://api.c03.frotabank.com.br/v2/whitelist/validate-document/91042461015`  
**Status:** `404`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: a079b04c-9474-438e-b81c-427a6637b900
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
if-none-match: W/"38-tULHWeIAHZMerk5YdJ9CCtAwGS4"
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:24:45 GMT
content-type: application/json; charset=utf-8
content-length: 56
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"38-tULHWeIAHZMerk5YdJ9CCtAwGS4"
```

### Response Body (56 chars)

```json
{"code":"person_not_found","message":"person not found"}
```

---

## 5. POST /v2/verification-code/send

**URL completa:** `https://api.c03.frotabank.com.br/v2/verification-code/send`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: a079b04c-9474-438e-b81c-427a6637b900
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 87
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (87 chars)

```json
{"verificationCodeType":"onboarding","phone":"11984636182","deliveryMethod":"whatsapp"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:24:48 GMT
content-type: application/json; charset=utf-8
content-length: 16
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"10-oV4hJxRVSENxc/wX8+mA4/Pe4tA"
```

### Response Body (16 chars)

```json
{"success":true}
```

---

## 6. POST /phone/confirmation

**URL completa:** `https://api.c03.frotabank.com.br/phone/confirmation`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: a079b04c-9474-438e-b81c-427a6637b900
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 51
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (51 chars)

```json
{"phone":"11984636182","verificationCode":"280410"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:25:00 GMT
content-type: application/json; charset=utf-8
content-length: 67
server: nginx
vary: Origin, Accept-Encoding
access-control-allow-credentials: true
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
etag: W/"43-7p1MWMo+ARMwn8jLE/+8b9I+RTM"
```

### Response Body (67 chars)

```json
{"success":true,"sessionId":"799ab073-28a3-4ef2-898d-f722bd38fbca"}
```

---

## 7. POST /user/cpf-validation

**URL completa:** `https://api.c03.frotabank.com.br/user/cpf-validation`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 21
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (21 chars)

```json
{"cpf":"91042461015"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:25:04 GMT
content-type: application/json; charset=utf-8
content-length: 16
server: nginx
vary: Origin, Accept-Encoding
access-control-allow-credentials: true
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
etag: W/"10-oV4hJxRVSENxc/wX8+mA4/Pe4tA"
```

### Response Body (16 chars)

```json
{"success":true}
```

---

## 8. GET /zipcode/03110010

**URL completa:** `https://api.c03.frotabank.com.br/zipcode/03110010`  
**Status:** `304`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
if-none-match: W/"83-OzN7oTiJQS9k6BzMozqmSlvI2aw"
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:25:10 GMT
server: nginx
vary: Origin
access-control-allow-credentials: true
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
etag: W/"83-OzN7oTiJQS9k6BzMozqmSlvI2aw"
```

### Response Body

`(empty)`

---

## 9. GET /professions

**URL completa:** `https://api.c03.frotabank.com.br/professions`  
**Status:** `304`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
if-none-match: W/"2d29-VnW09J9sWqyriV37BgNWQRCNuCA"
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:25:14 GMT
server: nginx
vary: Origin
access-control-allow-credentials: true
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
etag: W/"2d29-VnW09J9sWqyriV37BgNWQRCNuCA"
```

### Response Body

`(empty)`

---

## 10. GET /v2/terms

**URL completa:** `https://api.c03.frotabank.com.br/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
if-none-match: W/"a0ab-McD0HtCqcbm11Ki+FId+r4rn1No"
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:25:24 GMT
content-type: application/json; charset=utf-8
content-length: 41131
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"a0ab-iAKu8N5mrCX+2o5yKvMaogBEofI"
```

### Response Body (39669 chars)

```json
[{"description":"TERMOS E CONDIÇÕES GERAIS DE USO\n\nDATA DE ÚLTIMA ATUALIZAÇÃO:  25 / 07 / 2025.\n\nINTRODUÇÃO: QUAL A FINALIDADE DESTES TERMOS DE USO?\n\nEstes termos e condições gerais de uso (“Termos de Uso”), juntamente com a Política de Privacidade (“Política de Privacidade”), descrevem os direitos e obrigações dos usuários (“Você” ou “Titular”) ao adquirirem e utilizarem os serviços aqui descritos (“Serviços”).\n\nAO UTILIZAR OS SERVIÇOS OFERECIDOS, VOCÊ AUTOMATICAMENTE CONCORDA COM TODAS AS REGRAS DESTES TERMOS DE USO E DEMAIS CONDIÇÕES AQUI MENCIONADAS, RESPONSABILIZANDO-SE INTEGRALMENTE POR TODOS E QUAISQUER ATOS PRATICADOS AO UTILIZAR NOSSOS SERVIÇOS. CASO VOCÊ NÃO CONCORDE COM QUALQUER DOS TERMOS E CONDIÇÕES ABAIXO ESTABELECIDOS, VOCÊ NÃO DEVE UTILIZAR OS SERVIÇOS.\n\nOs Serviços são oferecidos pela REDE FROTA SOLUTIONS LTDA, pessoa jurídica de direito privado, inscrita no CNPJ sob o nº 24.478.438/0001-48, sediada na Avenida Deputado Jamel Cecílio, 2690, Quadra B-26, Lote 16/17, Loja 02, Edifício Metropolitan Mall, Bairro Jardim Goiás, Goiânia - GO, CEP 74810-100 (“Frotabank”), em parceria com a DOCK INSTITUIÇÃO DE PAGAMENTO S.A., sociedade anônima com sede na Avenida Tamboré, 267, Andar 27 Sala 2 Conj 271-A Edifício Canopus Corporate, Bairro Tamboré, Alphaville, Barueri - SP, CEP 06460-000, inscrita no CNPJ sob o nº 13.370.835/0001-85 (“Parceira”).\n\nQUAIS SÃO AS DEFINIÇÕES IMPORTANTES DESTES TERMOS DE USO?\n\nSem prejuízo de outras definições atribuídas nestes Termos de Uso, as palavras abaixo, quando utilizadas no singular ou plural, terão os seguintes significados:\n\nAplicações: são aplicações de internet como, por exemplo, site ou aplicativo mobile, disponibilizados para que Você possa gerenciar sua Conta, na forma prevista nestes Termos de Uso. \n\nBandeira: é a VISA, instituidora dos arranjos de pagamento VISA, empresa responsável pela marca e pelos sistemas físicos e digitais que permitem a emissão do Cartão e sua utilização nos Estabelecimentos, de acordo com a Lei nº 12.865/2013 e com o Regulamento dos Arranjos de Pagamento da VISA, disponível no site da VISA.\n\nCanais de Comunicação: são os canais oficiais para comunicação entre Você e a Frotabank, para assuntos relacionados ao uso dos Serviços aqui descritos, sendo que qualquer outro canal de comunicação que não esteja descrito aqui, ou nas Aplicações, não é considerado um canal oficial, e Você não deve utilizá-lo. Os Canais de Comunicação são os seguintes:\n\nChat Online. www.fr
...(truncated, 39669 chars total)
```

---

## 11. POST /user/documents/upload

**URL completa:** `https://api.c03.frotabank.com.br/user/documents/upload`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: multipart/form-data; boundary=bc312c60-570c-48ff-b732-c68787d6421f
content-length: 217747
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (217747 chars)

```
[multipart/form-data - binary file - omitted]
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:25:32 GMT
content-type: application/json; charset=utf-8
server: nginx
vary: Origin, Accept-Encoding
access-control-allow-credentials: true
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
etag: W/"685-VqVUVa5uFIYWBPvnerqpy5RlUB4"
content-encoding: gzip
```

### Response Body (1669 chars)

```json
{"url":"https://frota-bank-production-api-documents.s3.amazonaws.com/converted-379b8c3b-e6d4-4301-a908-90b1c8cf5c88-juanpablodavilaboeira.pdf?AWSAccessKeyId=ASIAU2PVAAAVCRTN3CP7&Expires=1792460432&Signature=FwG5yOQvT0OTOweq%2BSBt%2FSB60e0%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEG4aCXVzLWVhc3QtMSJHMEUCIFVWqwsqfIUwxysEebpI270%2F%2BQOWBYTq2UTmG117Yt2vAiEAxv6nEEGPKPl4sWKWRMDOz4QdLRAwsoB43Yoxe%2Bsg%2BzIqvAUINhADGgwzMzE3NjMxNTQ5ODYiDJ0O2fRqvVIV7d79yyqZBaFSDh%2F8Qwu44Wm8pmXRJCQWEl2lk%2F%2FJJTBxROqEdROzo74cfjTdjtVzlXt7vSb0aJvAMuF7Y19ua%2BNuJphs0wuzy4hXZBqa6vf7Y%2Bzwb4nYKVTabO0pgPqYAhT%2FasqBrVl6V5xNXcyJIIWBtBb40bIyMn4Th4%2FhSjDDLXUe1pQEfaKy4Yk5j5nGKneEye3q409MygyAvX%2BcNcCG4nDLYsuvcuqoFmTWp9SnIiQR7hYufEbHTp2u226Ud%2FiyjpU94sbE0y96CfvsWnTh1sG2eSybQ8BCZbXk06uKYQQHsW2OuwoRf7e%2F%2BJayYr0Gw5JG4ssMRggeFBbJ4Lw%2FLhkULS2k47IKBYavOFmqoJCdDo4onCnoegsjqke7sDC42hs7dUm212ESaa%2FDP4KE5Cv6PjFM9v7vLylhWM4k2qS%2B14BHp2a%2B9K9vHBon4V87fXqjv7aKGHox5HvMAHGAwasbcA%2Fm%2BJZGsC9l4qA8FkSeLjA29YvMzLP%2F9b6BlROZH5Yw%2BBQmT9tQMMPuihL0IUbgj1tfZBXyXeJiX4ojjJBEfLZMrsDK%2FpfR5f8mTx8bG6A3tOe%2Fvv3og%2B5aa2gWl%2Fg%2FTjFP7S5n6j2e9pIsdalknak1wfW5ebLD3I0WZ3IHp89jFrO282DJKrK3uzHIKmZFQbLgsyafXuurjp5PclVW0ncnNOVV4KxGPwKKrtypQVf01apz9B4tqD%2Be2VfmDWc3QnKBizhatXervc1HkuO1j6%2BqVkX0jG95VeCOvRWWq0th1qFDSY%2FDn2Utt%2BhupsbovqSZqe881D6THrJff3D838sXw5lu3yfUMXEfmECBoeauy6Y8os48%2BRkgBhnqvOlE6fPH92z9CbJgABIP%2FHNMR%2FAb8Xb4jeSCg4tvMIuN2tYGOrEBSTCIGuvDV2Z5rhzvClhg0%2BYpS%2BLPpGvJOHKRoPN70aopwHY6rttWwsEAAUB6bZSY8C6Hi9eESOHIrj9KVzkfEAmDggjpxf8Ebxnu7GvIT1sI84%2FqbC5X1f7p4vHP2bFHqXxG1xx%2FohlnwV%2FkZZoNe%2BaA3exlPNUUgJSER%2BcOXW3bS9w7bGs3YRYsdwbpcKMBevekCzU4sUywWy3LiXdgnfw5k%2Bdttt9auC%2BsH4qmJEJJ"}
```

---

## 12. POST /user/documents/upload

**URL completa:** `https://api.c03.frotabank.com.br/user/documents/upload`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 767518
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (767518 chars)

```json
{"file":{"encrypted":"eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ1bmljby1zZGstYW5kcm9pZCIsImNhcHR1cmUiOnsiaW1hZ2UiOiIvOWovMndDRUFBRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBUUVCQVFFQkFRRUJBZi9BQUJFSUFvQUI0QU1CSWdBQ0VRRURFUUgveEFHaUFBQUJCUUVCQVFFQkFRQUFBQUFBQUFBQUFRSURCQVVHQndnSkNnc1FBQUlCQXdNQ0JBTUZCUVFFQUFBQmZRRUNBd0FFRVFVU0lURkJCaE5SWVFjaWNSUXlnWkdoQ0NOQ3NjRVZVdEh3SkROaWNvSUpDaFlYR0JrYUpTWW5LQ2txTkRVMk56ZzVPa05FUlVaSFNFbEtVMVJWVmxkWVdWcGpaR1ZtWjJocGFuTjBkWFozZUhsNmc0U0Zob2VJaVlxU2s1U1ZscGVZbVpxaW82U2xwcWVvcWFxeXM3UzF0cmU0dWJyQ3c4VEZ4c2ZJeWNyUzA5VFYxdGZZMmRyaDR1UGs1ZWJuNk9ucThmTHo5UFgyOS9qNStnRUFBd0VCQVFFQkFRRUJBUUFBQUFBQUFBRUNBd1FGQmdjSUNRb0xFUUFDQVFJRUJBTUVCd1VFQkFBQkFuY0FBUUlERVFRRklURUdFa0ZSQjJGeEV5SXlnUWdVUXBHaHNjRUpJek5TOEJWaWN0RUtGaVEwNFNYeEZ4Z1pHaVluS0NrcU5UWTNPRGs2UTBSRlJrZElTVXBUVkZWV1YxaFpXbU5rWldabmFHbHFjM1IxZG5kNGVYcUNnNFNGaG9lSWlZcVNrNVNWbHBlWW1acWlvNlNscHFlb3FhcXlzN1MxdHJlNHVickN3OFRGeHNmSXljclMwOVRWMXRmWTJkcmk0K1RsNXVmbzZlcnk4L1QxOXZmNCtmci8yZ0FNQXdFQUFoRURFUUEvQVA3RC9GL3dNK0FseHFuZ1N6LzRVejhLL3Nlc1hkNnMwYStBZkNwdElSRzBWazFwZFdrZWpUVzh5eCtXeXhwTXJoWkxTUVJDTUxzTGRiL1pDL1pEbDhTWHIzSDdMSDdPZDFhYWRCWlNhMWMzSHdSK0YxeVk3ZTZoaThxMWxNbmhmOTdjWE10aW9qU1NSMUVseXpCUWtqdXZwZHBhUTJIai9XTk1qVHpMU2FDNjhiNkRGdUx5NmRxMGNsMU5OYUpLWFpoYVR6U1MzeTJ4UlZFdHcwU3RzMlJMNkJxbWo2YnE5NXFlbnpmYUV0ZkZVM2hyVWIyU0dkcmFRMkdueS9iTFo0WkkyM2d2ZndyYjNvSUVSdG5DTXUyV1N2Rjl2VzVvODFXcGU2dW5PVm03TnBOdDJzOXI2V2U0bFRnbGJrajFleWU5a2trdHJhYWVydDBQbjJ4L1lnL1lyZTRqMGZVUDJRdjJZOVF2RGVYVFg3WGY3UDhBOEpiaTNpV1cwajFPT3d0cEg4S1RNTGV6aHVZTFZVazJpU09TNkNibzVKQU9RMDc5aFA4QVlkalpvN245amY4QVpRbWwxVklicExtVDlucjRPcytrM2tWcGNUaXh1akw0UWZZYnhMZU9GZ1dLekFOdlFTc1RYMk5KZUNMeEJydW5XMForMHZiV2R3WkE0amlGdkxZUzJ0bkxia3FvRXp6RjB1WnQ0WXh3S2lzQUZVYzNwRmpQTFo2aWx6YlhVdHhkNjBGbkxHT1VnM0N5RzJjeHNvUGw2ZXNhU0lGUGxlWWNJV1ZDUXBUbkozYm01UlZyS1h1MnZiZDZYU1Q5N3ZycHVUWjgxbHV0YnQyc21sNlh2cmRKYTMwNm56VGYvc0cvc1JKQkRZSDlqLzhBWmNzb2ZGT3B0S2w5cGZ3QStGTmhmMnVtM05vTCtPMXRIdFBDQ3l3dW8wOXJTUWhncnBjTkdoTFhUZ01sL1lyL0FHSE5QMWhMTFIvMkxmMldmN1dXVVdkbDlnL1oyK0U2TXRyY1IyRnRiYW5yR294ZUVBSTR2Tm1rdWtlY3RkUytXd0c1aW5tZlcydVFYRnhxR2dyWnRGTkpwTWRwUGNxaFlRaEdFMXVKYmR5UWlOYVhBaUx0a004VXJCdHFvMGJSc2ROMCsvdjlMaFM5azFLVFIzOFN4WkQyOXNiUm5ld2hWcmd4bEpMZ1hNMjJTMjh4cElsdE5QWXhKRXlFd2sxT28wblpKSjNkM2RwTzEwck5idmJ6ZWhiYjkyemQxMTB0YXo2ZmN1K2w3MzFYek40Ny9ZUC9BR0lkWjhNYWh2OEEyT2YyV2J1N3RrZ3RWZjhBNFo3K
...(truncated, 767518 chars total)
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:30:32 GMT
content-type: application/json; charset=utf-8
server: nginx
vary: Origin, Accept-Encoding
access-control-allow-credentials: true
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
etag: W/"cd1-8wPIGNcaJ0wjGd2j6OX6PGu+jtA"
content-encoding: gzip
```

### Response Body (3281 chars)

```json
{"url":{"base64Url":"https://frota-bank-production-api-documents.s3.amazonaws.com/37e09f72-99ca-47b8-8bde-02fbc3be89fb-optmized-image.jpg?AWSAccessKeyId=ASIAU2PVAAAVKGKOTGT4&Expires=1792460732&Signature=bTUAHkgu%2BKIFprFcL0ytpiSD1%2FA%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEHAaCXVzLWVhc3QtMSJIMEYCIQC%2FcIlDf11pSI1mytW5fSfAGWLNKMhwHiL8NfRM6FdixwIhAIa0txA%2BLYLIj%2FqghUEgdAxLaD2Bx0o7FbUdib5%2BpjhTKrsFCDkQAxoMMzMxNzYzMTU0OTg2Igz2CwGExOSDbj5g7ncqmAWxieTs%2F9oGI6IUme09axizLxzlxkcGl64hF5fy39AJozssc4Zt4Q6idc11JMlIrTrfkjIDhipmWOJAV1H8o%2FjyAItf3AyzZesesMUM9Xu%2B74NOXyqCK0o8wujsl9U56gTujqk6wcMIfP2FfRdtlRVvd0jHYtKHZwfIgXgqBszfPnjQdfnmVrZ6n28rr0nABUBeuPPOgqHWdOgsA2h1KHcqDyaafj7Ab4NxLIzM17iIL9brt4N5FMGA3Dcpjk5Fkx40nIzaXgATf2qWq0DkNSfjGOdTCWKws6NxfkbEVcKladLhebIDx89HeJiYg%2F10%2FQYHRpKCwDiiyykCIBMV9b7tbPBkau2HWWNmveo14V4iznYWjFeyqkj%2BXHAuQY95bzFgkjwO8ZabvCG1u9OekM%2BqTM0rA4ZyMXwQEVVhB%2F7b0UqwpAN7i4jJzzNhKAhMKQu5ww%2BxiydlBwInQigo1grSyVcSxR0CKsYV11lEZ1AEfeZNUSu0%2BabxFghV6xXGaTd2McegEaETy1YoUkMDMrSme9WaVDLL%2B9V4H00%2FPiy%2Fo0A0Vo4cUFQkN5qAQhf7g%2BQr6R5RS9cnL3zgKkAlxgo2X4aat4fXsC8yrn%2F7GNhYLG3Uky%2B8rDkRFQmbAs1R3ha1Z13fc8h3Wyxvy72WVQubv4isctumQsde2TDAyCRNsNllTtjpbGSUHn%2FaruUUxd99QHq2uyvHahOXQ%2FRTTccnstClFJSYXW4o2hvES0QSNJRm05zzKilX00ZcGiITE1cMfoPHn4XIaCTgPZpOOLDzNrLU%2Fy%2FogbiMBFbnIrvuG4MiE29G04zMjlIptO51gAHyXTjZFqffzVLilsun%2F7nFWawXhoogUmELkndoQ5mjWjVHFDROazSrMMHd2tYGOrABUoWiqto8Sc8UO4pUblV%2B9AQnb9RbVt7uAN99%2B5Qk959dq%2B%2BBCKtdEQQfDJSQXpJLGQvrV5JCYg%2F7XS02aaTJzzANGg%2B8BUIdmck8FsSRZzLwnN5C5V9xA3z4swBoayi4Ob19tn9YgbRaSoV4hP7PFjWRwoPWJdtSka2RvjEJnYCQu0uXNvTrbBm6aCKo9v%2F3pSGKdw4UkUXDk%2FpbeKSkWMJHXTanGiWGmCQKNBm1LGg%3D","encryptedUrl":"https://frota-bank-production-api-documents.s3.amazonaws.com/37e09f72-99ca-47b8-8bde-02fbc3be89fb-encrypted.enc?AWSAccessKeyId=ASIAU2PVAAAVKGKOTGT4&Expires=1792460732&Signature=7kER5hbJOj3kdT9L2U0ii4%2B%2BBXs%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEHAaCXVzLWVhc3QtMSJIMEYCIQC%2FcIlDf11pSI1mytW5fSfAGWLNKMhwHiL8NfRM6FdixwIhAIa0txA%2BLYLIj%2FqghUEgdAxLaD2Bx0o7FbUdib5%2BpjhTKrsFCDkQAxoMMzMxNzYzMTU0OTg2Igz2CwGExOSDbj5g7ncqmAWxieTs%2F9oGI6IUme09axizLxzlxkcGl64hF5fy39AJozssc4Zt4Q6idc11JMlIrTrfkjIDhipmWOJAV1H8o%2FjyAItf3AyzZesesMUM9Xu%2B74NOXyqCK0o8wujsl9U56gTujqk6wcMIfP2FfRdtlRVvd0jHYtKHZwfIgXgqBszfPnjQdfnmVrZ6n28rr0nABUBeuPPOgqHWdOgsA2h1KHcqDyaafj7Ab4NxLIzM17iIL9brt4N5FMGA3Dcpjk5Fkx40nIzaXgATf2qWq0DkNSfjGOdTCWKws6NxfkbEVcKladLhebIDx89HeJiYg%2F10%2FQYHRpKCwDiiyykCIBMV9b7tbPBkau2HWWNmveo14V4iznYWjFeyqkj%2BXHAuQY95bzFgkjwO8ZabvCG1u9OekM
...(truncated, 3281 chars total)
```

---

## 13. POST /device_key

**URL completa:** `https://id.c03.frotabank.com.br/device_key`  
**Status:** `200`  
**Host:** `id.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
sg-api-key: 624ec48b-4ad7-4367-afd9-294a7f7e8c53
content-type: application/json;charset=utf-8
content-length: 143
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (143 chars)

```json
{"deviceId":"30f4a86b945e79c8","isRoot":false,"userId":"91042461015","uuid":"81476739-bf8b-401c-9e31-f264cc6c0f3b","operatingSystem":"Android"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:30:35 GMT
content-type: application/json; charset=utf-8
content-length: 72
x-amzn-requestid: 236a3cbb-7b1a-4afb-a4be-b544c71c56e5
referrer-policy: no-referrer
x-dns-prefetch-control: off
x-permitted-cross-domain-policies: none
x-xss-protection: 0
expect-ct: max-age=0
strict-transport-security: max-age=15552000; includeSubDomains
x-frame-options: SAMEORIGIN
x-amzn-remapped-content-length: 72
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-download-options: noopen
x-amz-apigw-id: FhOZUGJZoAMELMA=
x-content-type-options: nosniff
etag: W/"48-ESgJfJuskRlqSrad8dB9lgCRC64"
x-amzn-trace-id: Root=1-6ad6c43b-365a8a974f43fa1646e41011;Parent=7a54089a5f78810c;Sampled=0;Lineage=1:9f85c4f5:0
```

### Response Body (72 chars)

```json
{"success":true,"privateKey":"ccb5028159091d24d9ee6d58f4a60d428570194e"}
```

---

## 14. POST /user

**URL completa:** `https://api.c03.frotabank.com.br/user`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-device-key-signature: NjI0ZWM0OGItNGFkNy00MzY3LWFmZDktMjk0YTdmN2U4YzUzOjMwZjRhODZiOTQ1ZTc5Yzg6ODE0NzY3MzktYmY4Yi00MDFjLTllMzEtZjI2NGNjNmMwZjNiOjJkMTlhYTEwOThhODY5NDRjOGU2MTcxZTY1MTkwMGQ3NGViZmI0YWE6MzMzYjU5MGIwNzRmZjJmODM3ODY2OGQ3M2Q3YTMxMThjMzNhNzY5ZmVlNDRhOGE1NGJkOGIwZmM4ZDJkMzE5NA==
x-device-key-user-id: 91042461015
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 5827
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (5826 chars)

```json
{"addresses":[{"zipCode":"03110010","state":"SP","city":"São Paulo","complement":"","street":"Rua Borges de Figueiredo","number":"303","neighborhood":"Mooca"}],"birthday":"1978-03-04T03:00:00.000Z","documentNumber":"91042461015","documents":[{"url":"https://frota-bank-production-api-documents.s3.amazonaws.com/converted-379b8c3b-e6d4-4301-a908-90b1c8cf5c88-juanpablodavilaboeira.pdf?AWSAccessKeyId=ASIAU2PVAAAVCRTN3CP7&Expires=1792460432&Signature=FwG5yOQvT0OTOweq%2BSBt%2FSB60e0%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEG4aCXVzLWVhc3QtMSJHMEUCIFVWqwsqfIUwxysEebpI270%2F%2BQOWBYTq2UTmG117Yt2vAiEAxv6nEEGPKPl4sWKWRMDOz4QdLRAwsoB43Yoxe%2Bsg%2BzIqvAUINhADGgwzMzE3NjMxNTQ5ODYiDJ0O2fRqvVIV7d79yyqZBaFSDh%2F8Qwu44Wm8pmXRJCQWEl2lk%2F%2FJJTBxROqEdROzo74cfjTdjtVzlXt7vSb0aJvAMuF7Y19ua%2BNuJphs0wuzy4hXZBqa6vf7Y%2Bzwb4nYKVTabO0pgPqYAhT%2FasqBrVl6V5xNXcyJIIWBtBb40bIyMn4Th4%2FhSjDDLXUe1pQEfaKy4Yk5j5nGKneEye3q409MygyAvX%2BcNcCG4nDLYsuvcuqoFmTWp9SnIiQR7hYufEbHTp2u226Ud%2FiyjpU94sbE0y96CfvsWnTh1sG2eSybQ8BCZbXk06uKYQQHsW2OuwoRf7e%2F%2BJayYr0Gw5JG4ssMRggeFBbJ4Lw%2FLhkULS2k47IKBYavOFmqoJCdDo4onCnoegsjqke7sDC42hs7dUm212ESaa%2FDP4KE5Cv6PjFM9v7vLylhWM4k2qS%2B14BHp2a%2B9K9vHBon4V87fXqjv7aKGHox5HvMAHGAwasbcA%2Fm%2BJZGsC9l4qA8FkSeLjA29YvMzLP%2F9b6BlROZH5Yw%2BBQmT9tQMMPuihL0IUbgj1tfZBXyXeJiX4ojjJBEfLZMrsDK%2FpfR5f8mTx8bG6A3tOe%2Fvv3og%2B5aa2gWl%2Fg%2FTjFP7S5n6j2e9pIsdalknak1wfW5ebLD3I0WZ3IHp89jFrO282DJKrK3uzHIKmZFQbLgsyafXuurjp5PclVW0ncnNOVV4KxGPwKKrtypQVf01apz9B4tqD%2Be2VfmDWc3QnKBizhatXervc1HkuO1j6%2BqVkX0jG95VeCOvRWWq0th1qFDSY%2FDn2Utt%2BhupsbovqSZqe881D6THrJff3D838sXw5lu3yfUMXEfmECBoeauy6Y8os48%2BRkgBhnqvOlE6fPH92z9CbJgABIP%2FHNMR%2FAb8Xb4jeSCg4tvMIuN2tYGOrEBSTCIGuvDV2Z5rhzvClhg0%2BYpS%2BLPpGvJOHKRoPN70aopwHY6rttWwsEAAUB6bZSY8C6Hi9eESOHIrj9KVzkfEAmDggjpxf8Ebxnu7GvIT1sI84%2FqbC5X1f7p4vHP2bFHqXxG1xx%2FohlnwV%2FkZZoNe%2BaA3exlPNUUgJSER%2BcOXW3bS9w7bGs3YRYsdwbpcKMBevekCzU4sUywWy3LiXdgnfw5k%2Bdttt9auC%2BsH4qmJEJJ","documentType":"DIGITAL_DRIVER_LICENSE"},{"url":{"base64Url":"https://frota-bank-production-api-documents.s3.amazonaws.com/37e09f72-99ca-47b8-8bde-02fbc3be89fb-optmized-image.jpg?AWSAccessKeyId=ASIAU2PVAAAVKGKOTGT4&Expires=1792460732&Signature=bTUAHkgu%2BKIFprFcL0ytpiSD1%2FA%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEHAaCXVzLWVhc3QtMSJIMEYCIQC%2FcIlDf11pSI1mytW5fSfAGWLNKMhwHiL8NfRM6FdixwIhAIa0txA%2BLYLIj%2FqghUEgdAxLaD2Bx0o7FbUdib5%2BpjhTKrsFCDkQAxoMMzMxNzYzMTU0OTg2Igz2CwGExOSDbj5g7ncqmAWxieTs%2F9oGI6IUme09axizLxzlxkcGl64hF5fy39AJozssc4Zt4Q6idc11JMlIrTrfkjIDhipmWOJAV1H8o%2FjyAItf3AyzZ
...(truncated, 5826 chars total)
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:30:54 GMT
content-type: application/json; charset=utf-8
server: nginx
vary: Origin, Accept-Encoding
access-control-allow-credentials: true
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
etag: W/"f9d-Ou07lpli5yop98z4bZQZwHCCe6w"
content-encoding: gzip
```

### Response Body (3995 chars)

```json
{"id":130057,"phone":"11984636182","email":"juanpablodavilaboeira78@gmail.com","documentNumber":"91042461015","name":"Juan Pablo Davila Boeira","birthday":"1978-03-04T03:00:00.000Z","motherName":"Vercy Maria Falavigna Boeira","fantasyName":null,"type":"person","createdAt":"2026-10-20T01:30:36.138Z","updatedAt":"2026-10-20T01:30:36.138Z","conductorIndividualId":null,"conductorAccountId":null,"createdConductorCard":false,"createdConductorAppUser":false,"conductorCreationErrorMessage":null,"conductorCreationErrorStatusCode":null,"status":"pending_validation","newsletterAccept":true,"password":null,"legalNature":null,"isPEP":false,"rg":"9049061683","rgIssuingEntity":null,"rgIssuingState":null,"rgIssuingDate":"2021-09-08T03:00:00.000Z","monthlyIncome":"4000.00","professionId":1,"conductorRegistrationId":null,"accountNumber":null,"accountBank":null,"accountAgency":null,"accountAgencyDigit":null,"accountDigit":null,"aliasBankCreationStatusCode":null,"aliasBankCreationMessage":null,"aliasBankCreated":false,"createdConductorVirtualCard":false,"cnae":null,"companyStatus":null,"stateInscription":null,"establishmentFormat":null,"annualRevenue":null,"walletTermsAcceptedAt":null,"firstCardAddedToWalletAt":null,"transactionsPassword":null,"transactionsPasswordIncorrectAttemptsCount":0,"commonsSync":false,"addresses":[{"id":168340,"userId":130057,"street":"Rua Borges de Figueiredo","number":"303","complement":"","city":"São Paulo","state":"SP","createdAt":"2026-10-20T01:30:36.146Z","updatedAt":"2026-10-20T01:30:36.146Z","zipCode":"03110010","neighborhood":"Mooca","country":"Brasil"}],"terms":[{"id":335429,"userId":130057,"type":"PRIVACY_POLICY","token":"a6185102-96ce-4ef5-9879-553ce4229e83","createdAt":"2026-10-20T01:30:36.146Z","updatedAt":"2026-10-20T01:30:36.146Z"},{"id":335428,"userId":130057,"type":"TERMS_OF_USE","token":"8ae63b21-8e31-4ec8-8f2b-978b828cb1b3","createdAt":"2026-10-20T01:30:36.146Z","updatedAt":"2026-10-20T01:30:36.146Z"}],"documents":[{"id":489850,"userId":130057,"url":"{\"base64Url\":\"https://frota-bank-production-api-documents.s3.amazonaws.com/37e09f72-99ca-47b8-8bde-02fbc3be89fb-optmized-image.jpg\",\"encryptedUrl\":\"https://frota-bank-production-api-documents.s3.amazonaws.com/37e09f72-99ca-47b8-8bde-02fbc3be89fb-encrypted.enc\"}","createdAt":"2026-10-20T01:30:36.146Z","updatedAt":"2026-10-20T01:30:36.146Z","documentType":"SELFIE"},{"id":489849,"userId":130057,"url":"https://frota-bank-production-api-documents.s3.amazonaws.com/converted-379b8c3b-
...(truncated, 3995 chars total)
```

---

## 15. GET /v2/whitelist/validate-document/91042461015

**URL completa:** `https://api.c03.frotabank.com.br/v2/whitelist/validate-document/91042461015`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-device-key-signature: NjI0ZWM0OGItNGFkNy00MzY3LWFmZDktMjk0YTdmN2U4YzUzOjMwZjRhODZiOTQ1ZTc5Yzg6ODE0NzY3MzktYmY4Yi00MDFjLTllMzEtZjI2NGNjNmMwZjNiOmMyNDUwN2QxN2JkZmJhZGYzNDEwOTQ2MTBkYzg5MjEyMTg1YmEyNTk6NjM5OWFiN2FkNTFkYjQ4MTA4ZTVkNmRkZTExMWYxMjUyYzlhNzE2MTc1ZjdmY2JiMzMzYTZiNDcxMGY4YjIxYw==
x-device-key-user-id: 91042461015
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
if-none-match: W/"38-tULHWeIAHZMerk5YdJ9CCtAwGS4"
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:31:42 GMT
content-length: 0
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
```

### Response Body

`(empty)`

---

## 16. POST /v2/credentials/exists

**URL completa:** `https://api.c03.frotabank.com.br/v2/credentials/exists`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-device-key-signature: NjI0ZWM0OGItNGFkNy00MzY3LWFmZDktMjk0YTdmN2U4YzUzOjMwZjRhODZiOTQ1ZTc5Yzg6ODE0NzY3MzktYmY4Yi00MDFjLTllMzEtZjI2NGNjNmMwZjNiOjdlMzA3MjY4MGNhMDc4MmY1NDdhNDIxNzRkNTU3NWE0ZmE3NzZlMDc6NjA2ZWUwOTQyYzQyMWQxYjdlZjM5YmUzZTIxMTZhOGYwMTM4ZTE5NjhiYTk1ZjU4OGQwMGQ2YmU0MjUzM2IxMw==
x-device-key-user-id: 91042461015
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 26
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (26 chars)

```json
{"document":"91042461015"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:31:39 GMT
content-type: application/json; charset=utf-8
content-length: 16
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"10-oV4hJxRVSENxc/wX8+mA4/Pe4tA"
```

### Response Body (16 chars)

```json
{"success":true}
```

---

## 17. GET /device_key/status

**URL completa:** `https://id.c03.frotabank.com.br/device_key/status?uuid=81476739-bf8b-401c-9e31-f264cc6c0f3b&deviceId=30f4a86b945e79c8`  
**Status:** `200`  
**Host:** `id.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
sg-api-key: 624ec48b-4ad7-4367-afd9-294a7f7e8c53
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:31:43 GMT
content-type: application/json; charset=utf-8
content-length: 37
x-amzn-requestid: e2a4268a-3347-4e07-978e-287eec4443e0
referrer-policy: no-referrer
x-dns-prefetch-control: off
x-permitted-cross-domain-policies: none
x-xss-protection: 0
expect-ct: max-age=0
strict-transport-security: max-age=15552000; includeSubDomains
x-frame-options: SAMEORIGIN
x-amzn-remapped-content-length: 37
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-download-options: noopen
x-amz-apigw-id: FhOkAHuUIAMEotA=
x-content-type-options: nosniff
etag: W/"25-Lw9xuajt3qyx8qc4uZpO2RnN/fk"
x-amzn-trace-id: Root=1-6ad6c47f-6ef43540434e528f33c930ed;Parent=67a8f9f7761845e3;Sampled=0;Lineage=1:9f85c4f5:0
```

### Response Body (37 chars)

```json
{"success":true,"status":"validated"}
```

---

## 18. POST /v2/onboarding/status

**URL completa:** `https://api.c03.frotabank.com.br/v2/onboarding/status`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-device-key-signature: NjI0ZWM0OGItNGFkNy00MzY3LWFmZDktMjk0YTdmN2U4YzUzOjMwZjRhODZiOTQ1ZTc5Yzg6ODE0NzY3MzktYmY4Yi00MDFjLTllMzEtZjI2NGNjNmMwZjNiOjQwMTA3MmQyMjMzOTAwNjk4ZGQ3MGFhNGE0MGY3NzE1MmZhMWUyYTk6ZWZiMTkxZGU4MjBkYjQxOWJjMGNhMTE1NjUxMzU3OTk4OTE1ZTU4ZTg0MTkwODk5YTRlZmIyYjA4MmFiNDcwOQ==
x-device-key-user-id: 91042461015
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 26
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (26 chars)

```json
{"document":"91042461015"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:31:48 GMT
content-type: application/json; charset=utf-8
content-length: 31
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"1f-RnjrVmO8ACdzhvCwuaLH2OQt/1k"
```

### Response Body (31 chars)

```json
{"status":"pending_validation"}
```

---

## 19. POST /v2/auth/login

**URL completa:** `https://api.c03.frotabank.com.br/v2/auth/login`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
x-device-key-signature: NjI0ZWM0OGItNGFkNy00MzY3LWFmZDktMjk0YTdmN2U4YzUzOjMwZjRhODZiOTQ1ZTc5Yzg6ODE0NzY3MzktYmY4Yi00MDFjLTllMzEtZjI2NGNjNmMwZjNiOjE2YjdmYjRhOTQxYzJiNGIxNTlhNjY0YzhjZjExNjVlNWU4MzYwMzE6YjRhOThmOGI3MjQ1ZmNkOTE0NjkxODNhOGU0MjQzZWFiZDIyYTRmNjIwYzMzNGVkMDE5ODAzMTNmYTY2NjljYw==
x-device-key-user-id: 91042461015
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
content-type: application/json
content-length: 50
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body (50 chars)

```json
{"document":"91042461015","password":"Senh@2024!"}
```

### Response Headers

```
date: Tue, 20 Oct 2026 01:31:49 GMT
content-type: application/json; charset=utf-8
content-length: 993
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"3e1-OhuGv+rf1FAzjrgVGTNJ7hoDoVk"
```

### Response Body (993 chars)

```json
{"token":"eyJhbGciOiJSUzI1NiIsImtpZCI6IjkwNGIwZjkxYmU2ZWIwODY3ZGFiYmFhYjU4N2RmYzJlMzNmMDBhMjQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFua2luZy1mcm90YWJhbmsiLCJhdWQiOiJiYW5raW5nLWZyb3RhYmFuayIsImF1dGhfdGltZSI6MTc5MjQ1OTkwOSwidXNlcl9pZCI6ImZVZk9pTG9kSFNiaEtWUWNtZjlSYWJ6cmRuNjMiLCJzdWIiOiJmVWZPaUxvZEhTYmhLVlFjbWY5UmFienJkbjYzIiwiaWF0IjoxNzkyNDU5OTA5LCJleHAiOjE3OTI0NjM1MDksImVtYWlsIjoiOTEwNDI0NjEwMTUrZnJvdGFiYW5rcHJvZEB2aXppcmJhbmsuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsiOTEwNDI0NjEwMTUrZnJvdGFiYW5rcHJvZEB2aXppcmJhbmsuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.C6fPcGQ5VSDBjIOt9Ktwefmr7xEfIplHfC7wpWU3QJtCKy03qZB20JkLjhKtQ2UlRy383AkjTyNfizu-FBmzOx13r6hS4aOQBWYWxd723KF5Ka5gTuIPbFb7U6XTT4iBlqYZ3QY5w3P2gAxmignKpGvV_znqJXN1rAnhSZ1_xN3A4mn3F0KZf_NliW3a_RGLXK3b0VI_Y85pzrmYUZga4EgGioUOsczuJCfsbgERTDCCs-QE0Zdr6kUzplx4B7H6uF7lxZvqX3JO-8hN1wsDJfEoPJzD-EVqsQTCEE4Jlc2GCY6efsMfGbkF2ahEi2zDha5lvWdmvH6I3yexRlul3w"}
```

---

## 20. GET /v2/accountstatus/91042461015

**URL completa:** `https://api.c03.frotabank.com.br/v2/accountstatus/91042461015`  
**Status:** `200`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjkwNGIwZjkxYmU2ZWIwODY3ZGFiYmFhYjU4N2RmYzJlMzNmMDBhMjQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFua2luZy1mcm90YWJhbmsiLCJhdWQiOiJiYW...(truncated 988 chars)
x-device-key-signature: NjI0ZWM0OGItNGFkNy00MzY3LWFmZDktMjk0YTdmN2U4YzUzOjMwZjRhODZiOTQ1ZTc5Yzg6ODE0NzY3MzktYmY4Yi00MDFjLTllMzEtZjI2NGNjNmMwZjNiOjFhMjc2NmZmZjhmOTJjZjY4ZDJhZjM1OTg5YTkwMmYxMGM2NjQ1Mzg6OWI2NWFhMTU5OWExY2E2ZWJhNDBmZTI4MjliMzg1Nzk3ZTdkYTk0YzM2MjcwZmRlY2Q1N2QzNGQ4ZjM0NWJkOA==
x-device-key-user-id: 91042461015
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:31:53 GMT
content-type: application/json; charset=utf-8
content-length: 15
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"f-VaSQ4oDUiZblZNAEkkN+sX+q3Sg"
```

### Response Body (15 chars)

```json
{"status":"ok"}
```

---

## 21. GET /v2/personstatus

**URL completa:** `https://api.c03.frotabank.com.br/v2/personstatus`  
**Status:** `404`  
**Host:** `api.c03.frotabank.com.br`

### Request Headers

```
accept: application/json, text/plain, */*
x-app-name: br.com.frotabank.app
x-app-platform: android
x-app-finger-print: 30f4a86b945e79c8
x-app-build-number: 2026012801
x-app-version: 18.10.18
x-app-device-model: ROG / ROG Phone 7 Ultimate / star2qltechn / qcom
sessionid: 799ab073-28a3-4ef2-898d-f722bd38fbca
authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjkwNGIwZjkxYmU2ZWIwODY3ZGFiYmFhYjU4N2RmYzJlMzNmMDBhMjQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vYmFua2luZy1mcm90YWJhbmsiLCJhdWQiOiJiYW...(truncated 988 chars)
x-device-key-signature: NjI0ZWM0OGItNGFkNy00MzY3LWFmZDktMjk0YTdmN2U4YzUzOjMwZjRhODZiOTQ1ZTc5Yzg6ODE0NzY3MzktYmY4Yi00MDFjLTllMzEtZjI2NGNjNmMwZjNiOjU3ZTJiMTNiOTJkMDFmMDdlN2MxN2QzZmM0YzZmYThhMDk0MmFjZTM6NjBlY2QzMjEzMDU4MzhkOTQwYWIyZTM5ZWI3NjA0YmE0OWNhZmJjODhlMGQzODNiYmU2NmYyNGUxZTJlMWI5OQ==
x-device-key-user-id: 91042461015
x-correlation-id: 28cff8f92e3dd195f3010d875ce47eb3
accept-encoding: gzip
user-agent: okhttp/4.11.0
```

### Request Body

`(empty)`

### Response Headers

```
date: Tue, 20 Oct 2026 01:31:55 GMT
content-type: application/json; charset=utf-8
content-length: 73
server: nginx
content-security-policy: default-src 'self';base-uri 'self';block-all-mixed-content;font-src 'self' https: data:;frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests
x-dns-prefetch-control: off
expect-ct: max-age=0
x-frame-options: SAMEORIGIN
strict-transport-security: max-age=15552000; includeSubDomains
x-download-options: noopen
x-content-type-options: nosniff
x-permitted-cross-domain-policies: none
referrer-policy: no-referrer
x-xss-protection: 0
vary: Origin
access-control-allow-credentials: true
etag: W/"49-HLpXt+mD1GqLwq4vVRSczSZ/TiA"
```

### Response Body (73 chars)

```json
{"name":"NotFoundError","message":"Not found Person for current session"}
```

---


**Total de requests documentados:** 21
