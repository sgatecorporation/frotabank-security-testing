#!/usr/bin/env python3
"""
Frida Runner para Frotabank
Conecta ao dispositivo Android e injeta scripts Frida
"""

import frida
import sys
import os
import json
from datetime import datetime

class FridaRunner:
    def __init__(self):
        self.device = None
        self.session = None
        self.script = None
        self.app_name = "Frotabank"
        self.log_file = None

    def connect_device(self):
        """Conectar ao dispositivo Android via USB"""
        try:
            self.device = frida.get_usb_device()
            print(f"[+] Dispositivo conectado: {self.device.name}")
            print(f"[+] ID: {self.device.id}")
            return True
        except frida.TimedOutError:
            print("[-] Timeout ao conectar ao dispositivo")
            return False
        except Exception as e:
            print(f"[-] Erro: {e}")
            return False

    def list_processes(self):
        """Listar processos do dispositivo"""
        print("\n[*] Procurando Frotabank...")
        try:
            processes = self.device.enumerate_processes()
            for proc in processes:
                if "frota" in proc.name.lower():
                    print(f"  [+] Encontrado: PID {proc.pid} | {proc.name}")
        except Exception as e:
            print(f"  [!] Aviso ao enumerar: {e}")

    def attach_app(self):
        """Anexar ao processo do Frotabank"""
        try:
            # Verificar se app está rodando
            processes = {p.name: p.pid for p in self.device.enumerate_processes()}

            if self.app_name in processes:
                pid = processes[self.app_name]
                print(f"[+] App encontrado! PID: {pid}")
                self.session = self.device.attach(pid)
                print(f"[+] Sessão criada")
                return True
            else:
                print(f"[-] App '{self.app_name}' não está rodando")
                print("[*] Inicie o app manualmente e tente novamente")
                return False
        except Exception as e:
            print(f"[-] Erro ao anexar: {e}")
            return False

    def load_script(self, script_path):
        """Carregar script Frida"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()

            print(f"[*] Carregando script: {script_path}")
            self.script = self.session.create_script(code)
            self.script.on('message', self.on_message)
            self.script.load()
            print("[+] Script carregado com sucesso")
            return True
        except FileNotFoundError:
            print(f"[-] Script não encontrado: {script_path}")
            return False
        except Exception as e:
            print(f"[-] Erro ao carregar script: {e}")
            return False

    def on_message(self, message, data):
        """Callback para mensagens do script"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        if message['type'] == 'send':
            payload = message.get('payload', '')
            print(f"[{timestamp}] {payload}")
            self.log_message(f"{payload}")
        elif message['type'] == 'error':
            print(f"[ERROR] {message.get('stack', message)}")

    def log_message(self, msg):
        """Log mensagens em arquivo"""
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} | {msg}\n")

    def create_log_file(self):
        """Criar arquivo de log"""
        log_dir = "../relatorios"
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, f"frida_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        print(f"[*] Log: {self.log_file}")

    def run(self, script_name):
        """Executar fluxo completo"""
        self.create_log_file()

        if not self.connect_device():
            return

        self.list_processes()

        if not self.attach_app():
            return

        script_path = os.path.join(os.path.dirname(__file__), script_name)
        if not self.load_script(script_path):
            return

        print("\n[+] Frida rodando! Pressione Ctrl+C para sair")
        print("[*] Interaja com o app normalmente...\n")

        try:
            while True:
                input()
        except KeyboardInterrupt:
            print("\n[*] Parando...")
            self.session.detach()
            print("[+] Desconectado")

if __name__ == "__main__":
    script_name = sys.argv[1] if len(sys.argv) > 1 else "01_bypass_biometria_force_score.js"

    runner = FridaRunner()
    runner.run(script_name)
