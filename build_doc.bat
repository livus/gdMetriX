@echo off
setlocal enabledelayedexpansion


echo.
echo === Upgrading dependencies ===
python -m pip install --upgrade sphinx pydata-sphinx-theme
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to upgrade dependencies
    exit /b 1
)

echo.
echo === Building Sphinx documentation ===
call .\doc\make.bat html
del /q .\docs\*
xcopy /s /y .\doc\_build\html\* .\docs\

if not exist .\docs\.nojekyll (
    echo. > .\docs\.nojekyll
)

git add ./docs/*