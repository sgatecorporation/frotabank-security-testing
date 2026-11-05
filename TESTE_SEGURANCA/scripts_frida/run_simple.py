#!/usr/bin/env python3
"""
Frida Runner Simplificado - sem enumeração de processos
"""

import frida
import sys
import os
from datetime import datetime

app_name = "Frotabank"
script_file = "01_bypass_biometria_force_score.js"

print(f"[*] Conectando ao dispositivo...")
try:
    device = frida.get_usb_device()
    print(f"[+] Conectado: {device.name}")
except Exception as e:
    print(f"[-] Erro: {e}")
    sys.exit(1)

import subprocess
result = subprocess.run(
    ['C:\\Users\\Acer\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe',
     'shell', 'pidof', 'br.com.frotabank.app'],
    capture_output=True, text=True
)
pid = int(result.stdout.strip())
print(f"[*] Frotabank PID: {pid}")
try:
    session = device.attach(pid)
    print(f"[+] Anexado ao {app_name} (PID {pid})!")
except Exception as e:
    print(f"[-] Erro ao anexar: {e}")
    print(f"[!] Certifique-se que {app_name} está aberto no emulador!")
    sys.exit(1)

print(f"[*] Carregando script: {script_file}")
try:
    with open(script_file, 'r', encoding='utf-8') as f:
        code = f.read()

    script = session.create_script(code)
    script.on('message', lambda msg, data: print(f"[Frida] {msg.get('payload', msg)}"))
    script.load()
    print(f"[+] Script carregado!")

except FileNotFoundError:
    print(f"[-] Script não encontrado: {script_file}")
    sys.exit(1)
except Exception as e:
    print(f"[-] Erro ao carregar script: {e}")
    sys.exit(1)

print(f"\n[+] Frida hooks rodando! Pressione Ctrl+C para sair")
try:
    while True:
        input()
except KeyboardInterrupt:
    print(f"\n[*] Desconectando...")
    session.detach()
    print(f"[+] Pronto!")
