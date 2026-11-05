#!/usr/bin/env python3
"""
Spawn do Frotabank com Frida stealth (porta aleatoria + binario renomeado).
Bypassa anti-Frida que detecta o nome 'frida-server' e porta 27042.
"""
import frida
import sys
import os
import time
import subprocess
from datetime import datetime

PACKAGE = "br.com.frotabank.app"
SCRIPT_FILE = "09_capture_post_user.js"
LOG_DIR = "../relatorios"
FRIDA_PORT = 34567
FRIDA_HOST = f"127.0.0.1:{FRIDA_PORT}"

def ensure_adb_forward():
    """Garante que adb forward esta ativo"""
    try:
        subprocess.run(["adb", "forward", f"tcp:{FRIDA_PORT}", f"tcp:{FRIDA_PORT}"],
                       capture_output=True, timeout=5)
        print(f"[+] adb forward tcp:{FRIDA_PORT} -> tcp:{FRIDA_PORT}")
    except Exception as e:
        print(f"[!] adb forward falhou: {e}")

def ensure_frida_running():
    """Verifica se .sysmd esta rodando; se nao, inicia"""
    try:
        r = subprocess.run(["adb", "shell", "ps -A | grep .sysmd"],
                           capture_output=True, timeout=5, text=True)
        if ".sysmd" in r.stdout:
            print("[+] frida-server (.sysmd) ja esta rodando")
            return
        print("[!] frida-server nao esta rodando, iniciando...")
        subprocess.Popen(
            ["adb", "shell", "su root sh -c",
             f"'nohup /data/local/tmp/.sysmd -l 127.0.0.1:{FRIDA_PORT} > /dev/null 2>&1 &'"],
        )
        time.sleep(3)
    except Exception as e:
        print(f"[!] erro ao verificar frida: {e}")

def main():
    ensure_adb_forward()
    ensure_frida_running()
    ensure_adb_forward()  # novamente apos iniciar frida
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"stealth_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    log_file = open(log_path, "w", encoding="utf-8")
    print(f"[*] Log file: {log_path}")

    print(f"[*] Conectando ao Frida via {FRIDA_HOST}...")
    device_mgr = frida.get_device_manager()
    device = device_mgr.add_remote_device(FRIDA_HOST)
    print(f"[+] Device: {device.name}")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        code = f.read()

    def on_msg(msg, data):
        if msg["type"] == "send":
            text = str(msg.get("payload", ""))
            print(text, flush=True)
            log_file.write(text + "\n")
            log_file.flush()
        elif msg["type"] == "error":
            err = f"[ERR] {msg.get('stack', msg)}"
            print(err, flush=True)
            log_file.write(err + "\n")
            log_file.flush()

    print(f"[*] Spawning {PACKAGE}...")
    pid = device.spawn([PACKAGE])
    print(f"[+] PID: {pid}")
    session = device.attach(pid)

    script = session.create_script(code)
    script.on("message", on_msg)
    script.load()
    print("[+] Script carregado")

    device.resume(pid)
    print(f"[+] App iniciado. Faz o fluxo agora.")
    print("[*] Captura rodando. Ctrl+C para parar.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Parando...")
        log_file.close()
        try:
            session.detach()
        except Exception:
            pass
        print(f"[+] Log salvo em: {log_path}")

if __name__ == "__main__":
    main()
