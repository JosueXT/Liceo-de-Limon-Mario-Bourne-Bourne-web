@echo off
title Liceo de Limon Mario Bourne Bourne - Servidor Local
color 0b

echo ======================================================================
echo    LICEO DE LIMON MARIO BOURNE BOURNE - MINISTERIO DE EDUCACION PUBLICA
echo                    INICIADOR AUTOMATICO DEL SITIO WEB
echo ======================================================================
echo.

:: 1. Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se detecto Python instalado en esta computadora.
    echo.
    echo Por favor descarga e instala Python desde: https://www.python.org/downloads/
    echo IMPORTANTE: Durante la instalacion, marca la casilla que dice:
    echo "Add python.exe to PATH"
    echo.
    pause
    exit /b
)

echo [1/3] Python detectado correctamente.
echo [2/3] Verificando e instalando componentes necesarios...
python -m pip install -r requirements.txt --quiet

echo [3/3] Iniciando el servidor institucional...
echo.
echo ======================================================================
echo  El sitio esta funcionando. Puedes abrir tu navegador en:
echo  >>> http://localhost:5000 <<<
echo.
echo  Para iniciar sesion como administrador:
echo  Usuario:    Admin
echo  Contrasena: Admin
echo.
echo  (Para apagar el sitio, simplemente cierra esta ventana negra)
echo ======================================================================
echo.

:: Abrir automaticamente la pagina en el navegador predeterminado
start http://localhost:5000

:: Ejecutar la aplicacion
python app.py
pause
