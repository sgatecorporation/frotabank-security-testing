# Setup Frida Server + Frida Python Client

## 1. INSTALAR FRIDA NO PC
```bash
pip install frida frida-tools
```

## 2. BAIXAR FRIDA SERVER PARA ANDROID
- Versão: 16.0.x (compatível com Python frida)
- Download: https://github.com/frida/frida/releases
- Escolher: `frida-server-16.0.x-android-arm64.xz` (pra ARM64) ou arm (pra ARM)

## 3. DESCOMPRIMIR E ENVIAR PARA CELULAR
```bash
# Descomprimir
xz -d frida-server-16.0.x-android-arm64.xz

# Enviar pro celular via ADB
adb push frida-server-16.0.x-android-arm64 /data/local/tmp/frida-server
adb shell chmod +x /data/local/tmp/frida-server
```

## 4. INICIAR FRIDA SERVER NO CELULAR
```bash
# Em um terminal deixado rodando
adb shell /data/local/tmp/frida-server
```

## 5. VERIFICAR CONEXÃO DO PC
```bash
# Em outro terminal
frida-ps -U

# Deve listar os processos do celular
```

## 6. RODAR SCRIPT PYTHON COM FRIDA
```python
import frida

device = frida.get_usb_device()
print(f"Dispositivo: {device}")

# Listar processos
for process in device.enumerate_processes():
    print(f"{process.pid}: {process.name}")

# Anexar ao processo
session = device.attach("com.vizirbank.frota")
print(f"Session: {session}")
```

## TROUBLESHOOTING

**Erro: "unable to connect to remote frida-server"**
- Verificar: adb shell ps | grep frida-server
- Reiniciar: adb shell /data/local/tmp/frida-server &

**Erro: "Process not found"**
- App não está rodando. Abrir app primeiro

**Erro: "403 Forbidden"**
- Celular pode estar pedindo permissão. Verificar notificações

## ARQUITETURA DO CELULAR
```bash
adb shell getprop ro.product.cpu.abi
# Possíveis: arm64-v8a, armeabi-v7a, x86, x86_64
```

## PORTA CUSTOMIZADA (se necessário)
```bash
adb forward tcp:27042 tcp:27042
adb forward tcp:27043 tcp:27043
```
