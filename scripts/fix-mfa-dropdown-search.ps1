[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$MfaDirectory,
    [string]$CecilPath,
    [switch]$BuildOnly,
    [switch]$Restore
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$originalHash = 'E025C9F5138F1751039F56FBDAB0F2746A99A131C7846A21B12E321B647BFD2D'
$appDirectory = (Resolve-Path -LiteralPath $MfaDirectory).Path
$library = Join-Path $appDirectory 'libs\SukiUI.dll'
$controls = Join-Path $appDirectory 'libs\Avalonia.Controls.dll'
$backup = Join-Path $appDirectory 'backup\MaaUma-search-fix\SukiUI.dll'

if (-not $BuildOnly) {
    $appExe = Join-Path $appDirectory 'MFAAvalonia.exe'
    $running = @(Get-Process -Name MFAAvalonia -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -eq $appExe })
    if ($running.Count) { throw 'Close MFAAvalonia before installing or restoring the search fix.' }
}
if ($Restore) {
    if ($BuildOnly) { throw 'Restore and BuildOnly cannot be combined.' }
    if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $originalHash) {
        throw 'The original-library backup does not match the supported MFA 2.15.2 build.'
    }
    Copy-Item -LiteralPath $backup -Destination $library -Force
    Write-Output 'Restored the original SukiUI.dll. Restart MFAAvalonia.'
    return
}

$dotnet = (Get-Command dotnet -ErrorAction Stop).Source
$sdks = @(& $dotnet --list-sdks | ForEach-Object {
    if ($_ -match '^([0-9.]+) \[(.+)\]$') {
        [pscustomobject]@{ Version = [version]$Matches[1]; Root = $Matches[2] }
    }
} | Sort-Object Version -Descending)
if (-not $sdks.Count -or $sdks[0].Version.Major -lt 8) { throw '.NET SDK 8 or newer is required.' }
$sdk = $sdks[0]
$compiler = Join-Path $sdk.Root "$($sdk.Version)\Roslyn\bincore\csc.dll"
$dotnetRoot = Split-Path -Parent $sdk.Root
$referencePacks = @(Get-ChildItem -LiteralPath (Join-Path $dotnetRoot 'packs\Microsoft.NETCore.App.Ref') -Directory |
    Where-Object { ([version]$_.Name).Major -eq $sdk.Version.Major } |
    Sort-Object { [version]$_.Name } -Descending)
if (-not $referencePacks.Count) { throw 'The SDK reference pack is missing.' }
$referenceDirectory = Join-Path $referencePacks[0].FullName "ref\net$($sdk.Version.Major).0"
if (-not $CecilPath) {
    $cecilCandidates = @(Get-ChildItem -Path (Join-Path $env:USERPROFILE '.nuget\packages\mono.cecil\*\lib\netstandard2.0\Mono.Cecil.dll') -File -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending)
    if (-not $cecilCandidates.Count) { throw 'Supply -CecilPath pointing to Mono.Cecil.dll (0.11.x, netstandard2.0).' }
    $CecilPath = $cecilCandidates[0].FullName
}
$CecilPath = (Resolve-Path -LiteralPath $CecilPath).Path
$projectRoot = Split-Path -Parent $PSScriptRoot
$buildDirectory = Join-Path $projectRoot 'debug\mfa-search-patch'
New-Item -Path $buildDirectory -ItemType Directory -Force | Out-Null
$tool = Join-Path $buildDirectory 'PatchSearch.dll'
$patched = Join-Path $buildDirectory 'SukiUI.patched.dll'
$response = Join-Path $buildDirectory 'compile.rsp'
$source = Join-Path $PSScriptRoot 'mfa-search-fix\PatchSearch.cs'
$compilerArgs = @('/nologo', '/target:exe', "/out:`"$tool`"", "/r:`"$CecilPath`"") +
    @(Get-ChildItem -LiteralPath $referenceDirectory -Filter '*.dll' | ForEach-Object { "/r:`"$($_.FullName)`"" }) +
    @("`"$source`"")
Set-Content -LiteralPath $response -Value $compilerArgs -Encoding UTF8
& $dotnet $compiler "@$response"
if ($LASTEXITCODE -ne 0) { throw 'Search-patch compiler failed.' }
Copy-Item -LiteralPath $CecilPath -Destination (Join-Path $buildDirectory 'Mono.Cecil.dll') -Force
@{ runtimeOptions = @{ tfm = "net$($sdk.Version.Major).0";
    framework = @{ name = 'Microsoft.NETCore.App'; version = "$($sdk.Version.Major).0.0" } } } |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $buildDirectory 'PatchSearch.runtimeconfig.json') -Encoding UTF8
& $dotnet $tool $library $controls $patched
if ($LASTEXITCODE -ne 0) { throw 'Search-patch generation failed; the installed DLL was not changed.' }
if ($BuildOnly) {
    Write-Output "Built: $patched"
    return
}
if (Test-Path -LiteralPath $backup) {
    if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $originalHash) {
        throw 'A different backup already exists; refusing to overwrite it.'
    }
} else {
    New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
    Copy-Item -LiteralPath $library -Destination $backup
}
Copy-Item -LiteralPath $patched -Destination $library -Force
Write-Output 'Installed the search fix. Restart MFAAvalonia.'
