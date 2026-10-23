$ErrorActionPreference = 'Stop'
try {
    $root = $PSScriptRoot
    $destination = Join-Path $root '.runtime\v1.0.0-windows'
    $exe = Join-Path $destination 'Cut Label.exe'
    if (-not (Test-Path $exe)) {
        Write-Host 'Downloading Cut Label...'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $stage = Join-Path $root ('.runtime\download-' + [Guid]::NewGuid().ToString())
        New-Item -ItemType Directory -Force $stage | Out-Null
        Invoke-WebRequest -UseBasicParsing 'https://github.com/HoangMinhTrong/Cut_Label/releases/download/v1.0.0/Cut-Label-Windows-x64.zip' -OutFile "$stage\app.zip"
        Expand-Archive "$stage\app.zip" -DestinationPath "$stage\app"
        Move-Item "$stage\app" $destination
    }
    $env:CUT_LABEL_DATA_DIR = $root
    & $exe
    exit $LASTEXITCODE
} catch {
    Write-Host "Cannot start: $_"
    Write-Host 'Check Internet access and whether Release v1.0.0 has been published.'
    exit 1
}
