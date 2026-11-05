#!/usr/bin/env python3
"""
Frida Runner - modo SPAWN (inicia app com hooks desde o início)
"""

import frida
import sys
import os
from datetime import datetime

package = "br.com.frotabank.app"
scripts = sys.argv[1:] if len(sys.argv) > 1 else ["bypass_playstore_check.js", "01_bypass_biometria_force_score.js"]

print(f"[*] Conectando ao dispositivo...")
device = frida.get_usb_device()
print(f"[+] Conectado: {device.name}")

print(f"[*] Spawning {package}...")
pid = device.spawn([package])
print(f"[+] App iniciado com PID: {pid}")

session = device.attach(pid)
print(f"[+] Sessão criada!")

for script_file in scripts:
    if not os.path.exists(script_file):
        print(f"[-] Script não encontrado: {script_file}")
        continue
    print(f"[*] Carregando: {script_file}")
    with open(script_file, 'r', encoding='utf-8') as f:
        code = f.read()
    script = session.create_script(code)
    script.on('message', lambda msg, data: print(f"[Frida] {msg.get('payload', msg)}"))
    script.load()
    print(f"[+] Carregado: {script_file}")

print(f"[*] Resumindo app...")
device.resume(pid)
print(f"[+] App rodando com hooks! Pressione Ctrl+C para sair\n")

try:
    while True:
        input()
except KeyboardInterrupt:
    print(f"\n[*] Desconectando...")
    session.detach()
    print(f"[+] Pronto!")
