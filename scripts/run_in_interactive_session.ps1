param(
    [Parameter(Mandatory=$true)]
    [string]$WorkDir,
    [string]$ScriptName = "build_sw.py",
    [string]$TaskName = "",
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"
$FullWorkDir = (Resolve-Path $WorkDir).Path
$OutDir = Join-Path $FullWorkDir "out"
if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

# 1. Nombre de Tarea Unico por directorio para evitar colisiones entre proyectos
if ([string]::IsNullOrWhiteSpace($TaskName)) {
    $DirHash = [Math]::Abs($FullWorkDir.ToLower().GetHashCode()).ToString("X8")
    $ActualTaskName = "AG_CAD_$DirHash"
} else {
    $ActualTaskName = $TaskName
}

$BatPath = Join-Path $FullWorkDir "run_build.bat"
if (-not (Test-Path $BatPath)) {
    $BatContent = @"
@echo off
cd /d "%~dp0"
if not exist out mkdir out
set TARGET=build_sw.py
if exist out\run_target.txt set /p TARGET=<out\run_target.txt
"C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe" -u %TARGET% > out\build_log.txt 2>&1
(echo EXIT=%ERRORLEVEL%) >> out\build_log.txt
"@
    Set-Content -Path $BatPath -Value $BatContent -Encoding ASCII
}

$LogPath = Join-Path $OutDir "build_log.txt"
$TargetFile = Join-Path $OutDir "run_target.txt"
Remove-Item $LogPath -ErrorAction SilentlyContinue
if ($ScriptName -ne "build_sw.py") {
    if (Test-Path $ScriptName) {
        $NormalizedScript = (Resolve-Path $ScriptName).Path
    } else {
        $Candidate = Join-Path $FullWorkDir $ScriptName
        if (Test-Path $Candidate) {
            $NormalizedScript = (Resolve-Path $Candidate).Path
        } else {
            $NormalizedScript = $ScriptName.Replace('/', '\')
        }
    }
    Set-Content -Path $TargetFile -Value "`"$NormalizedScript`"`r`n" -Encoding ASCII
} else {
    Remove-Item $TargetFile -ErrorAction SilentlyContinue
}

try {
    # 2. Registrar tarea programada interactiva 100% invisible (Subsystem GUI via wscript.exe + SW_HIDE)
    # Al invocar wscript.exe (GUI nativo de Windows), el kernel NUNCA abre ninguna consola conhost/cmd en el monitor.
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $SilentVbs = Join-Path $ScriptDir "run_silent.vbs"
    if (-not (Test-Path $SilentVbs)) {
        $SilentVbs = "c:\Users\USER\OneDrive - CAD Automation\Documentos\ISO_tracker\.agents\skills\solidworks-parametric-cad\scripts\run_silent.vbs"
    }

    $Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "//B //Nologo `"$SilentVbs`" `"$BatPath`"" -WorkingDirectory $FullWorkDir
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    $Settings = New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $ActualTaskName -Action $Action -Principal $Principal -Settings $Settings -Force | Out-Null

    Start-ScheduledTask -TaskName $ActualTaskName

    $Elapsed = 0
    $ExitCode = 1
    $Finished = $false
    while ($Elapsed -lt $TimeoutSeconds) {
        Start-Sleep -Seconds 2
        $Elapsed += 2
        if (Test-Path $LogPath) {
            $Content = Get-Content $LogPath -Raw -ErrorAction SilentlyContinue
            if ($Content -match "EXIT=(\d+)") {
                Write-Output $Content
                $ExitCode = [int]$Matches[1]
                $Finished = $true
                break
            }
        }
    }

    if (-not $Finished) {
        Write-Error "Timeout esperando que finalice la tarea interactiva de SolidWorks '$ActualTaskName' ($TimeoutSeconds s)."
        exit 1
    }

    # 3. Limpieza automatica de BMPs convirtiendo a PNG para evitar saturar disco
    python -c "from PIL import Image; import glob, os; [Image.open(p).save(p[:-4]+'.png') or os.remove(p) for p in glob.glob(r'$OutDir/*.bmp')]" 2>$null

    # 4. Limpieza de journal pesado de SolidWorks si existe
    $SwJournal = Join-Path $FullWorkDir "swxJRNL.swj"
    if (Test-Path $SwJournal) {
        $jSize = (Get-Item $SwJournal).Length
        if ($jSize -gt 50MB) {
            Remove-Item $SwJournal -Force -ErrorAction SilentlyContinue
        }
    }

    exit $ExitCode
}
finally {
    # 5. Garantia de Desregistro: NUNCA dejar tareas programadas huerfanas activas
    Unregister-ScheduledTask -TaskName $ActualTaskName -Confirm:$false -ErrorAction SilentlyContinue
}
