# ##########################################################
# FlatCAM Plus - Versiyon Guncelleme Yardimcisi
# Cagrilir: update_version.ps1 -Version "1.2.3" -RootDir "..."
# ##########################################################

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Version,

    [Parameter(Mandatory = $true)]
    [string] $RootDir
)

$ErrorActionPreference = "Stop"

# Windows PowerShell 5.1 writes a BOM with [System.Text.Encoding]::UTF8, and tomllib rejects it.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# ---- pyproject.toml is the single source of truth for the version ----
$releaseDate = Get-Date -Format "yyyy.MM.dd"
$pyprojectFile = Join-Path $RootDir "pyproject.toml"

if (-not (Test-Path $pyprojectFile)) {
    throw "Dosya bulunamadi: $pyprojectFile"
}

$content = Get-Content $pyprojectFile -Raw -Encoding UTF8
$content = $content -replace '(?m)^version\s*=\s*"[^"]*"', "version = `"$Version`""
[System.IO.File]::WriteAllText($pyprojectFile, $content, $utf8NoBom)
Write-Host "[OK] pyproject.toml guncellendi: $Version"

# ---- flatcam_plus/version.py only carries the release date ----
$versionFile = Join-Path $RootDir "flatcam_plus\version.py"

if (-not (Test-Path $versionFile)) {
    throw "Dosya bulunamadi: $versionFile"
}

$content = Get-Content $versionFile -Raw -Encoding UTF8
$content = $content -replace 'APP_VERSION_DATE\s*=\s*"[^"]*"', "APP_VERSION_DATE = `"$releaseDate`""
[System.IO.File]::WriteAllText($versionFile, $content, $utf8NoBom)
Write-Host "[OK] flatcam_plus/version.py guncellendi: release date $releaseDate"

# ---- FlatCAMPlus.iss ----
$issFile = Join-Path $RootDir "packaging\windows\FlatCAMPlus.iss"

if (-not (Test-Path $issFile)) {
    Write-Warning "FlatCAMPlus.iss bulunamadi, atlanıyor: $issFile"
} else {
    $issContent = Get-Content $issFile -Raw -Encoding UTF8
    $issContent = $issContent -replace '#define AppVersion\s+"[^"]*"', "#define AppVersion `"$Version`""
    [System.IO.File]::WriteAllText($issFile, $issContent, $utf8NoBom)
    Write-Host "[OK] FlatCAMPlus.iss guncellendi: $Version"
}

Write-Host ""
Write-Host "Versiyon guncelleme tamamlandi: $Version"
