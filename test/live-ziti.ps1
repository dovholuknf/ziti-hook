# Live OpenZiti test. Starts the listener bound as ziti-hook-test-bind, then sends with ziti-hook-gh.
# Identity files stay where they are. Nothing is printed or copied from them.
param(
    [string]$Python = (Join-Path $PSScriptRoot '..\build.claude\venv\Scripts\python.exe'),
    [string]$IdentityDir = (Join-Path $env:USERPROFILE '.ziti\identities\ziti-hook'),
    [string]$Url = 'http://ziti-hook.ziti/'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
$log = Join-Path $root 'build.claude\listener.log'
$err = Join-Path $root 'build.claude\listener.err'
$secret = [guid]::NewGuid().ToString('N')

$listener = Start-Process -PassThru -NoNewWindow -FilePath $Python -RedirectStandardOutput $log `
    -RedirectStandardError $err -ArgumentList @(
    (Join-Path $PSScriptRoot 'listener.py'), '--identity', (Join-Path $IdentityDir 'ziti-hook-test-bind.json'),
    '--secret', $secret)
$failed = $false
try {
    $deadline = (Get-Date).AddSeconds(30)
    while (-not ((Test-Path $log) -and (Select-String -Path $log -Pattern 'bound service' -Quiet))) {
        if ($listener.HasExited -or (Get-Date) -gt $deadline) { throw "listener did not bind, see $err" }
        Start-Sleep -Milliseconds 500
    }
    Start-Sleep -Seconds 3  # let the controller register the terminator

    function Send($sec) {
        $env:INPUT_TRANSPORT = 'ziti'
        $env:INPUT_URL = $Url
        ${env:INPUT_ZITI-IDENTITY} = Get-Content -Raw (Join-Path $IdentityDir 'ziti-hook-gh.json')
        $env:INPUT_SECRET = $sec
        $env:INPUT_PAYLOAD = '{"hello":"ziti-hook"}'
        & $Python (Join-Path $root 'src\ziti_hook.py') 2>&1 | Out-Host
        $code = $LASTEXITCODE
        Remove-Item "Env:INPUT_ZITI-IDENTITY"
        $code
    }

    Write-Host '--- correct secret, expect HTTP 200'
    if ((Send $secret) -ne 0) { $failed = $true; Write-Host 'FAIL: send with correct secret' }
    Write-Host '--- wrong secret, expect rejection'
    if ((Send 'wrong') -eq 0) { $failed = $true; Write-Host 'FAIL: wrong secret was accepted' }
    if (-not (Select-String -Path $log -Pattern 'received \d+ bytes' -Quiet)) {
        $failed = $true; Write-Host 'FAIL: listener logged no request'
    }
}
finally {
    if (-not $listener.HasExited) { Stop-Process -Id $listener.Id -Force }
}
if ($failed) { Write-Host 'LIVE ZITI TEST FAILED'; exit 1 }
Write-Host 'LIVE ZITI TEST PASSED'
