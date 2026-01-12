@echo off
REM
REM uninstall-windows.bat - Uninstall ADCP Recorder from Windows
REM
REM This script removes the ADCP Recorder and optionally removes data.
REM Run as Administrator to remove Windows service.
REM

setlocal enabledelayedexpansion

echo ========================================
echo ADCP Recorder - Windows Uninstallation
echo ========================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Not running as Administrator
    echo Service removal will be skipped
    echo.
    set ADMIN=0
) else (
    echo Running as Administrator
    set ADMIN=1
    echo.
)

REM Configuration
set INSTALL_DIR=C:\Program Files\ADCP-Recorder
set DATA_DIR=C:\ADCP_Data
set CONFIG_DIR=%PROGRAMDATA%\ADCP-Recorder

REM Confirm uninstallation
echo This will remove the ADCP Recorder installation.
set /p CONFIRM="Are you sure you want to continue? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo Uninstallation cancelled
    pause
    exit /b 0
)
echo.

REM Step 1: Stop and remove service
echo [1/4] Removing Windows service...
if %ADMIN%==1 (
    sc query adcp-recorder >nul 2>&1
    if %errorLevel%==0 (
        echo Stopping service...
        sc stop adcp-recorder >nul 2>&1
        timeout /t 3 /nobreak >nul
        
        echo Removing service...
        sc delete adcp-recorder >nul 2>&1
        if %errorLevel%==0 (
            echo Service removed
        ) else (
            echo WARNING: Failed to remove service
        )
    ) else (
        echo Service not found
    )
) else (
    echo Skipping service removal (requires Administrator)
)
echo.

REM Step 2: Remove installation directory
echo [2/4] Removing installation...
if exist "%INSTALL_DIR%" (
    echo Removing: %INSTALL_DIR%
    rmdir /s /q "%INSTALL_DIR%"
    if %errorLevel%==0 (
        echo Installation directory removed
    ) else (
        echo WARNING: Failed to remove installation directory
        echo You may need to close any running programs and try again
    )
) else (
    echo Installation directory not found
)
echo.

REM Step 3: Ask about data removal
echo [3/4] Data removal...
if exist "%DATA_DIR%" (
    echo.
    echo WARNING: This will permanently delete all collected data!
    set /p REMOVE_DATA="Remove data directory %DATA_DIR%? (yes/no): "
    if /i "!REMOVE_DATA!"=="yes" (
        rmdir /s /q "%DATA_DIR%"
        echo Data directory removed
    ) else (
        echo Data directory preserved at: %DATA_DIR%
    )
) else (
    echo Data directory not found
)
echo.

REM Ask about configuration removal
if exist "%CONFIG_DIR%" (
    set /p REMOVE_CONFIG="Remove configuration directory? (yes/no): "
    if /i "!REMOVE_CONFIG!"=="yes" (
        rmdir /s /q "%CONFIG_DIR%"
        echo Configuration removed
    ) else (
        echo Configuration preserved at: %CONFIG_DIR%
    )
)
echo.

REM Step 4: Cleanup
echo [4/4] Cleanup complete
echo.

echo ========================================
echo Uninstallation Complete!
echo ========================================
echo.
echo ADCP Recorder has been uninstalled.
echo.

if exist "%DATA_DIR%" (
    echo Preserved directories:
    echo   %DATA_DIR%
    echo.
    echo To completely remove all files:
    echo   rmdir /s /q "%DATA_DIR%"
)

if exist "%CONFIG_DIR%" (
    echo   %CONFIG_DIR%
    echo.
    echo To remove configuration:
    echo   rmdir /s /q "%CONFIG_DIR%"
)

echo.
pause
