$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$AppName = "GPT-Regeister"
$IconPath = "gui\openai.ico"

if (-not (Test-Path $IconPath)) {
    throw "Icon file not found: $IconPath"
}

python -m pip show pyinstaller *> $null
if ($LASTEXITCODE -ne 0) {
    python -m pip install pyinstaller
}

Remove-Item -Recurse -Force ".\build", ".\dist" -ErrorAction SilentlyContinue
Remove-Item -Force ".\$AppName.spec" -ErrorAction SilentlyContinue

pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name $AppName `
  --contents-directory . `
  --icon $IconPath `
  --add-data "gui\openai.ico;gui" `
  --add-data "sentinel;sentinel" `
  --add-data "node;node" `
  run_gui.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed"
}

$OutputDir = Join-Path $ProjectRoot "dist\$AppName"
$ZipPath = Join-Path $ProjectRoot "dist\$AppName.zip"

if (Test-Path $ZipPath) {
    Remove-Item -Force $ZipPath
}
Compress-Archive -Path $OutputDir -DestinationPath $ZipPath -Force

$ExePath = Join-Path $OutputDir "$AppName.exe"

Write-Host ""
Write-Host "Build completed: $OutputDir"
Write-Host "Zip package: $ZipPath"
Write-Host "Executable: $ExePath"
