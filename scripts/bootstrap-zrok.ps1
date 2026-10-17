# Enable a zrok environment in a temp ZROK2_HOME and print it as one base64 string for a GitHub secret.
# Works in Windows PowerShell and in pwsh on Windows, Linux and macOS. Your real ~/.zrok2 is never read or changed.
param(
    [Parameter(Mandatory)][string]$Token,
    [string]$Description = 'ziti-hook github action'
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command zrok2 -ErrorAction SilentlyContinue)) { throw 'zrok2 is not on PATH' }

$home2 = Join-Path ([IO.Path]::GetTempPath()) ("zrok2-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $home2 | Out-Null
$oldHome = $env:ZROK2_HOME
try {
    $env:ZROK2_HOME = $home2
    & zrok2 enable --headless -d $Description $Token | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "zrok2 enable failed with exit code $LASTEXITCODE" }

    $files = Get-ChildItem -File $home2 | ForEach-Object Name
    if (-not $files) { throw "zrok2 enable wrote no files to $home2" }
    $tgz = Join-Path ([IO.Path]::GetTempPath()) ("zrok2-" + [guid]::NewGuid().ToString('N') + '.tgz')
    & tar -czf $tgz -C $home2 @files
    if ($LASTEXITCODE -ne 0) { throw 'tar failed' }
    $blob = [Convert]::ToBase64String([IO.File]::ReadAllBytes($tgz))
    Remove-Item $tgz -Force
}
finally {
    $env:ZROK2_HOME = $oldHome
    Remove-Item -Recurse -Force $home2 -ErrorAction SilentlyContinue
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
