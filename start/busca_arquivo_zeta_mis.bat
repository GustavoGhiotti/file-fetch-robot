@echo off
rem Caminho do diretorio atual do .bat
set "PROJECT_DIR=%~dp0"

rem Caminho um nivel acima
set "PROJECT_DIR=%PROJECT_DIR%.."

rem Muda para esse diretorio
cd /d "%PROJECT_DIR%"

rem Ativa a venv
call "%PROJECT_DIR%\venv\Scripts\activate.bat"

rem Roda o script como modulo
python -m scripts.busca_arquivo_zeta_mis