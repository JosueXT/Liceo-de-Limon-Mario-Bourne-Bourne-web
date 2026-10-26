"""
==============================================================================
CONFIGURACIÓN DE GUNICORN (PRODUCCIÓN EN RENDER)
Liceo de Limón Mario Bourne Bourne (MEP)
==============================================================================
"""
import os

# Puerto asignado dinámicamente por Render (habitualmente 10000)
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Tiempo de espera extendido a 120 segundos (evita WORKER TIMEOUT de 30s por latencia de Turso)
timeout = 120
graceful_timeout = 30
keepalive = 5

# Modelo de workers híbrido con hilos (óptimo para 512 MB de memoria en Render)
workers = 2
threads = 4
worker_class = "gthread"

# Registro de accesos y errores a stdout/stderr para verlos en el dashboard de Render
accesslog = "-"
errorlog = "-"
loglevel = "info"
