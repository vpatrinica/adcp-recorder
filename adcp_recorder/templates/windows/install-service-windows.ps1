# ADCP Recorder - Windows Service Installation Script using Servy
# 
# This PowerShell script installs the ADCP Recorder as a Windows service using Servy.
# Must be run as Administrator.
#
# Usage:
#   .\install-service-windows.ps1
#

# Require Administrator privileges
#Requires -RunAsAdministrator

Write-Host "========================================" -ForegroundColor Green
Write-Host "ADCP Recorder - Windows Service Setup" -ForegroundColor Green
Write-Host "(Using Servy Service Manager)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Configuration
$InstallDir = "C:\Program Files\ADCP-Recorder"
$VenvPath = Join-Path $InstallDir "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$DataDir = "C:\ADCP_Data"
$LogDir = Join-Path $DataDir "logs"
$ServiceName = "ADCPRecorder"
$ServiceDisplayName = "ADCP Recorder Service"
$ServiceDescription = "NMEA Telemetry Recorder for Nortek ADCP Instruments"

# Step 1: Check if Python is installed
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python not found at $PythonExe" -ForegroundColor Red
    Write-Host "Please run install-windows.bat first to install the package" -ForegroundColor Red
    exit 1
}

$PythonVersion = & $PythonExe --version 2>&1
Write-Host "Python: $PythonVersion" -ForegroundColor Green
Write-Host ""

# Step 2: Check/Install Servy
Write-Host "[2/6] Checking Servy installation..." -ForegroundColor Yellow

$ServyInstalled = $false
try {
    $null = & servy-cli --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ServyInstalled = $true
        Write-Host "Servy is installed" -ForegroundColor Green
    }
} catch {
    $ServyInstalled = $false
}

if (-not $ServyInstalled) {
    Write-Host "Installing Servy via winget..." -ForegroundColor Yellow
    
    # Check if winget is available
    try {
        $null = & winget --version 2>&1
    } catch {
        Write-Host "ERROR: winget not found" -ForegroundColor Red
        Write-Host "Please install Servy manually from: https://github.com/aelassas/servy/releases" -ForegroundColor Red
        exit 1
    }
    
    & winget install -e --id aelassas.Servy --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Servy installation may have failed" -ForegroundColor Yellow
        Write-Host "Please install Servy manually from: https://github.com/aelassas/servy/releases" -ForegroundColor Yellow
    }
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Verify Servy is available
    try {
        $null = & servy-cli --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "servy-cli not found"
        }
    } catch {
        Write-Host "ERROR: Servy CLI not found after installation" -ForegroundColor Red
        Write-Host "Please restart PowerShell and try again" -ForegroundColor Red
        exit 1
    }
    Write-Host "Servy installed successfully" -ForegroundColor Green
}
Write-Host ""

# Step 3: Create log directory
Write-Host "[3/6] Setting up directories..." -ForegroundColor Yellow

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "Created log directory: $LogDir" -ForegroundColor Green
} else {
    Write-Host "Log directory exists: $LogDir" -ForegroundColor Green
}
Write-Host ""

# Step 4: Check if service already exists
Write-Host "[4/6] Checking existing service..." -ForegroundColor Yellow

try {
    $StatusResult = & servy-cli status --name="$ServiceName" --quiet 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service already exists. Stopping and removing..." -ForegroundColor Yellow
        
        & servy-cli stop --name="$ServiceName" --quiet 2>&1
        Start-Sleep -Seconds 2
        
        & servy-cli uninstall --name="$ServiceName" --quiet
        Start-Sleep -Seconds 2
        Write-Host "Existing service removed" -ForegroundColor Green
    }
} catch {
    # Service doesn't exist, which is fine
}

# Also check via Windows services in case it was installed via pywin32 previously
$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($ExistingService) {
    Write-Host "Found legacy Windows service. Removing..." -ForegroundColor Yellow
    
    if ($ExistingService.Status -eq 'Running') {
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
    }
    
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
    Write-Host "Legacy service removed" -ForegroundColor Green
}
Write-Host ""

# Step 5: Install service via Servy
Write-Host "[5/6] Installing Windows service via Servy..." -ForegroundColor Yellow

$StdoutLog = Join-Path $LogDir "stdout.log"
$StderrLog = Join-Path $LogDir "stderr.log"

& servy-cli install --quiet `
    --name="$ServiceName" `
    --displayName="$ServiceDisplayName" `
    --description="$ServiceDescription" `
    --path="$PythonExe" `
    --startupDir="$InstallDir" `
    --params="-m adcp_recorder.service.supervisor" `
    --startupType="Automatic" `
    --priority="Normal" `
    --stdout="$StdoutLog" `
    --stderr="$StderrLog" `
    --enableDateRotation `
    --dateRotationType="Daily" `
    --maxRotations=30 `
    --enableHealth `
    --heartbeatInterval=30 `
    --maxFailedChecks=3 `
    --recoveryAction="RestartService" `
    --maxRestartAttempts=5 `
    --stopTimeout=10

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Service installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "Service installed via Servy" -ForegroundColor Green
Write-Host ""

# Step 6: Start service
Write-Host "[6/6] Starting service..." -ForegroundColor Yellow

$StartService = Read-Host "Start service now? (Y/N)"
if ($StartService -eq 'Y' -or $StartService -eq 'y') {
    & servy-cli start --name="$ServiceName" --quiet
    Start-Sleep -Seconds 2
    
    $StatusOutput = & servy-cli status --name="$ServiceName" --quiet 2>&1
    if ($StatusOutput -match "Running") {
        Write-Host "Service started successfully" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Service may not have started correctly" -ForegroundColor Red
        Write-Host "Status: $StatusOutput" -ForegroundColor Yellow
        Write-Host "Check logs at: $LogDir" -ForegroundColor Yellow
    }
} else {
    Write-Host "Service not started" -ForegroundColor Yellow
}
Write-Host ""

# Display service information
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service Information:" -ForegroundColor Cyan
Write-Host "  Name:        $ServiceName"
Write-Host "  Display:     $ServiceDisplayName"
Write-Host "  Start Type:  Automatic"
Write-Host "  Logs:        $LogDir"
Write-Host ""
Write-Host "Servy Management Commands:" -ForegroundColor Cyan
Write-Host "  Start:       servy-cli start --name=`"$ServiceName`""
Write-Host "  Stop:        servy-cli stop --name=`"$ServiceName`""
Write-Host "  Restart:     servy-cli restart --name=`"$ServiceName`""
Write-Host "  Status:      servy-cli status --name=`"$ServiceName`""
Write-Host ""
Write-Host "Or use Windows service commands:" -ForegroundColor Cyan
Write-Host "  Start:       Start-Service -Name $ServiceName"
Write-Host "  Stop:        Stop-Service -Name $ServiceName"
Write-Host "  Status:      Get-Service -Name $ServiceName"
Write-Host ""
Write-Host "Log files:" -ForegroundColor Cyan
Write-Host "  stdout:      $StdoutLog"
Write-Host "  stderr:      $StderrLog"
Write-Host ""
