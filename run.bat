@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

SET "VENV_DIR=.venv"
SET "PYTHON=python"

echo ========================================
echo      🎯 Hunter App Launcher 🎯
echo ========================================

REM --- Step 1: Check Python installation
%PYTHON% --version > temp_py_ver.txt 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python is not installed or not added to PATH.
    del temp_py_ver.txt >nul 2>&1
    pause
    exit /b
)

FOR /F "tokens=2 delims= " %%A IN (temp_py_ver.txt) DO (
    SET "PY_VERSION=%%A"
)
del temp_py_ver.txt >nul 2>&1

FOR /F "tokens=1,2,3 delims=." %%A IN ("!PY_VERSION!") DO (
    SET "PY_MAJOR=%%A"
    SET "PY_MINOR=%%B"
)

IF NOT "!PY_MAJOR!"=="3" (
    echo [ERROR] Python 3 is required. Found: !PY_VERSION!
    pause
    exit /b
)

IF !PY_MINOR! LSS 8 (
    echo [ERROR] Python 3.8+ is required. Found: !PY_VERSION!
    pause
    exit /b
)

echo [OK] Python !PY_VERSION! detected.

REM --- Step 2: Create virtual environment if needed
IF NOT EXIST "%VENV_DIR%" (
    echo Creating virtual environment in %VENV_DIR%...
    %PYTHON% -m venv %VENV_DIR%
    IF ERRORLEVEL 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
) ELSE (
    echo [OK] Virtual environment already exists.
)

REM --- Step 3: Activate virtual environment
echo Activating virtual environment...
CALL "%VENV_DIR%\Scripts\activate.bat"
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b
)

REM --- Step 4: Install dependencies
IF EXIST requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install --upgrade pip >nul
    pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b
    )
) ELSE (
    echo [WARNING] requirements.txt not found. Skipping dependencies.
)

REM --- Step 5: Choose app version and launch
echo.
echo Choose app version to run:
echo [1] Local Mode (app.py) - Full features with database
echo [2] Unified Mode (app_unified.py) - Auto-detecting environment  
echo [3] Enhanced Mode (enhanced_app.py) - Advanced pipeline features
echo [4] Cloud Mode (app_cloud.py) - Lightweight demo version
echo.
SET /P choice="Enter your choice (1-4): "

IF "%choice%"=="1" (
    IF EXIST app.py (
        echo Launching Local Mode...
        streamlit run app.py
    ) ELSE (
        echo [ERROR] app.py not found.
        pause
        exit /b
    )
) ELSE IF "%choice%"=="2" (
    IF EXIST app_unified.py (
        echo Launching Unified Mode...
        streamlit run app_unified.py
    ) ELSE (
        echo [ERROR] app_unified.py not found.
        pause
        exit /b
    )
) ELSE IF "%choice%"=="3" (
    IF EXIST enhanced_app.py (
        echo Launching Enhanced Mode...
        streamlit run enhanced_app.py
    ) ELSE (
        echo [ERROR] enhanced_app.py not found.
        pause
        exit /b
    )
) ELSE IF "%choice%"=="4" (
    IF EXIST app_cloud.py (
        echo Launching Cloud Mode...
        streamlit run app_cloud.py
    ) ELSE (
        echo [ERROR] app_cloud.py not found.
        pause
        exit /b
    )
) ELSE (
    echo [ERROR] Invalid choice. Defaulting to Unified Mode...
    IF EXIST app_unified.py (
        streamlit run app_unified.py
    ) ELSE IF EXIST app.py (
        streamlit run app.py
    ) ELSE (
        echo [ERROR] No app files found.
        pause
        exit /b
    )
)

pause
