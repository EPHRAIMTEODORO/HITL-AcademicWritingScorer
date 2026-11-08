# Prepare the existing Windows 0.1.4 installer; this does not install or launch the app.
[CmdletBinding()]
param([string]$Destination = $PSScriptRoot)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$releaseBase = 'https://github.com/EPHRAIMTEODORO/HITL-AcademicWritingScorer/releases/download/windows-v0.1.4-preview/'
$files = @'
[
  {"name":"7za.exe","size":1231360,"sha256":"b0cfdeaf429f5cc53f85123dd8f5a5feb92c19d31aa34df257edf9a26be05f95"},
  {"name":"HITL-Academic-Writing-Scorer-Setup-0.1.4.exe","size":8704,"sha256":"b1b36b0196c7d2d1bc4c114e8acb0a4d499fa920445b5310d074b4c2cf2e031f"},
  {"name":"hitl-app.7z.001","size":1992294400,"sha256":"b8b8ea36d52dfc76f78e2e0cef7f5d83351967a78dfe27aa2a366d61777f09c9"},
  {"name":"hitl-app.7z.002","size":1992294400,"sha256":"38f3931430ce2242daa96ee4383f07819cfc18fd77f0b7503b6885abe169b13f"},
  {"name":"hitl-app.7z.003","size":1076364920,"sha256":"2d768d85bb9070cd3453cc12b0bdcd22ce432e0eee4d0eff2be243d688a9fbc8"}
]
'@ | ConvertFrom-Json
$payload = [pscustomobject]@{
    name = 'hitl-app.7z'
    size = [long]5060953720
    sha256 = 'd5aa2cc2c0014f0202cbff8653b6727b29988f68ceea96fbe10d7ee95d5094b0'
}

function Assert-Download([string]$FilePath, $Expected) {
    $item = Get-Item -LiteralPath $FilePath
    $stream = [IO.File]::OpenRead($FilePath)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $digest = [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
    } finally {
        $stream.Dispose()
        $algorithm.Dispose()
    }
    if ($item.Length -ne [long]$Expected.size -or
        $digest -ne $Expected.sha256) {
        throw "Verification failed for $($Expected.name). Move the damaged file out of this folder and run the helper again."
    }
}

try {
    Write-Host 'HITL Academic Writing Scorer 0.1.4 - EXPERIMENTAL PREVIEW'
    Write-Host 'This app is unfinished. Bugs, crashes, and incorrect scores may occur.'
    Write-Host 'This helper downloads about 5.06 GB. Allow at least 25 GB of free disk space for preparation, installation, and model storage.'
    Write-Host 'The app will not be installed or launched automatically.'
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $destinationPath = (Resolve-Path -LiteralPath $Destination).Path
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

    foreach ($file in $files) {
        $path = Join-Path $destinationPath $file.name
        if (Test-Path -LiteralPath $path) {
            Write-Host "Checking existing download: $($file.name)"
            Assert-Download $path $file
            continue
        }
        $partial = $path + '.' + [guid]::NewGuid().ToString('N') + '.download'
        try {
            Write-Host "Downloading $($file.name) ($([math]::Round($file.size / 1MB)) MiB)..."
            Invoke-WebRequest -UseBasicParsing -Uri ($releaseBase + [uri]::EscapeDataString($file.name)) -OutFile $partial -TimeoutSec 3600
            Assert-Download $partial $file
            Move-Item -LiteralPath $partial -Destination $path
        } finally {
            if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial }
        }
    }

    $payloadPath = Join-Path $destinationPath $payload.name
    if (Test-Path -LiteralPath $payloadPath) {
        Assert-Download $payloadPath $payload
    } else {
        Write-Host 'Reassembling the three payload parts...'
        $assembled = $payloadPath + '.' + [guid]::NewGuid().ToString('N') + '.assembling'
        try {
            $output = [IO.File]::Open($assembled, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
            try {
                foreach ($part in ($files | Where-Object { $_.name -like 'hitl-app.7z.*' })) {
                    $inputStream = [IO.File]::OpenRead((Join-Path $destinationPath $part.name))
                    try { $inputStream.CopyTo($output) } finally { $inputStream.Dispose() }
                }
            } finally { $output.Dispose() }
            Assert-Download $assembled $payload
            Move-Item -LiteralPath $assembled -Destination $payloadPath
        } finally {
            if (Test-Path -LiteralPath $assembled) { Remove-Item -LiteralPath $assembled }
        }
    }

    Write-Host ''
    Write-Host 'All installer files passed SHA-256 verification.'
    Write-Host "Ready in: $destinationPath"
    Write-Host 'To install, open: HITL-Academic-Writing-Scorer-Setup-0.1.4.exe'
    Write-Host 'Keep the Setup executable, 7za.exe, and hitl-app.7z together. Setup replaces an existing installation.'
} catch {
    Write-Host ''
    Write-Host ('Preparation failed: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
