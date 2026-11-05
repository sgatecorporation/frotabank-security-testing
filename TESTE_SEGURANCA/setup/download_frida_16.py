#!/usr/bin/env python3
import urllib.request
import lzma

url = "https://github.com/frida/frida/releases/download/15.8.0/frida-server-15.8.0-android-arm64.xz"
filename = "frida-server-15.8.0-android-arm64.xz"

print(f"[*] Baixando {filename}...")
urllib.request.urlretrieve(url, filename)
print("[✓] Download completo!")

# Descomprimir
print("[*] Descomprimindo...")
with lzma.open(filename, 'rb') as f:
    with open('frida-server-15.8.0', 'wb') as out:
        out.write(f.read())
print("[✓] Descomprimido! Arquivo: frida-server-15.8.0")
