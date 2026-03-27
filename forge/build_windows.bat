@echo off
:: ═══════════════════════════════════════════════
::  FORGE — Script de Build para Windows (.exe)
:: ═══════════════════════════════════════════════
echo.
echo  ████████████████████████████████████
echo   FORGE — Gerando executável .exe...
echo  ████████████████████████████████████
echo.

:: 1. Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
echo [ERRO] Python nao encontrado. Instale em: https://python.org
pause & exit /b 1
)

:: 2. Instala dependências (FORÇANDO o Python correto)
echo [1/3] Instalando Flask e PyInstaller...
python -m pip install --upgrade pip --quiet
python -m pip install flask pyinstaller --quiet

:: 3. Gera o executável (SEM depender do PATH)
echo [2/3] Compilando o app...
python -m PyInstaller forge.spec --noconfirm --clean

:: 4. Resultado
if exist "dist\forge\forge.exe" (
echo.
echo  SUCESSO! Executavel gerado em:
echo     dist\forge\forge.exe
echo.
echo  Copie toda a pasta dist\forge para
echo  qualquer computador Windows e execute forge.exe
echo.
) else (
echo  ERRO durante o build. Verifique o log acima.
)

pause
