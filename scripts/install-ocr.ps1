param(
    [Parameter(Mandatory = $true)]
    [string]$ModelDirectory,
    [string]$Destination = (Join-Path $PSScriptRoot '..\assets\resource\model\ocr')
)

$ErrorActionPreference = 'Stop'
$files = @('det.onnx', 'rec.onnx', 'keys.txt')
$modelRoot = (Resolve-Path -LiteralPath $ModelDirectory).Path
foreach ($name in $files) {
    $source = Join-Path $modelRoot $name
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Missing OCR file: $source"
    }
    if ((Get-Item -LiteralPath $source).Length -eq 0) {
        throw "Empty OCR file: $source"
    }
}

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
foreach ($name in $files) {
    Copy-Item -LiteralPath (Join-Path $modelRoot $name) -Destination (Join-Path $Destination $name) -Force
}
Get-ChildItem -LiteralPath $Destination | Where-Object { $_.Name -in $files } | Select-Object Name, Length
