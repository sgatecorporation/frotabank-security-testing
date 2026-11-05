#!/usr/bin/env python3
import frida

device = frida.get_usb_device()
processes = device.enumerate_processes()

print("[*] Processos com 'frota':")
for proc in processes:
    if 'frota' in proc.name.lower():
        print(f"  Nome: {proc.name} | PID: {proc.pid}")

print("\n[*] Processo com PID 4183:")
for proc in processes:
    if proc.pid == 4183:
        print(f"  Nome: {proc.name} | PID: {proc.pid}")
