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
echo === Upgrading dependencies ===
python -m pip install --upgrade sphinx nbsphinx pydata-sphinx-theme sphinxcontrib-bibtex sphinxcontrib-jsmath
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to upgrade dependencies
    exit /b 1
)

echo.
echo === Building Sphinx documentation ===
call .\doc\make.bat clean
call .\doc\make.bat html

echo.
echo === Done: output in .\doc\_build\html ===
echo Docs are deployed automatically by .github\workflows\docs.yml on push to main.