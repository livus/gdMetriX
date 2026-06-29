@echo off
setlocal enabledelayedexpansion

echo.
echo === Activating virtual environment ===
call "%~dp0venv\Scripts\activate.bat"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment at %~dp0venv
    exit /b 1
)

echo.
echo === Rebuilding package and documentation ===
call ./build_doc.bat
call ./build.bat

echo.
echo === Upload package ===
python -m twine upload ./dist/*