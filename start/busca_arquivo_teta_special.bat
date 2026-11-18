@echo off
rem Caminho do diretorio atual do .bat
set "PROJECT_DIR=%~dp0"

rem Caminho um nivel acima
set "PROJECT_DIR=%PROJECT_DIR%.."

rem Muda para esse diretorio
cd /d "%PROJECT_DIR%"

:: (opcional) ativar venv
call "%PROJECT_DIR%\venv\Scripts\activate.bat"

:: roda o script como modulo; o cwd entra no sys.path
python -m scripts.busca_arquivo_teta_special