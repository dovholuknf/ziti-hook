# Enable a zrok environment in a temp home and print it as one base64 string for a GitHub secret.
# Works in Windows PowerShell and in pwsh on Windows, Linux and macOS.
# zrok2 keeps its state in ~/.zrok2 and has no override for that folder, so this script points the home variables at a
# temp folder instead. Your real ~/.zrok2 is never read or changed.
param(
    [Parameter(Mandatory)][string]$Token,
    [string]$Description = 'ziti-hook github action'
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command zrok2 -ErrorAction SilentlyContinue)) { throw 'zrok2 is not on PATH' }

$tmp = Join-Path ([IO.Path]::GetTempPath()) ("zrok2-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null
$saved = @{ HOME = $env:HOME; USERPROFILE = $env:USERPROFILE }
try {
    $env:HOME = $tmp
    $env:USERPROFILE = $tmp
    & zrok2 enable --headless -d $Description $Token | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "zrok2 enable failed with exit code $LASTEXITCODE" }
    $state = Join-Path $tmp '.zrok2'
    if (-not (Test-Path $state)) { throw "zrok2 enable wrote nothing to $state" }

    $tgz = Join-Path ([IO.Path]::GetTempPath()) ("zrok2-" + [guid]::NewGuid().ToString('N') + '.tgz')
    & tar -czf $tgz -C $state .
    if ($LASTEXITCODE -ne 0) { throw 'tar failed' }
    $blob = [Convert]::ToBase64String([IO.File]::ReadAllBytes($tgz))
    Remove-Item $tgz -Force
}
finally {
    $env:HOME = $saved.HOME
    $env:USERPROFILE = $saved.USERPROFILE
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}

Write-Host @'

Next steps
1. Add the string printed below to your repo as the secret ZROK_ENV (Settings, Secrets and variables, Actions).
   It grants the access of this environment. Treat it like a password.
2. Create the private share on the machine that runs the receiver, then add its token as the secret ZROK_SHARE_TOKEN.
3. Use the action with transport: zrok, zrok-env: ${{ secrets.ZROK_ENV }}, zrok-share-token: ${{ secrets.ZROK_SHARE_TOKEN }}.
4. To revoke, run "zrok2 disable" for this environment or regenerate the account token.

'@
$blob
