#!/usr/bin/env python3
"""Download Frida Server para Android"""

import urllib.request
import os
import sys

# Versão do Frida Server (compatível com Frida 17.23.3)
FRIDA_VERSION = "17.23.3"

# URL de download
FRIDA_ARM64 = f"https://github.com/frida/frida/releases/download/{FRIDA_VERSION}/frida-server-{FRIDA_VERSION}-android-arm64.xz"
FRIDA_ARM32 = f"https://github.com/frida/frida/releases/download/{FRIDA_VERSION}/frida-server-{FRIDA_VERSION}-android-arm.xz"

def download_file(url, filename):
    """Baixar arquivo"""
    print(f"[*] Baixando {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        size_mb = os.path.getsize(filename) / 1024 / 1024
        print(f"[✓] Download completo: {filename}")
        print(f"[*] Tamanho: {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"[-] Erro: {e}")
        return False

def main():
    # Escolher arquitetura
    print("\n=== Frida Server Download ===\n")
    print("Escolha a arquitetura do seu celular:")
    print("1. ARM64 (recomendado - maioria dos celulares modernos)")
    print("2. ARM32 (celulares mais antigos)")

    choice = input("\nOpção (1 ou 2): ").strip()

    if choice == "1":
        url = FRIDA_ARM64
        filename = f"frida-server-{FRIDA_VERSION}-android-arm64.xz"
    elif choice == "2":
        url = FRIDA_ARM32
        filename = f"frida-server-{FRIDA_VERSION}-android-arm.xz"
    else:
        print("[-] Opção inválida")
        sys.exit(1)

    # Download
    if download_file(url, filename):
        print(f"\n[✓] Arquivo pronto: {filename}")
        print("\nPróximos passos:")
        print(f"1. Descomprimir: xz -d {filename}")
        print("2. Enviar: adb push frida-server-* /data/local/tmp/frida-server")
        print("3. Permissão: adb shell chmod +x /data/local/tmp/frida-server")
        print("4. Rodar: adb shell /data/local/tmp/frida-server")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
