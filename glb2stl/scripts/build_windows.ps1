# Local build on Windows (for testing before a release).
# Run from PowerShell:  .\scripts\build_windows.ps1
# Needs Python 3.12; the installer step also needs Inno Setup 6 (winget install JRSoftware.InnoSetup).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path .venv-build)) { py -3.12 -m venv .venv-build }
& .\.venv-build\Scripts\python.exe -m pip install -q --upgrade pip
& .\.venv-build\Scripts\python.exe -m pip install -q -r requirements-gui.txt pyinstaller pillow
& .\.venv-build\Scripts\pyinstaller.exe --noconfirm glb2stl.spec

$version = (Select-String -Path glb2stl\__init__.py -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (Test-Path $iscc) {
    & $iscc "/DAppVersion=$version" installer\glb2stl.iss
    Write-Host "`nInstaller: dist\glb2stl-v$version-windows-setup.exe"
} else {
    Write-Host "`nInno Setup not found: skipping the installer (winget install JRSoftware.InnoSetup)"
}
Write-Host "Portable:  dist\glb2stl-portable.exe"
Write-Host "Folder:    dist\glb2stl\glb2stl.exe"
