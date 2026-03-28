@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   FORGE — Personal Trainer IA                ║
echo  ║   Gerando executavel .exe para Windows        ║
echo  ╚══════════════════════════════════════════════╝
echo.

echo [0/4] Validando arquivos do projeto...
if not exist "forge_server.py" ( echo [ERRO] forge_server.py nao encontrado. pause & exit /b 1 )
if not exist "forge.spec"      ( echo [ERRO] forge.spec nao encontrado.      pause & exit /b 1 )
if not exist "static\index.html" ( echo [ERRO] static\index.html nao encontrado. pause & exit /b 1 )
echo  OK - Arquivos validados.
echo.

echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale em: https://python.org
    echo        Marque "Add Python to PATH" durante a instalacao.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  OK - %PYVER%
echo.

echo [2/4] Instalando dependencias...
python -m pip install --upgrade pip --quiet --no-warn-script-location
python -m pip install flask PyJWT pyinstaller --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERRO] Falha ao instalar dependencias. pause & exit /b 1 )
echo  OK - Flask + PyJWT + PyInstaller instalados.
echo.

echo [3/4] Compilando executavel (aguarde 1 a 3 minutos)...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist"  rmdir /s /q "dist"  >nul 2>&1
python -m PyInstaller forge.spec --noconfirm --clean
if errorlevel 1 ( echo [ERRO] Falha no build. Veja o log acima. pause & exit /b 1 )
echo.

echo [4/4] Validando resultado...
if exist "dist\forge\forge.exe" (
    for %%F in ("dist\forge\forge.exe") do set SIZE=%%~zF
    set /a SIZEMB=!SIZE! / 1048576
    echo.
    echo  ====================================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo  ====================================================
    echo   Arquivo: dist\forge\forge.exe
    echo   Tamanho: ~!SIZEMB! MB
    echo.
    echo   Como distribuir:
    echo   1. Copie TODA a pasta dist\forge\
    echo   2. Cole em qualquer PC Windows
    echo   3. Execute forge.exe
    echo   4. Browser abre automaticamente em localhost:5050
    echo.
    echo   Login Admin: usuario=admin  senha=forge123
    echo  ====================================================
    echo.
    set /p TESTAR="Testar agora? (S/N): "
    if /i "!TESTAR!"=="S" start "" "dist\forge\forge.exe"
) else (
    echo [ERRO] Executavel nao gerado. Verifique os erros acima.
)
pause
