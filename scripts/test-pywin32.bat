@echo off
REM Test script to diagnose pywin32 installation issues

echo ========================================
echo PyWin32 Diagnostic Script
echo ========================================
echo.

set INSTALL_DIR=C:\Program Files\ADCP-Recorder

echo [1/5] Checking if virtual environment exists...
if not exist "%INSTALL_DIR%\venv" (
    echo ERROR: Virtual environment not found at %INSTALL_DIR%\venv
    pause
    exit /b 1
)
echo OK: Virtual environment found
echo.

echo [2/5] Testing Python import of win32serviceutil...
"%INSTALL_DIR%\venv\Scripts\python.exe" -c "import win32serviceutil; print('OK: win32serviceutil imported successfully')" 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Failed to import win32serviceutil
    echo.
    echo [DIAGNOSTIC] Checking pywin32 installation...
    "%INSTALL_DIR%\venv\Scripts\pip.exe" show pywin32
    echo.
    echo [FIX] Attempting to reinstall pywin32...
    "%INSTALL_DIR%\venv\Scripts\pip.exe" uninstall -y pywin32
    "%INSTALL_DIR%\venv\Scripts\pip.exe" install pywin32
    echo.
    echo [FIX] Running pywin32 post-install script...
    "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\venv\Scripts\pywin32_postinstall.py" -install
    echo.
    echo Please try importing again:
    "%INSTALL_DIR%\venv\Scripts\python.exe" -c "import win32serviceutil; print('OK: win32serviceutil imported successfully')"
) else (
    echo OK: win32serviceutil imported successfully
)
echo.

echo [3/5] Testing servicemanager module...
"%INSTALL_DIR%\venv\Scripts\python.exe" -c "import servicemanager; print('OK: servicemanager imported successfully')" 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Failed to import servicemanager
    echo This is the module causing your service error
) else (
    echo OK: servicemanager imported successfully
)
echo.

echo [4/5] Checking pywin32 DLL files...
if exist "%INSTALL_DIR%\venv\Lib\site-packages\pywin32_system32" (
    echo OK: pywin32_system32 directory exists
    dir "%INSTALL_DIR%\venv\Lib\site-packages\pywin32_system32\*.dll" /b
) else (
    echo ERROR: pywin32_system32 directory not found
)
echo.

echo [5/5] Checking if pywin32 post-install was run...
"%INSTALL_DIR%\venv\Scripts\python.exe" -c "import sys; import os; print('Python executable:', sys.executable); print('Python version:', sys.version)"
echo.

echo ========================================
echo Diagnostic Complete
echo ========================================
echo.
echo If servicemanager import failed, try running as Administrator:
echo   "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\venv\Scripts\pywin32_postinstall.py" -install
echo.
pause
