@echo off
cd /d "%~dp0"
where python >nul 2>nul || (echo No se encontro Python. Instalalo desde python.org y marca "Add Python to PATH". & pause & exit /b)
echo Instalando Lark...
python -m pip install lark
echo.
echo Compilando los ejemplos...
python compilador.py examples
echo.
pause
