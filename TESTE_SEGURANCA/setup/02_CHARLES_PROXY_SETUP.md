# Setup Charles Proxy para Interceptar Requisições Frotabank

## 1. INSTALAR CHARLES
- Download: https://www.charlesproxy.com/download/
- Versão: 4.6.x ou superior
- Windows: Charles_4.6.x_setup.exe

## 2. CONFIGURAR CHARLES

### A. Habilitar Proxy HTTP
- Abrir Charles
- Menu: Proxy > Proxy Settings
- HTTP Proxy Port: 8888
- ✅ Enable transparent HTTP proxying (opcional)

### B. Gerar SSL Certificate
- Menu: Help > SSL Proxying > Install Charles Root Certificate...
- Salvar certificado em local seguro

## 3. CONFIGURAR CELULAR/EMULADOR

### Para Emulador (LD Player):
```bash
# Emulador já tem proxy integrado
# Configurar: System Settings > WiFi > Proxy > Manual
# Proxy Host: 127.0.0.1 ou IP do PC
# Proxy Port: 8888
```

### Para Celular Físico:
```bash
# WiFi > Editar > Proxy Avançado > Manual
# Proxy Host: IP_DO_PC (ex: 192.168.1.100)
# Proxy Port: 8888
# Salvar
```

## 4. INSTALAR CERTIFICADO NO CELULAR

- Download do Charles Certificate em: http://chls.pro/ssl (via celular)
- Instalação:
  - Celular: Configurações > Segurança > Instalar certificado
  - Selecionar arquivo baixado
  - Nomear: "Charles"

## 5. TESTAR CONEXÃO

- No Charles: Menu > Tools > Map Remote
- Criar uma regra de teste
- Abrir browser no celular e acessar um site
- Verificar se requisição aparece no Charles

## 6. FROTABANK ESPECÍFICO

### Certificate Pinning
⚠️ **IMPORTANTE**: Frotabank pode ter certificate pinning

Se app não conectar após proxy:
1. Usar Frida para desabilitar certificate pinning
2. Ver script em: `scripts_frida/02_bypass_certificate_pinning.js`

### Interceptar Requisições do Frotabank

```
Charles > Proxy > SSL Proxying Settings
Domain: *.banking-frotabank.firebaseio.com
Port: 443
✅ Habilitar
```

## 7. CAPTURAR REQUISIÇÕES

### No Charles:
- Menu: Session > Start Recording
- Abrir Frotabank
- Realizar ação (login, biometria, SMS, etc)
- Menu: Session > Stop Recording
- Clicar em requisição para ver detalhes

### Salvar Sessão:
- File > Save Session As...
- Salvar em: `fluxos_capturados/`

### Exportar:
- Selecionar requisições > Clicar direito > Export Session
- Formato JSON/HAR

## 8. ESTRUTURA DO HAR

Arquivo salvo terá:
```json
{
  "log": {
    "entries": [
      {
        "request": {
          "method": "POST",
          "url": "https://...",
          "headers": [...],
          "postData": {...}
        },
        "response": {
          "status": 200,
          "headers": [...],
          "content": {...}
        }
      }
    ]
  }
}
```

## TROUBLESHOOTING

**App não conecta com proxy ativo**
- Desabilitar proxy, abrir app, verificar domínios em Charles
- Pode haver certificate pinning

**Charles não mostra requisições HTTPS**
- Verificar se certificado está instalado no celular
- Verificar SSL Proxying Settings

**Erro de timeout**
- Aumentar timeout no Charles: Tools > Options > Connection

## REGRAS ÚTEIS

### Block Rule (bloquear certa requisição):
- Tools > Block List
- Adicionar: banking-frotabank.firebaseio.com/...

### Breakpoints (pausar e editar em tempo real):
- Proxy > Breakpoint Settings
- Adicionar domínio
- Charles pausa requisição, permite editar
