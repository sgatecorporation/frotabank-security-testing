# Setup mitmproxy + LDPlayer sem Frida
# Executa: configura proxy no LDPlayer e inicia mitmdump capturando pro log

$ErrorActionPreference = "Continue"

$pcIp = "172.20.10.3"  # IP do PC na rede
$proxyPort = 8080

Write-Host "============================================"
Write-Host "  Setup mitmproxy no LDPlayer"
Write-Host "  Proxy: ${pcIp}:${proxyPort}"
Write-Host "============================================"

# 1. Config proxy no LDPlayer
Write-Host ""
Write-Host "[*] Configurando proxy no LDPlayer..."
adb shell "settings put global http_proxy ${pcIp}:${proxyPort}"
Write-Host "[+] Proxy configurado"

# 2. Verificar
$current = adb shell "settings get global http_proxy"
Write-Host "[*] Proxy ativo: $current"

Write-Host ""
Write-Host "============================================"
Write-Host "  AGORA ABRE OUTRA JANELA PS/CMD E RODA:"
Write-Host "    mitmdump -w capture.flows"
Write-Host "  OU:"
Write-Host "    mitmproxy  (interface interativa)"
Write-Host ""
Write-Host "  Depois abre o Frotabank no LDPlayer."
Write-Host "  Pra PARAR o proxy (voltar ao normal):"
Write-Host "    adb shell settings put global http_proxy :0"
Write-Host "============================================"
