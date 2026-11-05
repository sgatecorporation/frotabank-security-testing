# Guia Completo: Ecossistema de Testes Frotabank

## ESTRUTURA

```
TESTE_SEGURANCA/
├── setup/
│   ├── 01_FRIDA_SERVER_SETUP.md
│   └── 02_CHARLES_PROXY_SETUP.md
├── scripts_frida/
│   ├── 00_run_frida.py (executor)
│   ├── 01_bypass_biometria_force_score.js
│   ├── 02_bypass_sms_verification.js
│   └── ...
├── fluxos_capturados/
│   ├── TEMPLATE_FLUXO_COMPLETO.md
│   ├── fluxo_cadastro_20241013.har
│   ├── fluxo_login_20241013.har
│   └── ...
├── regras_charles/
│   ├── block_list.txt
│   ├── custom_rules.xml
│   └── ...
├── testes_modificados/
│   ├── TEST_CASE_001_BYPASS_BIOMETRIA.md
│   ├── TEST_CASE_002_BYPASS_SMS.md
│   ├── TEST_CASE_003_FIREBASE_INJECTION.md
│   └── ...
├── relatorios/
│   ├── frida_log_20241013_170000.txt
│   ├── summary_findings.md
│   └── vulnerability_report.pdf
└── GUIA_COMPLETO_TESTES.md (este arquivo)
```

## FLUXO DE TESTES

### Dia 1: Setup e Captura
```
1. Instalar Frida Server (setup/01_FRIDA_SERVER_SETUP.md)
2. Instalar Charles Proxy (setup/02_CHARLES_PROXY_SETUP.md)
3. Capturar fluxo completo de cadastro
4. Salvar em fluxos_capturados/
5. Documentar em TEMPLATE_FLUXO_COMPLETO.md
```

### Dia 2-3: Testes Baseados em Fluxo
```
1. Para cada endpoint capturado:
   a. Criar TEST_CASE_XXX_ENDPOINT_NAME.md
   b. Descrever modificação esperada
   c. Executar teste com Frida + Charles
   d. Documentar resultado
   e. Salvar logs em relatorios/
```

### Dia 4: Análise e Relatório
```
1. Consolidar todos os achados
2. Agrupar por severidade
3. Calcular CVSS scores
4. Gerar summary_findings.md
5. Criar vulnerability_report.pdf
```

## COMO EXECUTAR UM TESTE

### 1. Preparar Ambiente
```bash
# Terminal 1: Frida Server (no celular via adb)
adb shell /data/local/tmp/frida-server

# Terminal 2: Charles Proxy (já aberto)
# Menu > Proxy > Start Recording

# Terminal 3: Verificar conexão
frida-ps -U
```

### 2. Iniciar Teste
```bash
# Terminal 4: Executar Frida Script
cd testes_seguranca/scripts_frida
python 00_run_frida.py 01_bypass_biometria_force_score.js
```

### 3. Interagir com App
- Abrir Frotabank
- Navegador até ponto de teste (ex: biometria)
- Observar logs do Frida
- Charles mostra requisições interceptadas

### 4. Modificar Requisição no Charles
- Charles: Breakpoints > habilitar para endpoint
- App faz requisição > Charles pausa
- Editar JSON na resposta
- Clicar "Execute"
- App processa resposta modificada

### 5. Documentar Resultado
- Screenshot da requisição/resposta
- Copiar HAR file
- Preencher TEST_CASE
- Salvar logs em relatorios/

## TESTES PLANEJADOS

### Categoria: Autenticação
- [ ] TEST_CASE_001: Bypass biometria
- [ ] TEST_CASE_002: Bypass SMS
- [ ] TEST_CASE_003: Token reutilização
- [ ] TEST_CASE_004: Brute force SMS

### Categoria: Documentos
- [ ] TEST_CASE_005: Score documento baixo
- [ ] TEST_CASE_006: Imagem fake
- [ ] TEST_CASE_007: Documento expirado

### Categoria: Firebase
- [ ] TEST_CASE_008: Injeção dados usuario
- [ ] TEST_CASE_009: Acesso cross-user
- [ ] TEST_CASE_010: NoSQL injection

### Categoria: Rede
- [ ] TEST_CASE_011: MITM com certificado falso
- [ ] TEST_CASE_012: Replay de requisição
- [ ] TEST_CASE_013: Certificate pinning bypass

## CAMPOS A DOCUMENTAR EM CADA TESTE

```markdown
# Test Case XXX: [NOME]

## OBJETIVO
Breve descrição do que estamos testando

## VULNERABILIDADE EXPLORADA
Qual é a fraqueza de segurança

## REQUISIÇÃO ORIGINAL
```json
// Cole aqui a requisição capturada do Charles
```

## MODIFICAÇÃO REALIZADA
```json
// Cole aqui a versão modificada
```

## RESULTADO
- Status HTTP
- Resposta recebida
- Comportamento do app
- Evidência de sucesso/falha

## IMPACTO
- Qual a consequência se explorado
- CVSS score

## REPRODUÇÃO
- Passo a passo exato
- Ferramentas necessárias
- Tempo estimado
```

## URLS E CREDENCIAIS A DOCUMENTAR

Arquivo: `credenciais_teste.txt` (MANTIDO PRIVADO)
```
# Não commitar este arquivo em git!

Firebase Config:
- API Key: AIzaSyDfNsvvdHTNyW433gYM2HKXSoD4xS4wjP8
- Database URL: https://banking-frotabank-default-rtdb.firebaseio.com/
- Project ID: banking-frotabank

Contas Teste:
- CPF: 12345678901
- Email: test001@example.com
- Senha: [HASH]
- Token Firebase: eyJhbGc...

Endpoints Descobertos:
- https://banking-frotabank-default-rtdb.firebaseio.com/users/{uid}.json
- https://banking-frotabank-default-rtdb.firebaseio.com/biometria/{uid}
- etc...
```

## CHECKLIST FINAL

Antes de terminar os testes:

- [ ] Todos os fluxos capturados em HAR
- [ ] Todos os endpoints documentados
- [ ] Pelo menos 1 teste por categoria realizado
- [ ] Todos os logs salvos em relatorios/
- [ ] Summary findings preenchido
- [ ] CVSS scores calculados
- [ ] Evidências (screenshots/videos)
- [ ] Relatório final gerado

## PRÓXIMAS FASES

### Fase 2: Análise Server-Side
- Acessar Firebase diretamente
- Verificar security rules
- Tentar modificar dados via REST API

### Fase 3: Análise de Código
- Decompile APK completo
- Analisar libs nativas
- Verificar obfuscation

### Fase 4: Relatório Final
- Consolidar todas as vulnerabilidades
- Gerar CVSS scores
- Criar remediation roadmap
- Preparar apresentação

---

**Versão**: 1.0
**Última Atualização**: 2024-10-13
**Responsável**: [SEU_NOME]
