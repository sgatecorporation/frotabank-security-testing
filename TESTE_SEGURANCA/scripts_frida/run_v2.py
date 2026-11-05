#!/usr/bin/env python3
"""
Spawn + load script + resume + RPC install.
Essa ordem contorna o 'Java is not defined' em spawn pausado.
"""
import frida
import sys
import os
import time
import subprocess
from datetime import datetime

PACKAGE = "br.com.frotabank.app"
SCRIPT = "14_safe_bypass.js"
LOG_DIR = "../relatorios"
FRIDA_PORT = 34567

def ensure_setup():
    subprocess.run(["adb", "forward", f"tcp:{FRIDA_PORT}", f"tcp:{FRIDA_PORT}"],
                   capture_output=True, timeout=5)
    r = subprocess.run(["adb", "shell", "ps -A"],
                       capture_output=True, timeout=5, text=True)
    if ".sysmd" not in r.stdout:
        print("[!] iniciando frida-server...")
        subprocess.Popen(["adb", "shell", "su root sh -c",
                          f"'nohup /data/local/tmp/.sysmd -l 127.0.0.1:{FRIDA_PORT} > /dev/null 2>&1 &'"])
        time.sleep(3)
    print("[+] Setup OK")

def main():
    ensure_setup()

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    log_file = open(log_path, "w", encoding="utf-8")
    print(f"[*] Log: {log_path}")

    device = frida.get_device_manager().add_remote_device(f"127.0.0.1:{FRIDA_PORT}")
    print(f"[+] Device: {device.name}")

    with open(SCRIPT, "r", encoding="utf-8") as f:
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
    print("[+] Script carregado (sem Java.perform ainda)")

    # Resume PRIMEIRO - deixa o Java carregar
    device.resume(pid)
    print(f"[+] App resumido, polling pra Java carregar...")

    # Retry install varias vezes - Java pode demorar
    installed = False
    for attempt in range(30):  # 30 tentativas = 30s
        time.sleep(1)
        try:
            result = script.exports_sync.installjava()
            print(f"[+] RPC installjava ({attempt+1}s): {result}")
            installed = True
            break
        except Exception as e:
            if attempt == 0 or attempt % 5 == 0:
                print(f"[.] tentativa {attempt+1}s: {str(e)[:80]}")

    if not installed:
        print("[-] Nao conseguiu instalar Java hooks em 30s")

    print("[*] Captura rodando. Ctrl+C para parar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Parando...")
        log_file.close()
        try: session.detach()
        except: pass
        print(f"[+] Log: {log_path}")

if __name__ == "__main__":
    main()
