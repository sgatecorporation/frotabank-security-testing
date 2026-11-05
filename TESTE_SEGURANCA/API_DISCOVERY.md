# Frotabank API Discovery - Teste de Segurança

## Plataforma
O Frotabank é um app **white-label** da plataforma **Vizirbank** (banking-as-a-service).
- Framework: **React Native** com **Hermes** bytecode compilado
- Backend: **Vizirbank** API + **Firebase Realtime Database**

## Domínios e Infraestrutura

### API Principal
- **`https://api.id.vizirbank.com`** — API de identidade/autenticação (Vizirbank)

### Firebase (Produção)
- **Realtime DB**: `https://banking-frotabank-default-rtdb.firebaseio.com`
- **App**: `banking-frotabank.firebaseapp.com`
- **Storage**: `rotabanking-frotabank.appspot.com` (note: parece ter typo no storage)

### Firebase (Dev/Staging)
- **Realtime DB**: `https://banking-vizirbank-dev.firebaseio.com`
- **App**: `banking-vizirbank-dev.firebaseapp.com`
- **Storage**: `banking-vizirbank-dev.appspot.com`

### API Keys Firebase
- `AIzaSyC3MFMM3W1Kj0etjm6g5-15ccJNHvDN9VM`
- `AIzaSyDfNsvvdHTNyW433gYM2HKXSoD4xS4wjP8` (provavelmente dev)

### Sentry (Error Tracking)
- DSN: `https://b62d77c573424b72ab986cf655c67938@o939397.ingest.sentry.io/5896304`

### Outros
- **Indicação**: `https://indicacao.frotabank.com.br?cpf={{DOCUMENT}}&token={{JWT_TOKEN}}`
- **Git repos**: `git@github.com:frotabank/banking-app-core.git`, `banking-app-pix-plugin.git`, etc.

## Endpoints API REST (v2)

### Autenticação/Conta
- `v2/accounts` — Contas
- `v2/accounts/mfaEnrollment` — Inscrição MFA
- `v2/accounts/mfaSignIn` — Login MFA
- `v2/auth/login/accountNotActive` — Login conta inativa
- `v2/auth/multifactor-login` — Login multifator
- `v2/auth/credential-already-in-use` — Credencial em uso
- `v2/users/reset-password` — Reset de senha

### Onboarding/Cadastro
- `v2/people/phonesim` — Validação telefone/SIM
- `v2/people/registration-restrictions` — Restrições de registro
- `v2/people/update-emailoan` — Atualizar email
- `v2/people/update-identification-document` — Atualizar documento
- `v2/person-details` — Detalhes da pessoa
- `v2/whitelist/validate-document` — Validar documento na whitelist
- `v2/application/versions` — Versões do app
- `v2/application/time` — Horário do servidor
- `v1/accounts` — Contas v1
- `v1/recaptchaParams` — Parâmetros reCAPTCHA
- `v2/recaptcha` — reCAPTCHA v2

### Cartão
- `v2/card/physicalCardsEntry` — Entrada cartão físico
- `v2/card/validate/cvv` — Validar CVV
- `v2/card/virtual/info` — Info cartão virtual
- `v2/cards/creation-limit` — Limite criação cartões
- `v2/cards/reset-password-with-selfie` — Reset senha com selfie (!)
- `v1/card/unblock/physical` — Desbloquear cartão físico
- `v2/card/assign` — Atribuir cartão
- `v2/card/unblock/virtualCard/checkPassword` — Desbloquear virtual

### PIX
- `v2/pix/dict` — Dicionário PIX
- `v2/pix/medConfirm` — Confirmação MED
- `v2/pix/qr-code-transfer` — Transferência QR Code
- `v2/pix/transfers` — Transferências
- `v2/pix/accounts/addTrustedBankAccount` — Adicionar conta confiável
- `v2/pix/automatic/detail` — Detalhes PIX automático

### Outros
- `v2/billet/generate` — Gerar boleto
- `v2/billet/pdf` — PDF boleto
- `v2/cashback/partnergasstation` — Cashback posto
- `v2/cashback/statement` — Extrato cashback
- `v2/credit-card/limit/card/codeValidation` — Validação código cartão crédito
- `v2/device-key/authorization-success` — Autorização device key
- `v2/loan/additionaldata` — Dados adicionais empréstimo
- `v2/p2p/transfer/bankTransfer` — Transferência P2P
- `v2/statement/confirmDeleteSchedule` — Confirmar exclusão agendamento
- `v2/terms/acceptance` — Aceite de termos
- `v2/transfer/destination-account` — Conta destino transferência
- `v2/transport-card/recharge` — Recarga cartão transporte
- `v2/vouchers/statements` — Extratos voucher
- `v2/income-report` — Relatório de renda
- `v2/ibe/invites` — Convites IBE

## Códigos de Erro da API (BANK_API_*)

### Relevantes ao cadastro:
- `BANK_API_CPF_ALREADY_TAKEN` — CPF já cadastrado
- `BANK_API_USER_DOCUMENT_ALREADY_EXISTS` — Documento já existe
- `BANK_API_USER_DOCUMENT_NOT_AUTHORIZED_ON_WHITELIST` — Documento não autorizado
- `BANK_API_USER_NOT_ALLOW_INFORMED_DOCUMENT` — Documento não permitido
- `BANK_API_ONBOARDING_SESSION_EXPIRED` — Sessão de onboarding expirada
- `BANK_API_SMS_FAILED` — Falha SMS
- `BANK_API_SEND_DOCUMENTS_FAILED` — Falha envio documentos
- `BANK_API_PERSON_TELEPHONE_NOT_FOUND` — Telefone não encontrado
- `BANK_API_PHONE_DOESNT_BELONG_TO_ACCOUNT` — Telefone não pertence à conta
- `BANK_API_USER_BIRTH_NOT_MATCH` — Data nascimento não confere
- `BANK_API_USER_MOTHER_NAME_NOT_MATCH` — Nome da mãe não confere
- `BANK_API_USER_NAME_NOT_MATCH` — Nome não confere
- `BANK_API_NOT_AUTHORIZED_ON_WHITELIST_WITH_CUSTOM_MESSAGE` — Não autorizado na whitelist
- `BANK_API_LACK_OF_REGULATORY_INFORMATION` — Falta informação regulatória

### Feature Flags (REACT_APP_ENABLE_*)
- `REACT_APP_ENABLE_ONBOARDING`
- `REACT_APP_ENABLE_SELFIE_VALIDATION_ON_SENSITIVE_OPERATIONS`
- `REACT_APP_ENABLE_SENSOR_LOGIN`
- `REACT_APP_ENABLE_PINNING`
- `REACT_APP_ENABLE_MULTI_FACTOR_LOGIN`
- `REACT_APP_ENABLE_EDIT_PERSONAL_DATA`
- `REACT_APP_ENABLE_NO_REPEATED_OR_SEQUENTIAL_PASSWORD`

## Fluxo de Cadastro (Estimado)

1. **CPF** → `v2/whitelist/validate-document` (valida se CPF está na whitelist)
2. **Dados pessoais** → `v2/person-details` ou `v2/people/registration-restrictions`
3. **Telefone** → `v2/people/phonesim` (envia SMS)
4. **SMS** → Validação server-side (endpoint não claramente visível)
5. **Selfie/Liveness** → Unico SDK + FaceTec + iProov (validação biométrica)
6. **Documentos** → Upload via SDK (CNH/RG)
7. **Senha** → Criação de senha do app
8. **Aceite** → `v2/terms/acceptance`

## Análise: Possibilidade de Cadastro via API

### O que temos:
- Firebase API Keys (2)
- Firebase Realtime DB URLs (prod e dev)
- Firebase App URLs
- Sentry DSN
- Endpoints REST do Vizirbank (v2/*)
- Feature flags

### Desafios:
1. **Autenticação**: O app usa Firebase Auth. Para fazer requests à API, precisamos de um Firebase Auth token (JWT). Podemos obter usando as API keys com Firebase REST API.
2. **reCAPTCHA**: O app usa reCAPTCHA (`v1/recaptchaParams`, `v2/recaptcha`). Isso pode bloquear requests diretos.
3. **Biometria**: A validação de liveness (Unico/FaceTec/iProov) requer SDKs proprietários com sessões server-side. Não é possível simular facilmente por API.
4. **Device Key**: O app registra uma chave do dispositivo (`v2/device-key`).
5. **Assinatura do App**: CodePush e certificado de assinatura podem ser verificados server-side.

### Estratégia de Teste:
1. **Firebase Auth** → Usar `https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyC3MFMM3W1Kj0etjm6g5-15ccJNHvDN9VM` para criar conta Firebase
2. **Token JWT** → Usar o token retornado como Bearer para chamar endpoints Vizirbank
3. **Interceptar com Proxy** → Configurar mitmproxy/Charles Proxy no emulador para ver o tráfego real
4. **Replay requests** → Capturar e reproduzir requests do app real

### Sobre a assinatura:
Se o objetivo é modificar o app (repackaging), a assinatura original será perdida. O server pode verificar:
- Certificate fingerprint
- Package signature hash
- Shield anti-tamper (com.shield.ptr)
- pairip license verification
- CodePush deployment key

Para testar por API direta, não precisamos resignar - basta fazer as chamadas REST com os tokens corretos.
