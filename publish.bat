@echo off
setlocal enabledelayedexpansion

echo.
echo === Rebuilding package and documentation ===
call ./build_doc.bat
call ./build.bat

echo.
echo === Upload package ===
python -m twine upload ./dist/*