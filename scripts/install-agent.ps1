param(
    [string]$ProjectDirectory = (Join-Path $PSScriptRoot '..\assets'),
    [string]$PythonExecutable = 'python'
)

$ErrorActionPreference = 'Stop'
$projectPath = (Resolve-Path -LiteralPath $ProjectDirectory).Path
$agentPath = Join-Path $projectPath 'agent'
$requirementsPath = Join-Path $agentPath 'requirements.txt'
if (-not (Test-Path -LiteralPath $requirementsPath)) {
    throw "找不到 $requirementsPath，请先复制 assets/agent 到目标目录。"
}

# Each deployment gets its own venv. Do not copy a venv between directories.
$venvPath = Join-Path $agentPath '.venv'
& $PythonExecutable -m venv $venvPath
if ($LASTEXITCODE -ne 0) { throw '创建 Python 虚拟环境失败，需要 Python 3.9+（64 位）。' }
$agentPython = Join-Path $venvPath 'Scripts\python.exe'
& $agentPython -m pip install --only-binary=:all: -r $requirementsPath
if ($LASTEXITCODE -ne 0) { throw 'Agent 依赖安装失败，请检查网络后重试。' }
Write-Host "Agent 运行环境已准备好：$agentPython"
