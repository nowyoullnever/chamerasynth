param(
    [string]$Source = "references\Project-Sirius\Original_Firmware.bin"
)
$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$ghidra = Join-Path $root 'work\ghidra\ghidra_12.2_PUBLIC'
$jdk = Join-Path $root 'work\jdk25\jdk-25.0.5+8'
$input = Join-Path $root 'work\ghidra\input\Original_Firmware.payload.bin'
$metadata = Join-Path $root 'work\ghidra\input\payload-mapping.json'
$project = Join-Path $root 'work\ghidra\projects'
$exports = Join-Path $root 'work\ghidra\exports'
$scripts = Join-Path $root 'ghidra_scripts'
if (-not (Test-Path (Join-Path $ghidra 'support\analyzeHeadless.bat'))) { throw 'Ghidra 12.2 is not installed under work/ghidra.' }
if (-not (Test-Path (Join-Path $jdk 'bin\java.exe'))) { throw 'JDK 25 is not installed under work/jdk25.' }
$env:JAVA_HOME = $jdk
python tools\prepare_ghidra_payload.py $Source $input $metadata
New-Item -ItemType Directory -Force -Path $project,$exports | Out-Null
& (Join-Path $ghidra 'support\analyzeHeadless.bat') $project CharmeraA32 `
  -import $input -overwrite -loader BinaryLoader -loader-baseAddr 0x0 -processor 'ARM:LE:32:v4t' `
  -analysisTimeoutPerFile 900 -scriptPath $scripts -preScript SeedCharmeraFunctions.java `
  -postScript ExportCharmeraAnalysis.java $exports -log (Join-Path $root 'work\ghidra\analysis.log')
if ($LASTEXITCODE -ne 0) { throw "analyzeHeadless failed: $LASTEXITCODE" }
