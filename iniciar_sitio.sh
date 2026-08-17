#!/bin/bash
echo "======================================================================"
echo "   LICEO DE LIMON MARIO BOURNE BOURNE - MINISTERIO DE EDUCACION PUBLICA"
echo "                   INICIADOR AUTOMATICO DEL SITIO WEB"
echo "======================================================================"
echo ""

# 1. Verificar Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "[ERROR] No se detectó Python en tu sistema."
    echo "Descárgalo gratis desde: https://www.python.org/downloads/"
    exit 1
fi

echo "[1/3] Python detectado."
echo "[2/3] Instalando dependencias..."
$PYTHON_CMD -m pip install -r requirements.txt --quiet

echo "[3/3] Iniciando servidor..."
echo ""
echo "======================================================================"
echo "  El sitio está funcionando en: http://localhost:5000"
echo "  Usuario Administrador: Admin | Contraseña: Admin"
echo "  (Presiona Ctrl + C o cierra la ventana para detener)"
echo "======================================================================"
echo ""

# Intentar abrir el navegador automáticamente
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5000 &
elif command -v open &>/dev/null; then
    open http://localhost:5000 &
fi

$PYTHON_CMD app.py
