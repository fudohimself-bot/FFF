# Downloads every free tool the Gojo in Elden Ring plan needs into one folder (D:\GojoMod\tools by default).
# It only downloads and unzips. It does not touch either game's files.
# Run it with get_tools.bat (double-click), or: powershell -ExecutionPolicy Bypass -File get_tools.ps1
param([string]$Root = "D:\GojoMod")

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # makes Invoke-WebRequest much faster
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Tools = Join-Path $Root "tools"
New-Item -ItemType Directory -Force -Path $Tools | Out-Null

function Get-File($Url, $Dest) {
  Write-Host "  downloading $Url"
  Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing -Headers @{ "User-Agent" = "gojo-elden-ring" }
}

function Expand-Any($Archive, $Dest) {
  New-Item -ItemType Directory -Force -Path $Dest | Out-Null
  if ($Archive -like "*.zip") { Expand-Archive -Path $Archive -DestinationPath $Dest -Force }
  else { tar -xf $Archive -C $Dest }   # .7z and .rar: Windows 10/11's tar can read these
}

# Latest GitHub release of each tool. Keep = leave the archive zipped (Blender installs add-ons from the zip).
$GitHubTools = @(
  @{ Name = "FModel";             Repo = "4sval/FModel" },
  @{ Name = "Soulstruct-Blender"; Repo = "Grimrukh/soulstruct-blender"; Keep = $true },
  @{ Name = "UXM";                Repo = "Nordgaren/UXM-Selective-Unpack" },
  @{ Name = "Smithbox";           Repo = "vawser/Smithbox" },
  @{ Name = "ModEngine2";         Repo = "soulsmods/ModEngine2" },
  @{ Name = "WitchyBND";          Repo = "ividyon/WitchyBND" },
  @{ Name = "DSAnimStudio";       Repo = "Meowmaritus/DSAnimStudio" },
  @{ Name = "ERClipGeneratorTool";Repo = "The12thAvenger/ERClipGeneratorTool" }
)

$Failed = @()
foreach ($t in $GitHubTools) {
  Write-Host "== $($t.Name)"
  $Dir = Join-Path $Tools $t.Name
  try {
    $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/$($t.Repo)/releases/latest" -Headers @{ "User-Agent" = "gojo-elden-ring" }
    $assets = @($rel.assets | Where-Object { $_.name -match '\.(zip|7z|rar|exe)$' })
    if ($assets.Count -eq 0) { throw "no downloadable files in release $($rel.tag_name)" }
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
    foreach ($a in $assets) {
      $file = Join-Path $Dir $a.name
      Get-File $a.browser_download_url $file
      if (-not $t.Keep -and $a.name -match '\.(zip|7z|rar)$') {
        Expand-Any $file (Join-Path $Dir ([IO.Path]::GetFileNameWithoutExtension($a.name)))
      }
    }
    Write-Host "  ok: $($rel.tag_name)"
  } catch {
    Write-Host "  FAILED: $_" -ForegroundColor Red
    $Failed += $t.Name
  }
}

# Blender 5.1 or newer is what Soulstruct for Blender needs. This is the portable version: no installer, it runs from the folder.
Write-Host "== Blender 5.1.2 (portable)"
try {
  $zip = Join-Path $Tools "blender-5.1.2-windows-x64.zip"
  Get-File "https://download.blender.org/release/Blender5.1/blender-5.1.2-windows-x64.zip" $zip
  Expand-Any $zip $Tools
  Remove-Item $zip
  Write-Host "  ok: run $Tools\blender-5.1.2-windows-x64\blender.exe"
} catch { Write-Host "  FAILED: $_" -ForegroundColor Red; $Failed += "Blender" }

# FModel needs Cursed Clash's mapping file to read models. Both versions are fetched; try Mappings.usmap first.
Write-Host "== Cursed Clash mapping files (.usmap)"
try {
  $Maps = Join-Path $Tools "usmap"
  New-Item -ItemType Directory -Force -Path $Maps | Out-Null
  foreach ($m in @("Mappings.usmap", "1.01.Mappings.usmap")) {
    Get-File "https://raw.githubusercontent.com/MadMax1960/JJK-CC-Resources/main/$m" (Join-Path $Maps $m)
  }
  Write-Host "  ok: $Maps"
} catch { Write-Host "  FAILED: $_" -ForegroundColor Red; $Failed += "usmap" }

# Check the game folders (read only).
Write-Host ""
foreach ($g in @("D:\steam\steamapps\common\Jujutsu Kaisen CC\Jujutsu Kaisen CC\Content\Paks",
                 "D:\steam\steamapps\common\ELDEN RING\Game\eldenring.exe")) {
  if (Test-Path $g) { Write-Host "found   $g" } else { Write-Host "MISSING $g  (tell me where this game is installed)" -ForegroundColor Yellow }
}

Write-Host ""
if ($Failed.Count -gt 0) { Write-Host "Some downloads failed: $($Failed -join ', '). Screenshot this window and send it." -ForegroundColor Red }
else { Write-Host "All tools are in $Tools" -ForegroundColor Green }
