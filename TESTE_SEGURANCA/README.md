# 🔒 Ecossistema Profissional de Testes de Segurança - Frotabank

Ambiente completo para realização de testes de segurança, análise de vulnerabilidades e QA da aplicação bancária Frotabank.

## 📁 Estrutura

```
TESTE_SEGURANCA/
│
├── setup/                          # Guias de configuração
│   ├── 01_FRIDA_SERVER_SETUP.md   # Setup Frida Server + Python client
│   └── 02_CHARLES_PROXY_SETUP.md  # Setup Charles Proxy para interceptação
│
├── scripts_frida/                  # Scripts de injeção Frida
│   ├── 00_run_frida.py            # Runner Python para executar scripts
│   ├── 01_bypass_biometria_force_score.js
│   ├── 02_bypass_sms_verification.js
│   └── ...
│
├── fluxos_capturados/              # Fluxos completos capturados
│   ├── TEMPLATE_FLUXO_COMPLETO.md  # Template de documentação
│   ├── fluxo_cadastro_*.har        # Arquivos HAR com requisições
│   └── ...
│
├── regras_charles/                 # Configurações Charles Proxy
│   ├── block_list.txt
│   ├── breakpoints.xml
│   └── ...
│
├── testes_modificados/             # Test cases documentados
│   ├── TEST_CASE_001_BYPASS_BIOMETRIA.md
│   ├── TEST_CASE_002_BYPASS_SMS.md
│   └── ...
│
├── relatorios/                     # Logs e relatórios
│   ├── frida_log_*.txt
│   ├── summary_findings.md
│   └── vulnerability_report.pdf
│
└── GUIA_COMPLETO_TESTES.md         # Este guia
```

## 🚀 Quick Start

### 1. Primeira Execução (Dia 1)
```bash
# Terminal 1: Iniciar Frida Server
adb shell /data/local/tmp/frida-server

# Terminal 2: Abrir Charles Proxy
# (GUI) Menu > Proxy > Start Recording

# Terminal 3: Rodar Frida Script
cd TESTE_SEGURANCA/scripts_frida
python 00_run_frida.py 01_bypass_biometria_force_score.js
```

### 2. Capturar Fluxo
- Abrir Frotabank no celular
- Realizar ação completa (cadastro, login, biometria)
- Charles captura automaticamente
- Salvar session: File > Save Session As

### 3. Documentar Achados
- Copiar fluxo capturado para `fluxos_capturados/`
- Preencher `TEMPLATE_FLUXO_COMPLETO.md`
- Criar `TEST_CASE_XXX.md` para cada vulnerabilidade

## 🔍 Testes Implementados

| ID | Nome | Categoria | Status |
|----|------|-----------|--------|
| 001 | Bypass Biometria Score | Auth | ✅ Pronto |
| 002 | Bypass SMS Verification | Auth | 📝 Planejado |
| 003 | Token Reutilização | Auth | 📝 Planejado |
| 004 | Brute Force SMS | Auth | 📝 Planejado |
| 005 | Score Documento Baixo | Docs | 📝 Planejado |
| 006 | Firebase Injection | DB | 📝 Planejado |

## 📊 Campos Documentados

Cada teste inclui:
- ✅ Objetivo e vulnerabilidade explorada
- ✅ Requisição original (completa)
- ✅ Modificação realizada
- ✅ Resposta do servidor
- ✅ Comportamento do app
- ✅ Impacto de segurança
- ✅ CVSS Score
- ✅ Reprodução passo-a-passo
- ✅ Evidence (screenshots/logs)
- ✅ Recomendação de remediação

## 🔐 Dados Capturados

### Firebase Configuration
```json
{
  "apiKey": "AIzaSyDfNsvvdHTNyW433gYM2HKXSoD4xS4wjP8",
  "databaseURL": "https://banking-frotabank-default-rtdb.firebaseio.com/",
  "projectId": "banking-frotabank"
}
```

### Endpoints Mapeados
- POST /auth/register
- POST /auth/send-sms
- POST /auth/verify-sms
- POST /biometria/capture
- POST /documentos/upload
- PUT /users/{uid}
- GET /users/{uid}

### Tokens Capturados
- Firebase ID Tokens
- SMS Verification Tokens
- Biometria Tokens
- Session Tokens

## 📈 Progressão

### Semana 1: Setup + Captura
- [x] Instalar ferramentas
- [x] Configurar Frida Server
- [x] Configurar Charles Proxy
- [x] Capturar fluxo completo
- [x] Documentar endpoints

### Semana 2: Testes Iniciais
- [ ] Executar TEST_CASE_001
- [ ] Executar TEST_CASE_002
- [ ] Executar TEST_CASE_003
- [ ] Executar TEST_CASE_004

### Semana 3: Análise Profunda
- [ ] Firebase direct access
- [ ] Code analysis
- [ ] Native libs analysis

### Semana 4: Relatório
- [ ] Consolidar findings
- [ ] CVSS scores
- [ ] Remediation roadmap
- [ ] Final report

## ⚠️ Avisos de Segurança

- 🔐 **NÃO committar** credenciais em git
- 🔒 **Manter privado** todos os tokens capturados
- 🚫 **Usar apenas** em ambiente de teste autorizado
- 📝 **Documentar** tudo sem economizar detalhes

## 📞 Suporte

Para dúvidas:
1. Consultar `GUIA_COMPLETO_TESTES.md`
2. Verificar `setup/` para problemas de instalação
3. Revisar testes anteriores em `testes_modificados/`

---

**Última Atualização**: 2024-10-13
**Versão**: 1.0
**Ambiente**: Análise de Segurança Frotabank
