#!/usr/bin/env python3
"""Download e instrui instalação do Charles Proxy"""

import urllib.request
import os
import webbrowser
import subprocess
import sys

print("\n" + "="*50)
print("Charles Proxy - Download & Install")
print("="*50 + "\n")

print("[*] Charles Proxy 4.6.x (Windows)")
print("[*] Download direto: https://www.charlesproxy.com/download/latest/charles-4.6.3-win64.zip\n")

print("Opções de instalação:\n")
print("1. Abrir página de download no navegador")
print("2. Ver instruções manual")
print("3. Sair\n")

choice = input("Escolha (1, 2 ou 3): ").strip()

if choice == "1":
    print("\n[*] Abrindo página de download...")
    webbrowser.open("https://www.charlesproxy.com/download/")
    print("[✓] Página aberta no navegador")

elif choice == "2":
    print("\n" + "="*50)
    print("INSTALAÇÃO MANUAL - CHARLES PROXY")
    print("="*50)
    print("""
1. Download:
   - Acesse: https://www.charlesproxy.com/download/
   - Baixe: charles-4.6.3-win64.zip (ou versão mais recente)
   - Tamanho: ~50 MB

2. Instalação:
   - Descompacte o ZIP
   - Execute: Charles.exe
   - Windows pode pedir permissão de firewall
   - Aceite para "Private networks" e "Public networks"

3. Primeiro Uso:
   - Menu: Proxy > Proxy Settings
   - HTTP Proxy Port: 8888
   - ✓ Enable Transparent HTTP Proxying
   - OK

4. Certificado SSL:
   - Menu: Help > SSL Proxying > Install Charles Root Certificate
   - Salvar em local seguro

5. Configurar Celular:
   - WiFi Settings > Editar
   - Proxy > Manual
   - Host: 192.168.X.X (seu PC na rede)
   - Port: 8888
   - Salvar

6. Instalar Certificado no Celular:
   - Abrir: http://chls.pro/ssl (via celular)
   - Download do certificado
   - Configurações > Segurança > Instalar certificado
   - Nomear: "Charles"
   - Instalar

7. Testar:
   - Charles: Menu > Session > Start Recording
   - Celular: Abrir navegador, acessar site qualquer
   - Charles deve mostrar requisições

8. Interceptar Frotabank:
   - Charles > Proxy > SSL Proxying Settings
   - Add: Domain = *.banking-frotabank.firebaseio.com
   - Port: 443
   - Habilitar
   - Abrir Frotabank no celular
   - Charles intercepta requisições!

TROUBLESHOOTING:

❌ "App não conecta com proxy":
   - Desabilitar proxy
   - Abrir app
   - Verificar domains reais em Charles
   - Pode haver certificate pinning

❌ "Charles não mostra HTTPS":
   - Verificar se certificado está instalado no celular
   - Verificar SSL Proxying Settings

❌ "Timeout":
   - Tools > Options > Connection
   - Aumentar timeout

PRÓXIMOS PASSOS:

✓ Charles Proxy instalado e rodando
✓ Celular configurado
✓ Frida Server rodando
✓ Agora rodar testes!

Execute: python scripts_frida/00_run_frida.py
    """)

elif choice == "3":
    print("[*] Saindo...")
    sys.exit(0)
else:
    print("[-] Opção inválida")
    sys.exit(1)

print("\n" + "="*50)
print("Para mais detalhes, consulte: setup/02_CHARLES_PROXY_SETUP.md")
print("="*50 + "\n")
