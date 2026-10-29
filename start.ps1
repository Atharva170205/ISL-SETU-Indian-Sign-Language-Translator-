# ISL Setu - One-click startup script

$root = "D:\ISL_Setu"

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -like "*Wi-Fi*" -and $_.IPAddress -notlike "169.*"
}).IPAddress | Select-Object -First 1

Write-Host "Detected IP: $ip" -ForegroundColor Cyan

$certFile = Get-ChildItem "$root\certs" -Filter "*-key.pem" -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $certFile) {
    Write-Host "ERROR: No cert file found in $root\certs - cannot start backend with HTTPS." -ForegroundColor Red
    Write-Host "Generate certs first with mkcert, then re-run this script." -ForegroundColor Red
    pause
    exit 1
}

$certIp = $certFile.Name -replace '\+2-key\.pem$', ''
if ($certIp -ne $ip) {
    Write-Host "================================================" -ForegroundColor Red
    Write-Host " WARNING: IP changed since certs were generated!" -ForegroundColor Red
    Write-Host " Cert IP:    $certIp" -ForegroundColor Red
    Write-Host " Current IP: $ip" -ForegroundColor Red
    Write-Host " Regenerate certs:" -ForegroundColor Yellow
    Write-Host "   cd $root\certs" -ForegroundColor Yellow
    Write-Host "   .\mkcert.exe $ip localhost 127.0.0.1" -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Red
    Start-Sleep -Seconds 5
}

$keyPath = $certFile.FullName
$pemPath = $keyPath -replace '-key\.pem$', '.pem'

if (-not (Test-Path $pemPath)) {
    Write-Host "ERROR: Found key file but matching cert file not found: $pemPath" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Using cert: $pemPath" -ForegroundColor Cyan
Write-Host "Using key:  $keyPath" -ForegroundColor Cyan

$backendCmd = "cd '$root'; .\venv311\Scripts\Activate.ps1; uvicorn services.backend.main:app --host 0.0.0.0 --port 8000 --reload --ssl-keyfile `"$keyPath`" --ssl-certfile `"$pemPath`""

Write-Host "Starting backend (HTTPS)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

Write-Host "Starting frontend..." -ForegroundColor Cyan
$frontendCmd = "cd '$root\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host " ISL Setu is starting up!" -ForegroundColor Green
Write-Host " Backend:  https://${ip}:8000" -ForegroundColor Green
Write-Host " Frontend: https://${ip}:5173" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

Start-Process "https://${ip}:5173"