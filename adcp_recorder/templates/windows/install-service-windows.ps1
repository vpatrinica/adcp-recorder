# ADCP Recorder - Windows Service Installation Script
# 
# This PowerShell script installs the ADCP Recorder as a Windows service.
# Must be run as Administrator.
#
# Usage:
#   .\install-service-windows.ps1
#

# Require Administrator privileges
#Requires -RunAsAdministrator

Write-Host "========================================" -ForegroundColor Green
Write-Host "ADCP Recorder - Windows Service Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Configuration
$InstallDir = "C:\Program Files\ADCP-Recorder"
$VenvPath = Join-Path $InstallDir "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$ServiceName = "adcp-recorder"
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

# Step 2: Check if pywin32 is installed
Write-Host "[2/6] Checking pywin32..." -ForegroundColor Yellow

& $PythonExe -c "import win32serviceutil" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pywin32..." -ForegroundColor Yellow
    & (Join-Path $VenvPath "Scripts\pip.exe") install --quiet pywin32
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install pywin32" -ForegroundColor Red
        exit 1
    }
}
Write-Host "pywin32 is installed" -ForegroundColor Green
Write-Host ""

# Step 3: Check if service already exists
Write-Host "[3/6] Checking existing service..." -ForegroundColor Yellow

$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($ExistingService) {
    Write-Host "Service already exists. Stopping and removing..." -ForegroundColor Yellow
    
    if ($ExistingService.Status -eq 'Running') {
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
    }
    
    & $PythonExe -m adcp_recorder.service.win_service remove
    Start-Sleep -Seconds 2
    Write-Host "Existing service removed" -ForegroundColor Green
}
Write-Host ""

# Step 4: Install service
Write-Host "[4/6] Installing Windows service..." -ForegroundColor Yellow

& $PythonExe -m adcp_recorder.service.win_service install
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Service installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "Service installed" -ForegroundColor Green
Write-Host ""

# Step 5: Configure service
Write-Host "[5/6] Configuring service..." -ForegroundColor Yellow

# Set service to start automatically
sc.exe config $ServiceName start= auto | Out-Null

# Set service description
sc.exe description $ServiceName $ServiceDescription | Out-Null

# Set recovery options (restart on failure)
sc.exe failure $ServiceName reset= 86400 actions= restart/60000/restart/60000/restart/60000 | Out-Null

Write-Host "Service configured for automatic startup" -ForegroundColor Green
Write-Host ""

# Step 6: Start service
Write-Host "[6/6] Starting service..." -ForegroundColor Yellow

$StartService = Read-Host "Start service now? (Y/N)"
if ($StartService -eq 'Y' -or $StartService -eq 'y') {
    Start-Service -Name $ServiceName
    Start-Sleep -Seconds 2
    
    $Service = Get-Service -Name $ServiceName
    if ($Service.Status -eq 'Running') {
        Write-Host "Service started successfully" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Service failed to start" -ForegroundColor Red
        Write-Host "Check Event Viewer for details" -ForegroundColor Yellow
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
Write-Host "  Status:      $((Get-Service -Name $ServiceName).Status)"
Write-Host "  Start Type:  Automatic"
Write-Host ""
Write-Host "Service Management Commands:" -ForegroundColor Cyan
Write-Host "  Start:       Start-Service -Name $ServiceName"
Write-Host "  Stop:        Stop-Service -Name $ServiceName"
Write-Host "  Restart:     Restart-Service -Name $ServiceName"
Write-Host "  Status:      Get-Service -Name $ServiceName"
Write-Host "  Logs:        Get-EventLog -LogName Application -Source $ServiceName -Newest 20"
Write-Host ""
Write-Host "Or use sc.exe commands:" -ForegroundColor Cyan
Write-Host "  Start:       sc start $ServiceName"
Write-Host "  Stop:        sc stop $ServiceName"
Write-Host "  Query:       sc query $ServiceName"
Write-Host ""
Write-Host "To view logs, open Event Viewer:" -ForegroundColor Cyan
Write-Host "  eventvwr.msc"
Write-Host "  Navigate to: Windows Logs -> Application"
Write-Host "  Filter by Source: $ServiceName"
Write-Host ""
