import frida
import sys
import time

# Conectar ao dispositivo
try:
    device = frida.get_usb_device()
    print(f"[+] Dispositivo: {device.name}")
except Exception as e:
    print(f"[-] Erro ao conectar: {e}")
    sys.exit(1)

# Carregar o script de hooks
try:
    with open('FRIDA_HOOKS_QUICK_REFERENCE.js', 'r', encoding='utf-8') as f:
        hook_source = f.read()
except Exception as e:
    print(f"[-] Erro ao ler hooks: {e}")
    sys.exit(1)

# Enumerar processos
processes = device.enumerate_processes()
frota_pid = None

for proc in processes:
    if 'Frotabank' in proc.name:
        frota_pid = proc.pid
        print(f"[+] Encontrado: {proc.name} (PID: {frota_pid})")
        break

if not frota_pid:
    print("[-] Frotabank não está rodando!")
    print("[*] Processos disponíveis com 'frota':")
    for proc in processes:
        if 'frota' in proc.name.lower():
            print(f"    {proc.name}")
    sys.exit(1)

# Anexar e injetar
try:
    session = device.attach(frota_pid)
    print("[+] Anexado ao processo!")
    
    script = session.create_script(hook_source)
    script.on('message', lambda msg, data: print(f"[HOOK] {msg}"))
    script.load()
    
    print("[✓] Hooks carregados com sucesso!")
    print("[*] Aguardando eventos...")
    
    # Manter rodando
    time.sleep(3600)  # 1 hora
    
except Exception as e:
    print(f"[-] Erro ao injetar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
