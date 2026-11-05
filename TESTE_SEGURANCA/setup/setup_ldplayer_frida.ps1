# Setup Frida no LDPlayer - automatiza install + start do frida-server
# Executar: powershell -ExecutionPolicy Bypass -File setup_ldplayer_frida.ps1

$ErrorActionPreference = "Continue"

Write-Host "============================================"
Write-Host "  Setup Frida no LDPlayer"
Write-Host "============================================"
Write-Host ""

# 1. Detectar adb
$adbPath = ""
$candidates = @(
    "C:\LDPlayer\LDPlayer9\adb.exe",
    "C:\LDPlayer\LDPlayer\adb.exe",
    "C:\XuanZhi\LDPlayer9\adb.exe",
    "adb"
)
foreach ($c in $candidates) {
    try {
        $null = & $c version 2>&1
        if ($LASTEXITCODE -eq 0 -or $?) {
            $adbPath = $c
            Write-Host "[+] adb encontrado: $c"
            break
        }
    } catch {}
}

if (-not $adbPath) {
    Write-Host "[-] adb nao encontrado. Instala Android Platform Tools ou usa o do LDPlayer." -ForegroundColor Red
    Write-Host "    LDPlayer costuma ter em: C:\LDPlayer\LDPlayer9\adb.exe"
    exit 1
}

# 2. Conectar LDPlayer
Write-Host ""
Write-Host "[*] Conectando ao LDPlayer (127.0.0.1:5555)..."
& $adbPath connect 127.0.0.1:5555
Start-Sleep -Seconds 2

# 3. Verificar conexao e root
Write-Host ""
Write-Host "[*] Testando conexao..."
$deviceId = & $adbPath shell "echo CONECTADO" 2>&1
if ($deviceId -notmatch "CONECTADO") {
    Write-Host "[-] Nao conectou. Verifica se LDPlayer esta aberto." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Conectado"

Write-Host ""
Write-Host "[*] Testando root..."
$rootTest = & $adbPath shell "su -c id" 2>&1
if ($rootTest -match "uid=0") {
    Write-Host "[+] Root OK"
} else {
    Write-Host "[!] Root pode nao estar ativado no LDPlayer." -ForegroundColor Yellow
    Write-Host "    Ative em: Config -> Advanced settings -> Root permission"
}

# 4. Push frida-server x86
$fridaX86 = "C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\setup\frida-server-16.0.19-android-x86"
if (-not (Test-Path $fridaX86)) {
    Write-Host "[-] frida-server x86 nao encontrado em: $fridaX86" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[*] Enviando frida-server..."
& $adbPath push $fridaX86 /data/local/tmp/frida-server
& $adbPath shell "chmod 755 /data/local/tmp/frida-server"
Write-Host "[+] frida-server enviado"

# 5. Verificar se ja esta rodando e matar
Write-Host ""
Write-Host "[*] Matando instancias antigas..."
& $adbPath shell "su -c 'pkill -f frida-server'" 2>&1 | Out-Null

# 6. Rodar frida-server em background
Write-Host ""
Write-Host "[*] Iniciando frida-server..."
Start-Job -ScriptBlock {
    param($adb)
    & $adb shell "su -c '/data/local/tmp/frida-server'"
} -ArgumentList $adbPath | Out-Null

Start-Sleep -Seconds 3

# 7. Validar com frida-ps
Write-Host ""
Write-Host "[*] Validando (frida-ps -U)..."
try {
    $fridaCheck = & frida-ps -U 2>&1 | Select-Object -First 10
    Write-Host $fridaCheck
    Write-Host ""
    Write-Host "[+] Frida OK se listou processos acima."
} catch {
    Write-Host "[-] frida-tools nao instalado no PC." -ForegroundColor Yellow
    Write-Host "    Instala: py -3.14 -m pip install frida-tools frida==16.0.19"
}

# 8. Verificar APK Frotabank
Write-Host ""
Write-Host "[*] Verificando se Frotabank esta instalado..."
$frotaCheck = & $adbPath shell "pm list packages | grep frotabank" 2>&1
if ($frotaCheck -match "frotabank") {
    Write-Host "[+] Frotabank instalado: $frotaCheck"
} else {
    Write-Host "[!] Frotabank NAO instalado." -ForegroundColor Yellow
    Write-Host "    Instala com: $adbPath install C:\caminho\para\Frotabank.apk"
}

Write-Host ""
Write-Host "============================================"
Write-Host "  Setup concluido!"
Write-Host ""
Write-Host "  Proximo passo: rodar o script de captura"
Write-Host "    cd C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\scripts_frida"
Write-Host "    python 00_run_frida.py 09_capture_post_user.js"
Write-Host "============================================"
