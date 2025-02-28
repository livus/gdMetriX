@echo off
setlocal enabledelayedexpansion

REM Define the package name
set PACKAGE_NAME=gdMetriX

echo.
echo === Upgrading dependencies ===
python -m pip install --upgrade pip build twine
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to upgrade dependencies
    exit /b 1
)

echo.
echo === System Info ===
python --version
pip --version
sphinx-build --version
echo.

echo.
echo === Removing old distribution files ===
if exist dist rmdir /s /q dist

echo.
echo === Building the package ===
python -m build
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo === Finding the latest wheel file ===
for /f %%i in ('dir /b /o-d dist\*.whl') do set LATEST_WHEEL=dist\%%i
if not defined LATEST_WHEEL (
    echo ERROR: No wheel file found in dist/
    exit /b 1
)

echo.
echo === Running Twine check ===
python -m twine check dist/*
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Twine validation failed!
    exit /b 1
)

echo.
echo === Installing the package from %LATEST_WHEEL% ===
python -m pip install --force-reinstall --no-deps %LATEST_WHEEL%
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Installation failed
    exit /b 1
)

echo.
echo === Extracting expected version from pyproject.toml ===
for /f "tokens=2 delims==" %%a in ('findstr /R "version *= *" pyproject.toml') do set EXPECTED_VERSION=%%a
set EXPECTED_VERSION=%EXPECTED_VERSION: =%
set EXPECTED_VERSION=%EXPECTED_VERSION:"=%
if not defined EXPECTED_VERSION (
    echo ERROR: Could not extract version from pyproject.toml
    exit /b 1
)

echo.
echo === Checking installed package version ===
for /f %%i in ('python -c "import %PACKAGE_NAME%; print(%PACKAGE_NAME%.__version__)" 2^>nul') do set INSTALLED_VERSION=%%i
if not defined INSTALLED_VERSION (
    echo ERROR: Could not import %PACKAGE_NAME% or __version__ not found
    exit /b 1
)

if "%INSTALLED_VERSION%" == "%EXPECTED_VERSION%" (
    echo SUCCESS: Version check PASSED! Installed version: %INSTALLED_VERSION%
) else (
    echo ERROR: Version mismatch! Expected: %EXPECTED_VERSION%, but got: %INSTALLED_VERSION%
    exit /b 1
)

echo.
echo === Running Twine check ===
python -m twine check dist/*
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Twine validation failed!
    exit /b 1
)

echo.
echo Package built, installed, and verified successfully!
exit /b 0