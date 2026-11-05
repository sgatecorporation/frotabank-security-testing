#!/usr/bin/env python3
"""
Spawn do Frotabank com Frida + script de captura.
Bypassa anti-Frida melhor que attach.
"""
import frida
import sys
import os
import time
from datetime import datetime

PACKAGE = "br.com.frotabank.app"
SCRIPT_FILE = "09_capture_post_user.js"
LOG_DIR = "../relatorios"

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    log_file = open(log_path, "w", encoding="utf-8")
    print(f"[*] Log file: {log_path}")

    print("[*] Conectando ao LDPlayer...")
    device = frida.get_usb_device(timeout=10)
    print(f"[+] Device: {device.name}")

    # Carregar script antes
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        code = f.read()

    def on_msg(msg, data):
        if msg["type"] == "send":
            payload = msg.get("payload", "")
            text = str(payload)
            print(text, flush=True)
            log_file.write(text + "\n")
            log_file.flush()
        elif msg["type"] == "error":
            err = f"[ERR] {msg.get('stack', msg)}"
            print(err, flush=True)
            log_file.write(err + "\n")
            log_file.flush()

    # Spawn o app pausado
    print(f"[*] Spawning {PACKAGE}...")
    try:
        pid = device.spawn([PACKAGE])
        print(f"[+] PID: {pid}")
    except Exception as e:
        print(f"[-] Spawn falhou: {e}")
        print("[*] Tentando attach ao processo existente...")
        session = device.attach(PACKAGE)
    else:
        session = device.attach(pid)

    script = session.create_script(code)
    script.on("message", on_msg)
    script.load()
    print("[+] Script carregado")

    # Resume o app
    try:
        device.resume(pid)
        print(f"[+] App iniciado. Faz o fluxo agora.")
    except Exception:
        pass

    print("[*] Captura rodando. Ctrl+C para parar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Parando...")
        log_file.close()
        session.detach()
        print(f"[+] Log salvo em: {log_path}")

if __name__ == "__main__":
    main()
