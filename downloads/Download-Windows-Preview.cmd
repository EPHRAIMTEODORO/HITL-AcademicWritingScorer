@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "HITL_PREVIEW_FOLDER=%~dp0"
echo HITL Academic Writing Scorer 0.1.4 - EXPERIMENTAL PREVIEW
echo This unfinished app may contain bugs, crashes, and incorrect scores.
echo This helper downloads and verifies the installer files; it does not install the app.
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; try { $folder=$env:HITL_PREVIEW_FOLDER; $script=Join-Path $folder 'Prepare-Windows-Preview.ps1'; $expected='8acc8754702dd86c54624280cf0309e88cb6def2cacb52709d8a863b3885e576'; $verify={param($p) $s=[IO.File]::OpenRead($p); $a=[Security.Cryptography.SHA256]::Create(); try { $h=[BitConverter]::ToString($a.ComputeHash($s)).Replace('-','').ToLowerInvariant(); if($h -ne $expected){throw 'The preparation helper failed verification. Move it out of this folder and download the helper again.'} } finally {$s.Dispose(); $a.Dispose()} }; if(Test-Path -LiteralPath $script){ & $verify $script } else { [Net.ServicePointManager]::SecurityProtocol=[Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; $temporary=$script+'.'+[guid]::NewGuid().ToString('N')+'.download'; try { Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/EPHRAIMTEODORO/HITL-AcademicWritingScorer/releases/download/windows-v0.1.4-preview/Prepare-Windows-Preview.ps1' -OutFile $temporary -TimeoutSec 120; & $verify $temporary; Move-Item -LiteralPath $temporary -Destination $script } finally { if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary} } }; & $script -Destination $folder } catch { Write-Host ('Preparation failed: '+$_.Exception.Message) -ForegroundColor Red; exit 1 }"
set "HITL_PREVIEW_RESULT=%ERRORLEVEL%"
echo.
if not "%HITL_PREVIEW_RESULT%"=="0" echo The installer is not ready. Read the message above and try again.
if /I "%~1"=="--no-pause" goto done
pause
:done
exit /b %HITL_PREVIEW_RESULT%
