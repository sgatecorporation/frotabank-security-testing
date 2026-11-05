# Template: Fluxo Completo Frotabank

## INFORMAÇÕES DA SESSÃO
- **Data/Hora**: YYYY-MM-DD HH:MM:SS
- **Dispositivo**: (Emulador/Celular físico)
- **Arquitetura**: ARM64 / ARM32
- **Android Version**: Android X.X
- **App Version**: 1.X.X
- **Frida Version**: 16.0.x
- **Charles Version**: 4.6.x

## CONTA TESTE
- **CPF**: XXX.XXX.XXX-XX
- **Email**: test@example.com
- **Senha**: [REDACTED]
- **Telefone**: +55 XX 99999-XXXX

## FLUXO: [NOME DO FLUXO]
Exemplo: "Cadastro Completo com Biometria"

### 1. LOGIN/CRIAÇÃO DE CONTA

#### Requisição: POST /auth/register
```
URL: https://banking-frotabank-xxxxx.firebaseio.com/auth/register
Método: POST
Headers:
  - Content-Type: application/json
  - Authorization: Bearer [TOKEN]
  - User-Agent: Dalvik/2.1.0

Body:
{
  "email": "test@example.com",
  "password": "[HASH]",
  "cpf": "12345678901",
  "nome": "Test User",
  "telefone": "+5511999999999"
}

Response:
{
  "uid": "firebase_uid_xxx",
  "idToken": "eyJhbGciOiJSUzI1NiIs...",
  "status": "success"
}
```

**Análise**:
- ✅ Status 200 OK
- ⚠️ Token retornado sem validação
- 🔍 Sem MFA obrigatório

### 2. ENVIO DE SMS

#### Requisição: POST /auth/send-sms
```
URL: https://banking-frotabank-xxxxx.firebaseio.com/auth/send-sms
Método: POST
Body:
{
  "telefone": "+5511999999999",
  "uid": "firebase_uid_xxx"
}

Response:
{
  "sms_sent": true,
  "code_length": 6,
  "attempts_left": 3
}
```

**Análise**:
- ⚠️ Código enviado sem criptografia
- 🔴 Apenas 3 tentativas (brute-force possível)
- 🔍 Sem rate limiting visível

#### SMS Recebido
```
[Frotabank] Seu código: 123456
Válido por 10 minutos
```

### 3. VALIDAÇÃO DE SMS

#### Requisição: POST /auth/verify-sms
```
URL: https://banking-frotabank-xxxxx.firebaseio.com/auth/verify-sms
Método: POST
Body:
{
  "uid": "firebase_uid_xxx",
  "code": "123456"
}

Response:
{
  "verified": true,
  "token": "sms_verification_token_xxx"
}
```

**Análise**:
- ✅ Código validado
- ⚠️ Sem HTTPS pinning visível
- 🔍 Token de verificação pode ser reutilizado

### 4. CAPTURA BIOMETRIA

#### Requisição: POST /biometria/capture
```
URL: https://banking-frotabank-xxxxx.firebaseio.com/biometria/capture
Método: POST
Headers:
  - Authorization: Bearer [BIOMETRIA_TOKEN]
  
Body:
{
  "uid": "firebase_uid_xxx",
  "image_base64": "[LONG_BASE64_IMAGE]",
  "timestamp": 1697299200000,
  "device_id": "android_device_id_xxx"
}

Response:
{
  "liveness_score": 0.95,
  "face_detected": true,
  "approved": true,
  "message": "Biometria validada com sucesso"
}
```

**Análise**:
- 🔴 Score fixo em 0.95 (anormalmente alto)
- ⚠️ Sem detecção de deepfake
- 🔍 Sem validação de movimento em tempo real

### 5. VALIDAÇÃO DE DOCUMENTOS

#### Requisição: POST /documentos/upload
```
URL: https://banking-frotabank-xxxxx.firebaseio.com/documentos/upload
Método: POST
Body:
{
  "uid": "firebase_uid_xxx",
  "tipo": "RG",
  "front_base64": "[BASE64]",
  "back_base64": "[BASE64]",
  "selfie_base64": "[BASE64]"
}

Response:
{
  "rg_number": "12345678",
  "name_match": 0.92,
  "document_verified": true,
  "selfie_match": 0.89
}
```

**Análise**:
- ⚠️ Scores de matching aceitos sem validação humana
- 🔴 Documentos antigos não rejeitados
- 🔍 Sem detecção de edição de imagem

### 6. CRIAÇÃO DE CONTA NO FIREBASE

#### Requisição: PUT /users/{uid}
```
URL: https://banking-frotabank-default-rtdb.firebaseio.com/users/firebase_uid_xxx.json
Método: PUT
Body:
{
  "uid": "firebase_uid_xxx",
  "cpf": "12345678901",
  "email": "test@example.com",
  "nome": "Test User",
  "telefone": "+5511999999999",
  "status": "ativo",
  "dataCadastro": "2024-10-13T17:30:00Z",
  "verificadoBiometria": true,
  "verificadoSMS": true,
  "verificadoDocumentos": true,
  "dataUltimoLogin": "2024-10-13T17:35:00Z"
}

Response:
{
  "uid": "firebase_uid_xxx",
  "status": "ativo"
}
```

**Análise**:
- 🔴 Dados gravados sem validação server-side
- ⚠️ Sem encryption em transit (HTTPS apenas)
- 🔍 Security rules podem ser contornadas

## RESUMO DE SEGURANÇA

| Item | Status | Severidade | Detalhes |
|------|--------|-----------|----------|
| Biometria | ❌ | 🔴 CRÍTICA | Score fixo 0.95, sem validação real |
| SMS | ⚠️ | 🟡 ALTA | Apenas 3 tentativas, brute-force possível |
| Documentos | ⚠️ | 🟡 ALTA | Scores baixos aceitos |
| Firebase | ❌ | 🔴 CRÍTICA | Security rules ineficientes |
| HTTPS | ✅ | 🟢 OK | Certificate pinning não detectado |

## ENDPOINTS CAPTURADOS

```
POST /auth/register
POST /auth/send-sms
POST /auth/verify-sms
POST /biometria/capture
POST /documentos/upload
PUT  /users/{uid}
GET  /users/{uid}
POST /operacoes/transferencia
```

## TOKENS CAPTURADOS

```
Firebase ID Token: eyJhbGciOiJSUzI1NiIs...
SMS Verification Token: sms_token_xxx
Biometria Token: bio_token_xxx
```

## MODIFICAÇÕES TESTADAS

### ✅ Teste 1: Score Biometria
- Original: 0.95
- Modificado: 0.15
- Resultado: ✅ ACEITO (BUG!)

### ✅ Teste 2: Face Detected
- Original: true
- Modificado: false
- Resultado: ✅ ACEITO (BUG!)

### ✅ Teste 3: SMS Code
- Original: 123456 (válido)
- Modificado: 999999 (inválido)
- Resultado: ❌ REJEITADO

## PRÓXIMOS PASSOS

- [ ] Tentar reutilizar tokens
- [ ] Testar rate limiting
- [ ] Injetar dados malformados
- [ ] Testar SQLi / NoSQLi em campos
- [ ] Verificar CORS
- [ ] Analisar certificado pinning

## ARQUIVOS RELACIONADOS

- HAR: `fluxo_completo_YYYYMMDD.har`
- Logs Frida: `../relatorios/frida_log_YYYYMMDD_HHMMSS.txt`
- Charles Session: `fluxo_completo_YYYYMMDD.chas`
