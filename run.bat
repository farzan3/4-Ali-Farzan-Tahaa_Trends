@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

SET "VENV_DIR=.venv"
SET "PYTHON=python"

echo ========================================
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

IF NOT "!PY_MINOR!"=="12" (
    echo [ERROR] Python 3.12.x is required. Found: !PY_VERSION!
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

REM --- Step 5: Launch Streamlit app
IF EXIST app.py (
    echo Launching Streamlit app...
    streamlit run app.py
) ELSE (
    echo [ERROR] app.py not found in current directory.
    pause
    exit /b
)

pause
